"""Tool-call policy for the Sentinel firewall.

A protected agent is only allowed to call tools on a small allowlist, and even
those tools have argument constraints (e.g. ``search`` can look things up, but
``run_shell`` with ``rm -rf`` is always blocked). This is the "dangerous tool
call" layer of Defend mode — easy to explain in a viva:

  1. Is the tool name on the allowlist?
  2. Do the arguments match a known-dangerous pattern?
  3. Does the payload look like data exfiltration (secrets / PII leaving)?
"""
from __future__ import annotations

import re
from typing import Any

from .models import ToolCall


# Tools the demo protected-agent is allowed to call. Anything else is blocked.
ALLOWED_TOOLS: set[str] = {
    "search",          # fake document search (returns retrieved text)
    "get_weather",     # harmless demo tool
    "calculator",      # arithmetic
}

# Tools that exist on the mock agent but are *never* allowed through the
# firewall in production-shaped demos. The red-team and the mock agent will
# still *propose* them so we can show the firewall catching them.
DENIED_TOOLS: set[str] = {
    "run_shell",
    "send_email",
    "http_request",
    "write_file",
    "read_secrets",
}


# Patterns that make even an allowlisted tool dangerous (arg-level).
_DANGEROUS_ARG_PATTERNS: list[tuple[str, str]] = [
    (r"\brm\s+-rf\b", "shell destructive delete (rm -rf)"),
    (r"\b(curl|wget)\b.+\|\s*(ba)?sh\b", "download-and-execute pipe"),
    (r"\bcat\s+/etc/passwd\b", "passwd file read"),
    (r"\b(nc|ncat|netcat)\b.+\-e\b", "reverse shell via netcat"),
    (r"\bpowershell\b.+\-enc\b", "encoded PowerShell"),
    (r"\.\./\.\./", "filesystem path traversal"),
    (r"/etc/shadow|/root/\.ssh", "sensitive system path"),
]

# Domains we treat as "attacker-controlled" for the demo. Outbound traffic to
# these is always blocked (data-exfil / C2).
_ATTACKER_DOMAINS = (
    "evil.example",
    "attacker.local",
    "exfil.bad",
    "pastebin.com",       # classic exfil sink in demos
    "webhook.site",
)


# Secrets / PII that must never leave via tool arguments.
_SECRET_PATTERNS: list[tuple[str, str]] = [
    (r"(?i)\b(api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*\S+",
     "credential / secret in tool args"),
    (r"(?i)\bAKIA[0-9A-Z]{16}\b", "AWS access key id"),
    (r"(?i)\bsk-[A-Za-z0-9]{20,}\b", "OpenAI-style secret key"),
    (r"\b(?:\d[ -]*?){13,16}\b", "possible credit-card number"),
    (r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b.+\b(password|otp|ssn)\b",
     "email paired with sensitive field"),
    (r"(?i)system prompt|you are a helpful|hidden instructions",
     "system-prompt exfiltration"),
]


def evaluate_tool_call(call: ToolCall) -> dict:
    """Return a structured policy decision for one tool call.

    Keys: verdict ('allow'|'block'), reasons (list[str]), categories (list),
    risk_score (float).
    """
    reasons: list[str] = []
    categories: list[str] = []
    risk = 0.0

    name = (call.name or "").strip()
    args_flat = _flatten_args(call.arguments)

    if name in DENIED_TOOLS:
        reasons.append(f"tool '{name}' is on the deny list")
        categories.append("dangerous_tool")
        risk = max(risk, 0.95)
    elif name not in ALLOWED_TOOLS:
        reasons.append(f"tool '{name}' is not on the allowlist")
        categories.append("dangerous_tool")
        risk = max(risk, 0.85)

    for pattern, label in _DANGEROUS_ARG_PATTERNS:
        if re.search(pattern, args_flat, flags=re.IGNORECASE):
            reasons.append(f"dangerous argument pattern: {label}")
            categories.append("dangerous_tool")
            risk = max(risk, 0.95)

    for domain in _ATTACKER_DOMAINS:
        if domain in args_flat.lower():
            reasons.append(f"outbound to attacker-controlled domain '{domain}'")
            categories.append("data_exfiltration")
            risk = max(risk, 0.9)

    for pattern, label in _SECRET_PATTERNS:
        if re.search(pattern, args_flat):
            reasons.append(f"possible exfiltration: {label}")
            categories.append("data_exfiltration")
            risk = max(risk, 0.9)

    # send_email / http_request specifically: body that looks like system prompt
    if name in ("send_email", "http_request", "run_shell") and risk < 0.95:
        # Already denied above; keep risk high.
        risk = max(risk, 0.9)

    if risk >= 0.7:
        verdict = "block"
    elif risk >= 0.4:
        verdict = "sanitize"
    else:
        verdict = "allow"

    return {
        "verdict": verdict,
        "reasons": reasons,
        "categories": sorted(set(categories)),
        "risk_score": round(risk, 3),
    }


def _flatten_args(args: Any) -> str:
    """Flatten tool arguments into a single searchable string."""
    import json
    try:
        return json.dumps(args, sort_keys=True, default=str)
    except Exception:
        return str(args)
