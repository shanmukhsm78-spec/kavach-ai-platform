"""Tiny train/eval for Protect mode on the shipped sample sets.

Run:  .venv/bin/python -m modes.protect.evaluate
  * URL   - deterministic scorer, positive = verdict != safe
  * SMS   - rules + Naive Bayes, evaluated with LEAVE-ONE-OUT so the NB model
            never sees the message it is scoring (honest number)
  * Voice - signal heuristic on datasets/voice/{real,fake}
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .sms_detector import NaiveBayes, load_samples, score_sms
from .url_detector import score_url
from .voice_detector import score_audio

ROOT = Path(__file__).resolve().parents[2] / "datasets"


def _metrics(pairs: list[tuple[int, int]]) -> dict:
    tp = sum(1 for y, p in pairs if y and p); tn = sum(1 for y, p in pairs if not y and not p)
    fp = sum(1 for y, p in pairs if not y and p); fn = sum(1 for y, p in pairs if y and not p)
    n = len(pairs) or 1
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return {"n": len(pairs), "accuracy": round((tp + tn) / n, 3), "precision": round(prec, 3),
            "recall": round(rec, 3), "tp": tp, "tn": tn, "fp": fp, "fn": fn}


def eval_url() -> dict:
    with open(ROOT / "phishing" / "urls_sample.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return _metrics([(int(r["label"] == "phishing"), int(score_url(r["url"])["verdict"] != "safe")) for r in rows])


def eval_sms() -> dict:
    rows = load_samples()
    pairs = []
    for i, (text, y) in enumerate(rows):
        model = NaiveBayes().fit(rows[:i] + rows[i + 1:])     # leave-one-out
        pairs.append((y, int(score_sms(text, model=model)["verdict"] != "safe")))
    rules_only = [(y, int(score_sms(t, use_ml=False)["verdict"] != "safe")) for t, y in rows]
    return {"rules+nb_loo": _metrics(pairs), "rules_only": _metrics(rules_only)}


def eval_voice() -> dict:
    pairs = []
    for label, y in (("real", 0), ("fake", 1)):
        for wav in sorted((ROOT / "voice" / label).glob("*.wav")):
            pairs.append((y, int(score_audio(wav)["verdict"] != "safe")))
    return _metrics(pairs)


def evaluate_all() -> dict:
    return {"url": eval_url(), "sms": eval_sms(), "voice": eval_voice()}


if __name__ == "__main__":
    print(json.dumps(evaluate_all(), indent=2))
