"""Download public Protect-mode datasets and build held-out benchmark CSVs.

Run:  make protect-download   (needs internet once; everything after is offline)

Sources (raw files go to datasets/*/raw/, which is gitignored):
  * PhiUSIIL Phishing URL Dataset (UCI id 967, CC BY 4.0)
    https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.zip
  * SMS Spam Collection (UCI id 228, CC BY 4.0)
    https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip
  * OpenPhish community feed (optional, recent live phishing; NOT redistributed,
    kept in raw/ only, used as an extra out-of-distribution recall check)
    https://openphish.com/feed.txt

Processed outputs (committed, small):
  datasets/phishing/benchmark.csv  url,label,split   (2500 phishing + 2500 legit)
  datasets/sms/benchmark.csv       text,label,split  (full UCI corpus, 5574 rows)
Split = stratified 80/20 with SEED=42.
"""
from __future__ import annotations

import csv
import io
import random
import sys
import urllib.request
import zipfile
from pathlib import Path

SEED = 42
ROOT = Path(__file__).resolve().parents[1] / "datasets"
PHI_URL = "https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.zip"
SMS_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
OPENPHISH_URL = "https://openphish.com/feed.txt"
PER_CLASS = 2500


def fetch(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        print(f"downloading {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "kavach-benchmark/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            dest.write_bytes(r.read())
    return dest


def split(rows: list[dict], key: str) -> list[dict]:
    rng = random.Random(SEED)
    out = []
    for lab in sorted({r[key] for r in rows}):
        grp = [r for r in rows if r[key] == lab]
        rng.shuffle(grp)
        cut = int(len(grp) * 0.8)
        for i, r in enumerate(grp):
            out.append({**r, "split": "train" if i < cut else "test"})
    rng.shuffle(out)
    return out


def build_phishing() -> None:
    z = fetch(PHI_URL, ROOT / "phishing" / "raw" / "phiusiil.zip")
    with zipfile.ZipFile(z) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".csv"))
        reader = csv.DictReader(io.TextIOWrapper(zf.open(name), encoding="utf-8", errors="replace"))
        # PhiUSIIL: label 1 = legitimate, 0 = phishing
        pools = {"phishing": [], "legit": []}
        for r in reader:
            pools["phishing" if r["label"] == "0" else "legit"].append(r["URL"].strip())
    rng = random.Random(SEED)
    rows = []
    for lab, urls in pools.items():
        urls = sorted(set(urls))
        rng.shuffle(urls)
        rows += [{"url": u, "label": lab} for u in urls[:PER_CLASS]]
    write(ROOT / "phishing" / "benchmark.csv", ["url", "label", "split"], split(rows, "label"))
    try:
        fetch(OPENPHISH_URL, ROOT / "phishing" / "raw" / "openphish_feed.txt")
    except Exception as e:  # optional
        print(f"openphish feed skipped: {e}")


def build_sms() -> None:
    z = fetch(SMS_URL, ROOT / "sms" / "raw" / "sms_spam_collection.zip")
    with zipfile.ZipFile(z) as zf:
        text = zf.read("SMSSpamCollection").decode("utf-8", errors="replace")
    rows = []
    for line in text.splitlines():
        if "\t" in line:
            lab, msg = line.split("\t", 1)
            rows.append({"text": msg, "label": "scam" if lab == "spam" else "ham"})
    write(ROOT / "sms" / "benchmark.csv", ["text", "label", "split"], split(rows, "label"))


def write(path: Path, fields: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)")


if __name__ == "__main__":
    ok = True
    for fn in (build_phishing, build_sms):
        try:
            fn()
        except Exception as e:
            ok = False
            print(f"FAILED {fn.__name__}: {e}", file=sys.stderr)
    sys.exit(0 if ok else 1)
