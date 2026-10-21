# Phishing URL sample set

`urls_sample.csv` - 40 rows (20 legit, 20 phishing). **The phishing rows are
synthetic, hand-written in the style of public feeds** (they are not live
malicious sites - do not visit them). Legit rows are real homepages.

Expand for a real study with:
- PhishTank (https://phishtank.org/developer_info.php)
- OpenPhish community feed (https://openphish.com/)
- UCI "Phishing Websites" / "PhiUSIIL" datasets (https://archive.ics.uci.edu/)
- Tranco top-sites list for legit URLs (https://tranco-list.eu/)

Evaluate with: `.venv/bin/python -m modes.protect.evaluate`

## Real benchmark (`benchmark.csv`)
Built by `make protect-download` (`scripts/protect_download.py`) on 2026-10-21.
- **Source:** PhiUSIIL Phishing URL Dataset, A. Prasad & S. Chandra (2023), UCI ML Repository id 967,
  https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.zip — **CC BY 4.0**.
- **Rows:** 2,500 phishing + 2,500 legitimate unique URLs, sampled with seed 42 (from 235,795).
- **Columns:** `url,label,split` — stratified 80/20 train/test, seed 42.
- **Extra (not committed):** OpenPhish community feed https://openphish.com/feed.txt saved to
  `raw/openphish_feed.txt` (300 live URLs on 2026-10-21), used only for a recall check. Do not visit these URLs.
- Raw zips live in `raw/` (gitignored). Results: `docs/protect_benchmark.md`.
