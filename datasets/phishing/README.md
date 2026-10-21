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
