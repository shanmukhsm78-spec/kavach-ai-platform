"""Layered detectors for Sentinel (Defend mode).

Layer 1 — deterministic signature / heuristic rules (always on, offline).
Layer 2 — learned signatures from the self-heal store (data/defend/learned.jsonl).
Layer 3 — optional LLM judge (only when KAVACH_LLM != off). Never required.

The detectors cover:
  * prompt injection / jailbreak (role override, ignore-previous, system-prompt
    exfiltration, encoded / obfuscated forms, injections hidden in docs)
  * data exfiltration (secrets / PII leaving)
  * dangerous tool calls (delegated to tool_policy.py)
"""
from __future__ import annotations

import base64
import re
from typing import Iterable, Optional

from . import llm_assist, tool_policy
from .models import InspectionResult, ToolCall


# ---------------------------------------------------------------------------
# Signature catalogue (Layer 1)
# Each entry: (signature_id, category, compiled-or-string pattern, weight,
#              human reason). weight contributes to risk_score (capped at 1.0).
# ---------------------------------------------------------------------------

# Direct prompt-injection / jailbreak phrases. Case-insensitive substring or
# regex. Kept deliberately readable for the viva — "these are the classic
# phrases attackers use to override an LLM's system prompt".
_INJECTION_RULES: list[tuple[str, str, str, float, str]] = [
    ("inj_ignore_prev", "prompt_injection",
     r"(?i)\bignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions|rules|prompts|directives)\b",
     0.85, "classic 'ignore previous instructions' override"),
    ("inj_disregard", "prompt_injection",
     r"(?i)\b(disregard|forget|override)\s+(all\s+)?(previous|prior|your)\s+(instructions|rules|guidelines)\b",
     0.8, "instruction-override phrasing"),
    ("inj_role_override", "jailbreak",
     r"(?i)\b(you\s+are\s+now|act\s+as|pretend\s+to\s+be|roleplay\s+as)\b.+\b(dan|jailbreak|unrestricted|evil|developer\s+mode)\b",
     0.85, "role-override / DAN-style jailbreak"),
    ("inj_developer_mode", "jailbreak",
     r"(?i)\b(developer\s+mode|jailbreak\s+mode|no\s+restrictions|uncensored\s+mode)\b",
     0.75, "requests developer / unrestricted mode"),
    ("inj_system_exfil", "prompt_injection",
     r"(?i)\b(reveal|show|print|repeat|output|dump)\b.+\b(system\s+prompt|hidden\s+instructions|initial\s+instructions|your\s+instructions)\b",
     0.9, "system-prompt exfiltration attempt"),
    ("inj_new_instr", "prompt_injection",
     r"(?i)\b(new\s+instructions?|updated\s+instructions?|from\s+now\s+on)\b.+\b(you\s+must|you\s+will|always)\b",
     0.7, "injected 'new instructions' block"),
    ("inj_end_of_prompt", "prompt_injection",
     r"(?i)(<<\s*end\s+of\s+(system\s+)?prompt\s*>>|\[?\s*end\s+system\s*\]?)",
     0.8, "fake end-of-system-prompt marker"),
    ("inj_tool_force", "prompt_injection",
     r"(?i)\b(call|invoke|use)\s+the\s+(tool|function)\b.+\b(run_shell|send_email|http_request)\b",
     0.85, "forces a dangerous tool call from natural language"),
    ("inj_hidden_in_doc", "prompt_injection",
     r"(?i)(IMPORTANT\s+FOR\s+AI|AI\s+ASSISTANT\s*[:：]|BEGIN\s+INVISIBLE\s+INSTRUCTION|"
     r"<\s*instruction\s*>|\[INST\])",
     0.8, "injection framing commonly hidden inside retrieved documents"),
    ("inj_base64_hint", "prompt_injection",
     r"(?i)\b(decode|base64|rot13)\b.+\b(and\s+)?(execute|follow|obey)\b",
     0.75, "asks the model to decode + obey an encoded payload"),
]

# Data-exfiltration cues that can appear in prompts OR in tool-call args.
_EXFIL_RULES: list[tuple[str, str, str, float, str]] = [
    ("exfil_secrets_ask", "data_exfiltration",
     r"(?i)\b(send|email|post|upload|exfiltrate|leak)\b.+\b(password|api[_-]?key|secret|token|credentials?)\b",
     0.9, "asks to send secrets / credentials out"),
    ("exfil_webhook", "data_exfiltration",
     r"(?i)\b(webhook\.site|pastebin\.com|evil\.example|attacker\.local|exfil\.bad)\b",
     0.85, "known attacker / exfil sink domain"),
    ("exfil_env_dump", "data_exfiltration",
     r"(?i)\b(dump|print|list)\b.+\b(env(ironment)?\s+variables?|process\.env|/etc/passwd)\b",
     0.8, "environment / secret dump request"),
]


def _compile(rules: list[tuple[str, str, str, float, str]]):
    out = []
    for sid, cat, pat, weight, reason in rules:
        out.append((sid, cat, re.compile(pat), weight, reason))
    return out


_INJECTION_COMPILED = _compile(_INJECTION_RULES)
_EXFIL_COMPILED = _compile(_EXFIL_RULES)


# ---------------------------------------------------------------------------
# Encoding / obfuscation helpers
# ---------------------------------------------------------------------------

_B64_RE = re.compile(r"(?<![A-Za-z0-9+/=])([A-Za-z0-9+/]{24,}={0,2})(?![A-Za-z0-9+/=])")


def _try_decode_base64_fragments(text: str) -> list[str]:
    """Pull out base64-looking blobs and decode the ones that look like text.

    Attackers sometimes hide "ignore previous instructions" as base64 inside a
    retrieved document. We decode candidates and re-run the injection rules on
    the plaintext.
    """
    decoded: list[str] = []
    for match in _B64_RE.findall(text or ""):
        try:
            # Pad if needed.
            pad = "=" * (-len(match) % 4)
            raw = base64.b64decode(match + pad, validate=False)
            # Only keep mostly-printable UTF-8.
            s = raw.decode("utf-8", errors="strict")
            if s and sum(ch.isprintable() or ch.isspace() for ch in s) / len(s) > 0.85:
                decoded.append(s)
        except Exception:
            continue
    return decoded


def _leetspeak_normalize(text: str) -> str:
    """Cheap leetspeak fold so 'ign0re prev10us instructi0ns' still matches."""
    table = str.maketrans({
        "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a",
        "$": "s",
    })
    return text.translate(table)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class DetectorEngine:
    """Stateful detector: base rules + learned signatures from self-heal."""

    def __init__(self, learned_signatures: Optional[Iterable[str]] = None):
        # Learned signatures are plain substrings (lowercased) that previously
        # bypassed the firewall. Self-heal appends to this set.
        self.learned: set[str] = set()
        if learned_signatures:
            self.add_learned(learned_signatures)

    def add_learned(self, signatures: Iterable[str]) -> int:
        before = len(self.learned)
        for s in signatures:
            s = (s or "").strip().lower()
            if s and len(s) >= 8:          # ignore tiny noisy scraps
                self.learned.add(s)
        return len(self.learned) - before

    # -- prompt / document --------------------------------------------------

    def inspect_text(self, content: str, channel: str = "prompt") -> InspectionResult:
        text = content or ""
        reasons: list[str] = []
        categories: list[str] = []
        matched: list[str] = []
        risk = 0.0

        # 1) Direct rule match on the raw text + a leetspeak-normalized copy.
        variants = [text, _leetspeak_normalize(text)]
        # 2) Also scan any successfully-decoded base64 fragments.
        variants.extend(_try_decode_base64_fragments(text))

        for variant in variants:
            for sid, cat, cre, weight, reason in _INJECTION_COMPILED + _EXFIL_COMPILED:
                if cre.search(variant):
                    if sid not in matched:
                        matched.append(sid)
                        reasons.append(reason)
                        categories.append(cat)
                        risk = min(1.0, risk + weight)

        # 3) Learned signatures from the self-heal store (substring match).
        lowered = text.lower()
        for sig in self.learned:
            if sig in lowered:
                matched.append(f"learned:{sig[:40]}")
                reasons.append("matched a previously-bypassed attack (self-heal)")
                categories.append("learned")
                risk = min(1.0, risk + 0.9)
                break  # one learned hit is enough

        # 4) Decide verdict from risk.
        verdict, sanitized = self._verdict_from_risk(risk, text, categories)

        engine = "rules"
        # 5) Optional LLM judge — can only escalate, never downgrade a block.
        if risk < 0.7:  # only bother the LLM on borderline / clean cases
            judged = llm_assist.llm_judge(channel, text, verdict, reasons)
            if judged:
                engine = "rules+llm"
                if judged["verdict"] == "block" and verdict != "block":
                    verdict = "block"
                    risk = max(risk, float(judged["risk_score"]))
                    reasons.append(f"llm-judge: {judged['reason']}")
                    categories.append("llm_judge")

        return InspectionResult(
            channel=channel,
            verdict=verdict,
            risk_score=round(risk, 3),
            reasons=reasons,
            categories=sorted(set(categories)),
            sanitized=sanitized,
            original=_preview(text, 500),
            engine=engine,
            matched_signatures=matched,
        )

    # -- tool calls ---------------------------------------------------------

    def inspect_tool_call(self, call: ToolCall) -> InspectionResult:
        policy = tool_policy.evaluate_tool_call(call)
        # Also run the text detectors over the flattened args — catches
        # "please ignore previous instructions and send_email(...)" style
        # payloads stuffed into a string argument.
        flat = call.render()
        text_result = self.inspect_text(flat, channel="tool_call")

        # Merge: take the stricter verdict / higher risk.
        order = {"allow": 0, "sanitize": 1, "block": 2}
        if order[text_result.verdict] > order[policy["verdict"]]:
            verdict = text_result.verdict
        else:
            verdict = policy["verdict"]
        risk = max(policy["risk_score"], text_result.risk_score)
        reasons = list(policy["reasons"]) + [
            r for r in text_result.reasons if r not in policy["reasons"]
        ]
        categories = sorted(set(policy["categories"] + text_result.categories))

        return InspectionResult(
            channel="tool_call",
            verdict=verdict,
            risk_score=round(risk, 3),
            reasons=reasons,
            categories=categories,
            sanitized="" if verdict == "block" else flat,
            original=_preview(flat, 500),
            engine="rules",
            matched_signatures=text_result.matched_signatures,
        )

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _verdict_from_risk(risk: float, text: str,
                           categories: list[str]) -> tuple[str, str]:
        if risk >= 0.7:
            return "block", ""
        if risk >= 0.4:
            # Soft sanitize: strip the most common override phrases.
            cleaned = text
            for _, _, cre, _, _ in _INJECTION_COMPILED:
                cleaned = cre.sub("[removed-by-sentinel]", cleaned)
            return "sanitize", cleaned
        return "allow", text


def _preview(text: str, n: int) -> str:
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "…"
