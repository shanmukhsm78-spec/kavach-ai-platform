"""Scam SMS / message detector (Indian context).

Two transparent layers, combined:
  1. Rule layer - regex families for digital-arrest, KYC, OTP theft, lottery,
     UPI collect, job and loan scams + urgency + links. Each family adds points.
  2. ML layer  - a tiny *Multinomial Naive Bayes* written in pure Python and
     trained on datasets/sms/sms_samples.csv. We avoid scikit-learn on purpose
     (not installed, heavy); NB is the classic spam-filter model and is easy
     to explain in a viva: P(scam | words) ∝ P(scam) * Π P(word | scam).
Final score = rule points +/- an ML nudge - see score_sms().
"""
from __future__ import annotations

import csv
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from .common import make_result

DATA = Path(__file__).resolve().parents[2] / "datasets" / "sms" / "sms_samples.csv"

RULES: dict[str, tuple[int, str]] = {
    "digital_arrest": (55, r"digital arrest|\bcbi\b|cyber ?cell|police|narcotics|customs|arrest warrant|money laundering|fedex parcel|\bed\b officer|डिजिटल अरेस्ट|पुलिस"),
    "kyc": (40, r"\bkyc\b|pan (card )?(link|update)|account (will be )?(blocked|suspended|deactivated)|aadhaar.*(update|link)|केवाईसी"),
    "otp": (45, r"\b(share|send|tell|forward)\b.{0,25}\b(otp|pin|cvv)\b|\botp\b.{0,30}\b(share|send|tell|call)"),
    "lottery": (40, r"lottery|you (have )?won|winner|prize|lucky draw|kbc|jackpot|cashback of|लॉटरी|इनाम"),
    "upi_collect": (40, r"(scan|accept|approve).{0,30}(qr|upi|request|collect)|upi pin.{0,20}(receive|get)|enter (your )?upi pin"),
    "job_scam": (35, r"work from home|part[- ]time job|earn (rs\.?|₹|inr)? ?\d+.{0,15}(per|a) (day|hour)|registration fee|like youtube videos|telegram task"),
    "loan_scam": (30, r"pre[- ]?approved loan|instant loan|loan.{0,20}(no documents|without documents|in 5 minutes)|low interest loan"),
    "utility_cutoff": (40, r"(electricity|power|gas|connection).{0,30}(disconnect|cut)|बिजली.{0,20}कट"),
    "family_impersonation": (40, r"(hi|hello) (mom|mum|dad|papa|maa)\b|lost my phone.{0,40}new number|this is my new number"),
    "urgency": (15, r"immediately|urgent|within \d+ ?(hours|hrs|minutes)|today itself|last chance|expire|तुरंत"),
    "contains_link": (10, r"https?://|www\.|bit\.ly|\b[a-z0-9-]+\.(xyz|top|tk|in|com|link|click)/"),
}
_COMPILED = {k: (w, re.compile(p, re.I)) for k, (w, p) in RULES.items()}
_TOKEN = re.compile(r"[a-z\u0900-\u097f]{2,}")
# Safety advice that legit banks add ("do not share OTP") must not trigger OTP theft.
_SAFE_ADVICE = re.compile(r"(do not|don't|never) share", re.I)
_URL_RE = re.compile(r"(https?://\S+|www\.\S+|\b[a-z0-9-]+\.[a-z]{2,6}/\S*)", re.I)


def load_samples(path: Path = DATA) -> list[tuple[str, int]]:
    with open(path, encoding="utf-8") as fh:
        return [(r["text"], int(r["label"] == "scam")) for r in csv.DictReader(fh)]


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class NaiveBayes:
    """Minimal multinomial NB with Laplace smoothing (binary: 1=scam, 0=ham)."""

    def fit(self, rows: list[tuple[str, int]]) -> "NaiveBayes":
        self.counts = {0: Counter(), 1: Counter()}
        self.docs = Counter()
        for text, y in rows:
            self.docs[y] += 1
            self.counts[y].update(tokenize(text))
        self.vocab = set(self.counts[0]) | set(self.counts[1])
        self.totals = {c: sum(self.counts[c].values()) for c in (0, 1)}
        return self

    def predict_proba(self, text: str) -> float:
        n, v = sum(self.docs.values()), len(self.vocab) or 1
        logp = {}
        for c in (0, 1):
            lp = math.log((self.docs[c] + 1) / (n + 2))
            for t in tokenize(text):
                if t in self.vocab:
                    lp += math.log((self.counts[c][t] + 1) / (self.totals[c] + v))
            logp[c] = lp
        m = max(logp.values())
        e1, e0 = math.exp(logp[1] - m), math.exp(logp[0] - m)
        return e1 / (e1 + e0)


@lru_cache(maxsize=1)
def get_model() -> NaiveBayes | None:
    try:
        return NaiveBayes().fit(load_samples())
    except Exception:          # dataset missing -> rules only (graceful degradation)
        return None


def rule_score(text: str) -> tuple[int, list[str]]:
    score, codes = 0, []
    for code, (w, rx) in _COMPILED.items():
        if code == "otp" and _SAFE_ADVICE.search(text):
            continue
        if rx.search(text):
            score += w
            codes.append(code)
    return score, codes


def score_sms(text: str, model: NaiveBayes | None = None, use_ml: bool = True) -> dict:
    rs, codes = rule_score(text)
    feats = {"rule_score": rs}
    # A link inside the message is checked with the URL detector too.
    m = _URL_RE.search(text)
    if m:
        from .url_detector import score_url
        u = score_url(m.group(0))
        feats["link_risk"] = u["risk_score"]
        if u["risk_score"] >= 35:
            rs += 25
            codes.append("phishing_link")
    score, engine = float(rs), "rules"
    model = model if model is not None else (get_model() if use_ml else None)
    if model is not None:
        p = model.predict_proba(text)
        feats["ml_scam_probability"] = round(p, 3)
        engine = "rules+naive_bayes"
        # The ML vote nudges the rule score by at most +/-15 points. On its own
        # (no rule fired) it can reach "suspicious" but never "dangerous",
        # because a 42-row model is too small to be trusted alone.
        score = score + 30 * (p - 0.5) if rs else max(0.0, p - 0.5) * 80
        if p >= 0.9 and "ml_scam" not in codes:
            codes.append("ml_scam")
    return make_result("sms", text, score, codes, features=feats, engine=engine)
