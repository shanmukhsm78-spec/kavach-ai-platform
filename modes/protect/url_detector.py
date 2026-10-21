"""Phishing URL detector - deterministic lexical + heuristic features.

How it works (viva summary):
  1. Parse the URL and extract ~14 explainable features (IP host, '@', punycode,
     typosquatting via edit distance, suspicious TLD, shortener, ...).
  2. Each feature that fires adds a fixed weight to a 0-100 risk score.
  3. Well-known trusted domains get a strong negative weight.
No ML model is needed, so results are reproducible and every point of the
score can be explained to the examiner.
"""
from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from .common import make_result

# Brands commonly impersonated in India + globally -> their real domains.
BRANDS = {
    "sbi": ["sbi.co.in", "onlinesbi.sbi", "onlinesbi.com"],
    "hdfc": ["hdfcbank.com"], "icici": ["icicibank.com"], "axis": ["axisbank.com"],
    "paytm": ["paytm.com"], "phonepe": ["phonepe.com"], "amazon": ["amazon.in", "amazon.com"],
    "flipkart": ["flipkart.com"], "google": ["google.com", "google.co.in"],
    "paypal": ["paypal.com"], "apple": ["apple.com"], "microsoft": ["microsoft.com", "live.com"],
    "netflix": ["netflix.com"], "facebook": ["facebook.com"], "instagram": ["instagram.com"],
    "whatsapp": ["whatsapp.com"], "irctc": ["irctc.co.in"], "incometax": ["incometax.gov.in"],
    "uidai": ["uidai.gov.in"], "github": ["github.com"],
}
TRUSTED = {d for ds in BRANDS.values() for d in ds} | {
    "gov.in", "nic.in", "wikipedia.org", "youtube.com", "linkedin.com", "npci.org.in",
    "rbi.org.in", "cybercrime.gov.in", "python.org", "stackoverflow.com"}
SUSPICIOUS_TLDS = {"xyz", "top", "tk", "ml", "ga", "cf", "gq", "buzz", "click", "link",
                   "work", "info", "online", "site", "live", "rest", "icu", "shop", "cyou"}
SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "is.gd", "cutt.ly", "rb.gy",
              "ow.ly", "shorturl.at", "tiny.cc"}
SENSITIVE = ("login", "verify", "kyc", "update", "secure", "account", "banking",
             "signin", "wallet", "otp", "reward", "refund", "confirm", "suspend")

CONFUSABLES = {"а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x",
               "і": "i", "ӏ": "l", "ԁ": "d", "ɡ": "g", "ο": "o", "ν": "v"}

# feature -> weight (points added to the risk score when it fires)
WEIGHTS = {
    "ip_host": 40, "at_symbol": 35, "punycode": 35, "typosquat": 50,
    "brand_not_owner": 40, "shortener": 35, "suspicious_tld": 25,
    "many_subdomains": 15, "no_https": 15, "sensitive_words": 15,
    "many_hyphens": 10, "long_url": 10, "non_std_port": 15,
}
TRUSTED_BONUS = -50


def _levenshtein(a: str, b: str) -> int:
    """Classic edit distance (small strings, O(n*m) is fine)."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _registered_domain(host: str) -> str:
    """Rough eTLD+1 (handles co.in / gov.in style two-part suffixes)."""
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in ("co", "gov", "org", "net", "ac", "nic"):
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _is_trusted(host: str) -> bool:
    return any(host == t or host.endswith("." + t) for t in TRUSTED)


def extract_features(url: str) -> dict:
    raw = url.strip()
    if "://" not in raw:
        raw = "http://" + raw
    p = urlparse(raw)
    host = (p.hostname or "").lower()
    reg = _registered_domain(host)
    label = reg.split(".")[0]                    # e.g. "paypa1" from paypa1.com
    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    lower = raw.lower()

    try:
        ipaddress.ip_address(host); is_ip = True
    except ValueError:
        is_ip = False

    trusted = _is_trusted(host)
    # Typosquat: registered label is 1-2 edits away from a brand (but not equal).
    # Punycode look-alikes: decode xn-- and map Cyrillic/Greek look-alike letters.
    homoglyph = False
    if label.startswith("xn--"):
        try:
            skeleton = "".join(CONFUSABLES.get(ch, ch) for ch in label.encode().decode("idna"))
            homoglyph = skeleton in BRANDS          # e.g. Cyrillic "аpple" -> "apple"
        except UnicodeError:
            pass
    normalized = label.replace("0", "o").replace("1", "l").replace("3", "e").replace("@", "a")
    typo = (not trusted) and homoglyph or (not trusted) and any(
        (0 < _levenshtein(label, b) <= (1 if len(b) <= 4 else 2)) or (normalized == b != label)
        for b in BRANDS)
    # Brand name in subdomain/path while the site is not owned by the brand.
    brand_elsewhere = (not trusted) and any(
        b in lower.replace(reg, "", 1) or (b in label and label != b) for b in BRANDS)

    f = {
        "host": host, "registered_domain": reg, "length": len(raw),
        "ip_host": is_ip,
        "at_symbol": "@" in p.netloc or "@" in p.path,
        "punycode": "xn--" in host,
        "no_https": p.scheme != "https",
        "suspicious_tld": tld in SUSPICIOUS_TLDS,
        "shortener": reg in SHORTENERS or host in SHORTENERS,
        "many_subdomains": host.count(".") >= 4,
        "typosquat": typo,
        "brand_not_owner": brand_elsewhere and not typo,
        "long_url": len(raw) > 90,
        "many_hyphens": reg.replace("xn--", "").count("-") >= 2,
        "sensitive_words": (not trusted) and any(w in lower for w in SENSITIVE),
        "non_std_port": p.port not in (None, 80, 443),
        "trusted_domain": trusted and not is_ip,
    }
    return f


def score_url(url: str) -> dict:
    f = extract_features(url)
    score, codes = 0.0, []
    for name, w in WEIGHTS.items():
        if f.get(name):
            score += w
            codes.append(name)
    if f["trusted_domain"]:
        score += TRUSTED_BONUS
        codes.append("trusted_domain")
    return make_result("url", url, score, codes, features=f)
