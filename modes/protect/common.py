"""Shared result shape + scoring helpers for all Protect detectors."""
from __future__ import annotations

from .i18n import build_explanation, reason_text

SUSPICIOUS_AT = 35   # score >= this -> suspicious
DANGEROUS_AT = 65    # score >= this -> dangerous


def verdict_for(score: int) -> str:
    if score >= DANGEROUS_AT:
        return "dangerous"
    if score >= SUSPICIOUS_AT:
        return "suspicious"
    return "safe"


def make_result(kind: str, value: str, score: float, codes: list[str],
                features: dict | None = None, engine: str = "rules") -> dict:
    """Build the uniform response every detector returns."""
    score = int(max(0, min(100, round(score))))
    verdict = verdict_for(score)
    return {
        "kind": kind,
        "input": value[:500],
        "risk_score": score,
        "verdict": verdict,
        "reasons": [{"code": c, "en": reason_text(c, "en"), "hi": reason_text(c, "hi")} for c in codes],
        "explanation": build_explanation(verdict, codes),
        "features": features or {},
        "engine": engine,
    }
