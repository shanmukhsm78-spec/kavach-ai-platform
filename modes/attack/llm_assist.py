"""Optional LLM assistance for Attack mode (graceful, never required).

The pipeline runs fully offline with deterministic, rule-based text. If an
LLM *is* configured and reachable, we use it only to polish prose: an
executive summary and friendlier remediation advice. Any failure (no server,
bad key, timeout) silently falls back to the deterministic text so grading /
viva demos never break.

Enable/disable explicitly with the KAVACH_LLM env var:
    KAVACH_LLM=off   -> never call the LLM (default-safe for offline grading)
    KAVACH_LLM=auto  -> try the LLM, fall back on any error (default)
"""
from __future__ import annotations

import os
from typing import Optional


def llm_enabled() -> bool:
    """Whether we should even attempt an LLM call."""
    return os.getenv("KAVACH_LLM", "auto").lower() not in ("off", "0", "false", "no")


def _try_chat(system: str, user: str) -> Optional[str]:
    """Best-effort single LLM turn. Returns None on *any* problem."""
    if not llm_enabled():
        return None
    try:
        # Imported lazily so the module works even if the SDK/env is absent.
        from agents.core import get_llm

        client = get_llm()
        # Short timeout so an unreachable local model can't hang a scan.
        text = client.chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            timeout=20,
        )
        text = (text or "").strip()
        return text or None
    except Exception:
        # Deterministic path takes over. We never surface LLM errors to grading.
        return None


def summarize_findings(target: str, findings: list[dict]) -> tuple[str, bool]:
    """Return (summary_text, used_llm).

    Deterministic summary is always computed first; the LLM, if available, is
    asked to rewrite it more readably. If the LLM is off/unreachable we return
    the deterministic version and ``used_llm=False``.
    """
    counts: dict[str, int] = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    breakdown = ", ".join(f"{n} {sev}" for sev, n in counts.items()) or "no issues"

    deterministic = (
        f"The automated assessment of {target} identified {len(findings)} "
        f"finding(s): {breakdown}. The highest-impact issues should be "
        "remediated first. All testing was performed non-destructively against "
        "an authorised local lab."
    )

    polished = _try_chat(
        system=(
            "You are a senior penetration tester writing the executive summary "
            "of a report. Be concise (3-4 sentences), factual, no markdown."
        ),
        user=(
            f"Target: {target}\nFindings (JSON-ish): {findings}\n"
            f"Draft summary: {deterministic}\nRewrite it clearly."
        ),
    )
    if polished:
        return polished, True
    return deterministic, False
