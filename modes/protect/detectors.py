"""Protect mode (Kavach shield) facade: one entry point for all detectors.

    check("url", "http://sbi-kyc.xyz")   -> phishing URL detector
    check("sms", "Your KYC expired...")  -> scam message detector
    check("audio", "/path/clip.wav")     -> voice-clone heuristic

Every result: risk_score 0-100, verdict safe|suspicious|dangerous, reasons,
explanation {"en","hi"}. Optional LLM rewrite goes in explanation["llm"].
"""
from __future__ import annotations

from .llm_assist import llm_explain
from .sms_detector import score_sms
from .url_detector import score_url
from .voice_detector import score_audio

DETECTORS = ["phishing_url", "scam_sms", "voice_clone"]
LANGUAGES = ["en", "hi"]
_DISPATCH = {"url": score_url, "sms": score_sms, "audio": score_audio, "voice": score_audio}


def check(kind: str, value: str, language: str = "en") -> dict:
    if kind not in _DISPATCH:
        raise ValueError(f"unknown kind {kind!r}; use url|sms|audio")
    result = _DISPATCH[kind](value)
    extra = llm_explain(result)
    if extra:
        result["explanation"]["llm"] = extra
    result["language"] = language if language in LANGUAGES else "en"
    return result
