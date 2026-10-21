"""Optional LLM explanation layer for Protect mode (never required).

Same contract as Attack/Defend: KAVACH_LLM=off -> never call; auto -> try and
silently fall back. The LLM only *rewrites the explanation* in friendlier
words; it never changes the deterministic score or verdict.
"""
from __future__ import annotations

import os
from typing import Optional


def llm_enabled() -> bool:
    return os.getenv("KAVACH_LLM", "auto").lower() not in ("off", "0", "false", "no")


def llm_explain(result: dict) -> Optional[str]:
    if not llm_enabled():
        return None
    try:
        from agents.core import get_llm
        reasons = "; ".join(r["en"] for r in result["reasons"])
        text = get_llm().chat([
            {"role": "system", "content": "You warn ordinary Indian users about scams. "
             "In 2 short sentences, explain the risk simply. Do not change the verdict."},
            {"role": "user", "content": f"Type: {result['kind']}\nVerdict: {result['verdict']}\n"
             f"Score: {result['risk_score']}\nReasons: {reasons}\nInput: {result['input'][:400]}"},
        ], timeout=20)
        return (text or "").strip() or None
    except Exception:
        return None
