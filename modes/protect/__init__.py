"""Protect mode - Kavach scam shield (phishing URL, scam SMS, voice-clone)."""
from .detectors import DETECTORS, LANGUAGES, check

__all__ = ["check", "DETECTORS", "LANGUAGES"]
