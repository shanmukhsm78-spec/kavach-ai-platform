# Attack Mode — AI Pentester

Attack mode is an autonomous, multi-agent web pentester that runs **only against
a local lab you own**. It chains four stages and emits a professional report.

```
Recon  ─▶  Scanner  ─▶  Exploit (safe PoC)  ─▶  Reporter (Markdown + PDF)
```

## Design at a glance

| File | Role |
|------|------|
| `modes/attack/safety.py` | Scope guard — refuses any target that isn't loopback/RFC1918 |
| `modes/attack/recon.py` | Fetches the target, enumerates routes/forms/headers, fingerprints tech |
| `modes/attack/scanner.py` | Runs safe checks (headers, XSS, SQLi, dir listing, secrets, weak config) |
| `modes/attack/exploit.py` | Attaches a safe, non-destructive proof-of-concept per finding |
| `modes/attack/mitre.py` | Hardcoded MITRE ATT&CK technique mapping per check |
| `modes/attack/reporter.py` | Renders Markdown + PDF (reportlab); optional LLM summary |
| `modes/attack/llm_assist.py` | Optional LLM polish; **degrades gracefully** to deterministic text |
| `modes/attack/pipeline.py` | Orchestrates the four stages |
| `modes/attack/mocktarget/` | Deliberately-vulnerable FastAPI app for offline testing |

## Safety (important viva point)

Before any traffic is sent, `assert_local_target()` resolves the hostname and
**refuses unless every resolved IP is loopback or RFC1918/link-local**. This
blocks pointing the tool at real sites and DNS-rebinding surprises. Public
targets return HTTP 400 `Out of scope: …` from the API.

## Offline / no-paid-API operation

The pipeline is fully deterministic and runs with **no LLM**. If an LLM is
configured (`KAVACH_LLM=auto` + an OpenAI-compatible endpoint), it is used only
to polish the executive summary. Any error falls back to rule-based text, so
grading never breaks. Force offline with `KAVACH_LLM=off`.

## Run it

### Against the bundled mock target (no Docker needed)
```bash
# from repo root, with the venv active / PYTHONPATH=.
python -m pytest tests/ -v            # runs the whole pipeline offline
python -m modes.attack.mocktarget.app # or run the mock target on :8081 manually
```

### Against OWASP Juice Shop (realistic lab)
```bash
# start Juice Shop locally
docker compose -f docker/docker-compose.yml up juiceshop   # serves :3000
# or standalone:
docker run --rm -p 3000:3000 bkimminich/juice-shop
# then start the backend and scan
make backend
curl -X POST http://localhost:8000/attack/scan \
  -H 'Content-Type: application/json' \
  -d '{"target_url":"http://localhost:3000"}'
```

### API endpoints
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/attack/scan` | Run a scan; returns findings JSON + report paths |
| GET | `/attack/report/{scan_id}` | Download the PDF report |
| GET | `/attack/report/{scan_id}/markdown` | Download the Markdown report |
| GET | `/attack/result/{scan_id}` | Fetch the stored `result.json` |

Results are stored under `data/attack/<scan_id>/` (`report.md`, `report.pdf`,
`result.json`). A checked-in sample is in `docs/sample_report/`.

## Checks implemented & MITRE mapping

| Check | Severity | MITRE ATT&CK |
|-------|----------|--------------|
| Missing security headers | Medium | T1189 Drive-by Compromise |
| Reflected XSS | High | T1059.007 Scripting: JavaScript |
| Error-based SQL injection | Critical | T1190 Exploit Public-Facing Application |
| Directory listing | Medium | T1083 File and Directory Discovery |
| Exposed sensitive file (`.env`, `.git`) | High | T1552.001 Unsecured Credentials |
| Admin reachable without auth | High | T1078.001 Default Accounts |
| Verbose server/version banner | Low | T1592.002 Gather Victim Host Info |
| Cookie missing HttpOnly/Secure | Medium | T1539 Steal Web Session Cookie |
