# Defend mode — Sentinel (AI-agent firewall)

## What it is

A security layer that sits in front of an LLM agent and inspects three
channels in real time:

| Channel | What is inspected | Example threat |
|---------|-------------------|----------------|
| `prompt` | User input | "Ignore previous instructions…" |
| `document` | Retrieved docs / tool outputs | Indirect prompt injection hidden in a webpage |
| `tool_call` | Proposed tool invocations | `run_shell("rm -rf /")`, `send_email` to attacker |

Each inspection returns **ALLOW / SANITIZE / BLOCK** with a risk score and
human-readable reasons.

## Architecture

```
User / Red-team / Protected agent
            │
            ▼
   ┌─────────────────────┐
   │  Sentinel Firewall  │
   │  (modes/defend/)    │
   └─────────┬───────────┘
             │
   ┌─────────▼───────────┐
   │  DetectorEngine     │
   │  L1 rules (offline) │
   │  L2 learned sigs    │
   │  L3 optional LLM    │
   └─────────┬───────────┘
             │
             ├── tool_policy (allowlist + arg patterns)
             ├── store (events.jsonl, learned.jsonl, stats.json)
             └── red-team → self-heal loop
```

## Self-heal loop (the viva demo)

1. **Red-team run #1** — seeded corpus (classic injections + deliberate
   "stealth" paraphrases that bypass Layer-1). Record detection rate.
2. **Self-heal** — every bypassed payload is appended to
   `data/defend/learned.jsonl` and loaded as a new signature.
3. **Red-team run #2** — same corpus; stealth cases are now blocked.
   Detection rate goes up. Show the before/after numbers on the dashboard.

## Offline / grading

Set `KAVACH_LLM=off` (the pytest conftest already does this). The entire
Defend mode runs with deterministic rules — no model download, no network.

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/defend/status` | readiness |
| POST | `/defend/inspect` | single inspection |
| POST | `/defend/run-redteam` | one red-team batch |
| POST | `/defend/self-heal` | `{"run_demo": true}` for the full loop |
| POST | `/defend/demo-chain` | indirect-injection chain demo |
| GET | `/defend/stats` | counters + before/after rates |
| GET | `/defend/events` | timeline |

## How to run

```bash
# from repo root
make backend            # uvicorn on :8000
make frontend           # Next.js on :3000 → open /defend

# offline tests
KAVACH_LLM=off .venv/bin/pytest tests/test_defend_firewall.py -v

# one-shot self-heal demo from the CLI
KAVACH_LLM=off PYTHONPATH=.:backend .venv/bin/python -c \
  "from modes.defend.pipeline import run_self_heal_demo; \
   import json; print(json.dumps(run_self_heal_demo(), indent=2))"
```

## Key files

```
modes/defend/
  models.py            dataclasses (InspectionResult, AttackCase, …)
  detectors.py         layered rule engine + learned signatures
  tool_policy.py       tool allowlist / deny list / arg patterns
  firewall.py          Firewall class + process singleton
  corpus.py            seeded red-team attacks (detectable + stealth)
  redteam.py           batch runner + detection-rate math
  self_heal.py         ingest bypasses → learned.jsonl
  protected_agent.py   mock agent showing the injection→tool chain
  pipeline.py          orchestration used by the API
  store.py             data/defend persistence
  llm_assist.py        optional LLM judge / variant generator
```
