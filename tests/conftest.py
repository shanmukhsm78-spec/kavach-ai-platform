"""Pytest setup: make the repo root importable and force offline LLM mode.

This lets tests import ``modes``, ``agents`` and ``backend.app`` the same way
the running services do, and guarantees the deterministic (no-LLM) path so the
suite is fully offline and reproducible for grading.
"""
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for p in (_ROOT, _ROOT / "backend"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Never call an external/local LLM during tests -> deterministic output.
os.environ["KAVACH_LLM"] = "off"
