# Datasets

This folder holds **public** datasets used by Protect mode (and later by
Defend's self-heal store). Large binary files are **not** committed — add them
locally and keep them out of git (see `.gitignore`).

## Suggested public sources

| Purpose | Suggested source | Notes |
|---------|------------------|-------|
| Phishing URLs | [PhishTank](https://phishtank.org/), [OpenPhish](https://openphish.com/), or the URLhaus feed | Use recent dumps; keep a small sample (~1k) for demos |
| Scam / spam SMS | [SMS Spam Collection (UCI)](https://archive.ics.uci.edu/dataset/228/sms+spam+collection), or Indian scam-SMS research corpora | Prefer English + Hindi if available |
| Voice-clone / deepfake audio | [ASVspoof](https://www.asvspoof.org/), [FakeAVCeleb](https://github.com/DASH-Lab/FakeAVCeleb) | Download a tiny subset for the demo; do not redistribute |

## Layout (create locally)

```
datasets/
  phishing/
    urls_train.csv
    urls_demo.csv
  sms/
    sms_spam.csv
  voice/
    real/
    fake/
```

## How to add

```bash
mkdir -p datasets/phishing datasets/sms datasets/voice/{real,fake}
# download into those folders, then keep originals out of git
```

Placeholders (`.gitkeep`) keep empty folders in the repo.
