# Protect mode — Kavach Shield (anti-scam detector)

Protects ordinary users from phishing links, scam SMS and AI voice clones.
Every detector returns the same shape:

```json
{ "risk_score": 0-100, "verdict": "safe|suspicious|dangerous",
  "reasons": [{"code": "kyc", "en": "...", "hi": "..."}],
  "explanation": {"en": "...", "hi": "...", "llm": "(optional)"} }
```
Thresholds: `>= 35` suspicious, `>= 65` dangerous (`modes/protect/common.py`).

## Code map
| File | Role |
|---|---|
| `modes/protect/url_detector.py` | Phishing URL: lexical/heuristic features + weights |
| `modes/protect/sms_detector.py` | Scam SMS: regex families + pure-Python Naive Bayes |
| `modes/protect/voice_detector.py` | Voice clone: stdlib `wave` signal features (demo-grade) |
| `modes/protect/i18n.py` | English + Hindi reason / verdict templates, 1930 helpline |
| `modes/protect/llm_assist.py` | Optional LLM rewording (`KAVACH_LLM=off|auto`) |
| `modes/protect/store.py` | `data/protect/checks.jsonl`, `stats.json`, `uploads/` |
| `modes/protect/evaluate.py` | Sample-set train/eval (accuracy, precision, recall) |
| `backend/app/routers/protect.py` | API routes |
| `frontend/app/protect/page.tsx` | Dashboard page (3 tabs, EN/HI toggle) |
| `extension/` | MV3 popup: checks current URL + selected text |
| `scripts/make_voice_samples.py` | Regenerates synthetic voice samples |

## 1. Phishing URL detector
Features (weight): IP host (40), `@` in URL (35), punycode (35), typosquat of a
known brand via edit distance / digit swaps / Cyrillic homoglyphs (50), brand in
subdomain/path on a non-brand site (40), shortener (35), suspicious TLD (25),
>=4 dots (15), no HTTPS (15), sensitive words like login/kyc/verify (15),
>=2 hyphens (10), >90 chars (10), non-standard port (15). Trusted domains −50.
Deterministic, no model file, every point explainable.

## 2. Scam SMS detector
Rule families: digital arrest/police/CBI, KYC/account blocked, OTP sharing
(skipped when the message says "do not share"), lottery/prize, UPI collect/QR,
job scam, loan scam, utility cut-off, "hi mom new number", urgency, links (the
link is also scored by the URL detector).
ML: **Multinomial Naive Bayes in pure Python** (scikit-learn is not installed and
is unnecessary for 42 rows). The NB probability nudges the rule score by ±15; on
its own it can only reach "suspicious".

## 3. Voice-clone detector — HONEST LIMITATION
This is a **demonstration-grade heuristic**, not a real deepfake detector.
Features: loudness variation (`rms_cv`), pause ratio, high-frequency noise,
zero-crossing variation (pitch proxy). The sample clips in `datasets/voice` are
*synthetic* signals. Modern voice clones would fool it. A real deployment needs
an anti-spoofing model (e.g. AASIST / RawNet2) trained on **ASVspoof 2019/2021**
and tested on "In-the-Wild" data — listed as future work.

## API
| Method | Path | Body |
|---|---|---|
| POST | `/protect/url` | `{"url": "...", "language": "en"}` |
| POST | `/protect/sms` | `{"text": "..."}` |
| POST | `/protect/audio` | multipart `file=@clip.wav` **or** form `path=datasets/voice/fake/fake_1.wav` (paths restricted to `datasets/voice/`) |
| GET | `/protect/stats` | counters + recent checks |
| GET | `/protect/eval` | sample accuracy |
| GET | `/protect/status` | readiness |

```bash
curl -s -X POST localhost:8000/protect/url -H 'content-type: application/json' -d '{"url":"http://sbi-kyc-update.xyz/verify"}'
curl -s -X POST localhost:8000/protect/audio -F file=@datasets/voice/fake/fake_1.wav
```

## Sample results (offline, `python -m modes.protect.evaluate`)
| Detector | n | Accuracy | Precision | Recall |
|---|---|---|---|---|
| URL (rules) | 40 | 1.000 | 1.000 | 1.000 |
| SMS rules + NB (leave-one-out) | 42 | 0.881 | 0.905 | 0.864 |
| SMS rules only | 42 | 0.929 | 1.000 | 0.864 |
| Voice heuristic (synthetic) | 8 | 1.000 | 1.000 | 1.000 |

Caveat for the viva: the rules were written while looking at these samples, so
these are *sanity* numbers, not a benchmark.

## Real benchmark (held-out test, `make protect-download && make protect-bench`)
Full methodology and honesty notes: [`protect_benchmark.md`](protect_benchmark.md).
PhiUSIIL URLs (UCI 967) and UCI SMS Spam Collection (UCI 228), stratified 80/20, seed 42.

| Detector | n (test) | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|---|
| URL (rules) | 1000 | 0.714 | 1.000 | 0.428 | 0.599 |
| SMS rules only | 1116 | 0.888 | 0.857 | 0.200 | 0.324 |
| SMS rules + NB (NB fit on train only) | 1116 | 0.962 | 0.982 | 0.733 | 0.839 |
| SMS NB only | 1116 | 0.983 | 0.952 | 0.920 | 0.936 |

OpenPhish live feed (300 URLs): recall 0.513. Voice: demonstration-grade, not benchmarked.
The UCI SMS corpus is not Indian-context; India scam rules are only checked on the synthetic samples.
