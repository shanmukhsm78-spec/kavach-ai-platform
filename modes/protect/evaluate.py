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




# ---------------------------------------------------------------------------
# Real benchmark (held-out test split from public datasets).
# Build the CSVs first with:  make protect-download
# ---------------------------------------------------------------------------
BENCH_SEED = 42


def _load_bench(rel: str) -> list[dict] | None:
    p = ROOT / rel
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f1(m: dict) -> dict:
    p, r = m["precision"], m["recall"]
    m["f1"] = round(2 * p * r / (p + r), 3) if p + r else 0.0
    return m


def bench_url(split: str = "test") -> dict | None:
    rows = _load_bench("phishing/benchmark.csv")
    if rows is None:
        return None
    rows = [r for r in rows if r["split"] == split]
    return _f1(_metrics([(int(r["label"] == "phishing"), int(score_url(r["url"])["verdict"] != "safe")) for r in rows]))


def bench_openphish() -> dict | None:
    """Recall on the live OpenPhish feed (all phishing; out-of-distribution)."""
    p = ROOT / "phishing" / "raw" / "openphish_feed.txt"
    if not p.exists():
        return None
    urls = [u.strip() for u in p.read_text(encoding="utf-8").splitlines() if u.strip()]
    hits = sum(1 for u in urls if score_url(u)["verdict"] != "safe")
    return {"n": len(urls), "recall": round(hits / (len(urls) or 1), 3), "detected": hits}


def bench_sms(split: str = "test") -> dict | None:
    rows = _load_bench("sms/benchmark.csv")
    if rows is None:
        return None
    train = [(r["text"], int(r["label"] == "scam")) for r in rows if r["split"] == "train"]
    test = [(r["text"], int(r["label"] == "scam")) for r in rows if r["split"] == split]
    model = NaiveBayes().fit(train)                     # fit on TRAIN only
    return {
        "n_train": len(train),
        "rules_only": _f1(_metrics([(y, int(score_sms(t, use_ml=False)["verdict"] != "safe")) for t, y in test])),
        "rules+nb": _f1(_metrics([(y, int(score_sms(t, model=model)["verdict"] != "safe")) for t, y in test])),
        "nb_only": _f1(_metrics([(y, int(model.predict_proba(t) >= 0.5)) for t, y in test])),
    }


def _row(name: str, m: dict) -> str:
    return (f"| {name} | {m['n']} | {m['accuracy']:.3f} | {m['precision']:.3f} | {m['recall']:.3f} "
            f"| {m['f1']:.3f} | TP {m['tp']} / FP {m['fp']} / FN {m['fn']} / TN {m['tn']} |")


def write_report(path: Path | None = None) -> Path:
    path = path or Path(__file__).resolve().parents[2] / "docs" / "protect_benchmark.md"
    url, sms, oph = bench_url(), bench_sms(), bench_openphish()
    url_tr, sms_tr = bench_url("train"), bench_sms("train")
    hdr = "| Detector | n (test) | Accuracy | Precision | Recall | F1 | Confusion matrix |\n|---|---|---|---|---|---|---|"
    L = ["# Protect mode — real benchmark (held-out test sets)", "",
         "_Generated by `make protect-bench` (`python -m modes.protect.evaluate --bench`). Do not edit numbers by hand._", "",
         "## Methodology", "",
         "- **URL data:** PhiUSIIL Phishing URL Dataset (Prasad & Chandra, 2023), UCI ML Repository id 967, CC BY 4.0 — "
         "https://archive.ics.uci.edu/dataset/967 . Random sample of 2,500 phishing + 2,500 legitimate unique URLs (seed 42).",
         "- **SMS data:** SMS Spam Collection v.1 (Almeida & Hidalgo, 2011), UCI id 228, CC BY 4.0 — "
         "https://archive.ics.uci.edu/dataset/228 . All 5,574 messages (747 spam / 4,827 ham); spam is treated as 'scam'.",
         "- **Extra URL check:** OpenPhish community feed (https://openphish.com/feed.txt), downloaded 2026-10-21, "
         "all live phishing → recall only. Kept locally in `raw/`, not redistributed.",
         f"- **Split:** stratified 80/20 train/test, fixed seed {BENCH_SEED} (column `split` in each benchmark.csv).",
         "- **Positive prediction:** verdict is `suspicious` or `dangerous` (score ≥ 35).",
         "- **URL detector** is rule-based (no training). Any rule tuning was done by looking at TRAIN-split errors only.",
         "- **SMS Naive Bayes** is fitted on the TRAIN split only and scored on TEST. Rules were never tuned on TEST.", "",
         "## URL — phishing detector", "", hdr]
    if url:
        L += [_row("Rules (held-out test)", url), _row("Rules (train split, for reference)", url_tr)]
    else:
        L += ["| not run — run `make protect-download` | | | | | | |"]
    if oph:
        L += ["", f"OpenPhish live feed: **recall {oph['recall']:.3f}** ({oph['detected']}/{oph['n']} flagged)."]
    L += ["", "## SMS — scam detector", "", hdr]
    if sms:
        L += [_row("Rules only", sms["rules_only"]), _row("Rules + Naive Bayes", sms["rules+nb"]),
              _row("Naive Bayes only (p ≥ 0.5)", sms["nb_only"]), "",
              f"NB trained on {sms['n_train']} TRAIN messages. Train-split Rules+NB F1 for reference: {sms_tr['rules+nb']['f1']:.3f}."]
    else:
        L += ["| not run — run `make protect-download` | | | | | | |"]
    L += ["", "## Detector changes made for this benchmark", "",
          "- **URL:** added one feature, `free_hosting` (+35): page hosted on free hosting / site-builder / IPFS gateways "
          "(web.app, firebaseapp.com, repl.co, glitch.me, netlify.app, wixsite, IPFS…). Found by reading TRAIN-split false negatives only. "
          "Held-out test recall before the change: 0.162 (F1 0.279); after: see table above.",
          "- **SMS:** tried relaxing how far Naive Bayes alone can push a message (TRAIN recall 0.754 → 0.765) — gain too small and it "
          "hurt the India sample set, so it was **reverted**. Rules+NB is lower than NB-only because the fusion deliberately caps NB "
          "when no rule fires (designed for the 42-row sample model). That trade-off is reported, not hidden.",
          "- Remaining URL misses are mostly plain domains with no path (e.g. `http://www.example-shop.com`): lexical rules "
          "cannot tell these apart without page content or reputation data — future work.", ""]
    v = eval_voice()
    L += ["", "## Voice — NOT a benchmark", "",
          f"Voice-clone detection is **demonstration-grade only**: a signal heuristic checked on {v['n']} synthetic demo clips "
          f"(accuracy {v['accuracy']:.2f}). No public anti-spoofing corpus (e.g. ASVspoof) was used, so no real-world claim is made.", "",
          "## What these numbers mean (and don't)", "",
          "- They are honest held-out numbers on public datasets the detectors were not tuned on.",
          "- PhiUSIIL legitimate URLs are mostly site homepages while phishing URLs often have deep paths, so URL-shape cues are easier "
          "here than in real traffic. Real-world precision is likely lower.",
          "- The UCI SMS corpus is UK/Singapore SMS from ~2010 (prize/ringtone spam), not Indian 2020s scams (digital arrest, UPI, KYC). "
          "The India-specific rules are mostly *not exercised* by it; India-context performance is only shown on the small **synthetic** "
          "`datasets/sms/sms_samples.csv` set, which is not a benchmark.",
          "- Single split, single seed; no confidence intervals. With ~150 spam test messages, ±3–4 points of recall is within noise.",
          "- No adversarial / evasion testing was done.", ""]
    path.write_text("\n".join(L), encoding="utf-8")
    return path


if __name__ == "__main__":
    import sys
    if "--bench" in sys.argv:
        out = write_report()
        print(json.dumps({"url": bench_url(), "openphish": bench_openphish(), "sms": bench_sms()}, indent=2))
        print(f"report -> {out}")
    else:
        print(json.dumps(evaluate_all(), indent=2))
