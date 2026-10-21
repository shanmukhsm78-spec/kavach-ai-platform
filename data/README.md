# `data/` — runtime output (mostly git-ignored)

This directory holds artifacts **generated at runtime**. It is *not* where the
committed sample datasets live — those are in `datasets/` (phishing URLs, scam
SMS, voice samples) and `docs/sample_report/` (a sample Attack report).

| Subdir | Written by | Contents |
|--------|-----------|----------|
| `data/attack/`  | Attack mode  | Per-scan folders: `result.json`, Markdown + PDF reports. |
| `data/defend/`  | Defend mode  | `events.jsonl`, `stats.json`, `learned.jsonl` (self-heal signatures). |
| `data/protect/` | Protect mode | Check history / counters. |

Each subdir keeps a `.gitkeep` so the structure exists on a fresh clone, but the
generated files inside are git-ignored (see `.gitignore`). Deleting the contents
is safe — the modes recreate them on the next run.
