# Kavach AI Platform

**Self-defending AI security for a world where attackers and defenders are both AI.**

Kavach is a final-year CSE / IT project (cybersecurity + AI) by **Shanmukh**.
One shared agent brain powers three modes — **Attack**, **Defend**, and
**Protect** — behind a single FastAPI backend and one Next.js dashboard. The
pentester invents attacks, the Sentinel firewall learns from them, and the
hardened detector warns ordinary people about phishing, scam SMS and voice clones.

---

## The three modes

| Mode | Codename | What it does (MVP) |
|------|----------|--------------------|
| **Attack** | AI Pentester | Multi-agent team (Recon → Scanner → Exploit → Reporter) scans a *local* vulnerable lab (OWASP Juice Shop / DVWA), maps findings to MITRE ATT&CK, emits a PDF + Markdown report. |
| **Defend** | Sentinel | AI-agent firewall that inspects prompts, retrieved docs and tool calls; blocks prompt injection, data exfil and dangerous tools; red-team AI + self-heal loop; live timeline + block/allow stats. |
| **Protect** | Kavach Shield | Detects phishing URLs, scam SMS and AI voice-clone audio; multilingual warnings (English + Hindi); browser-extension demo + web dashboard; risk score with plain-language explanation. |

## Architecture (overview)

```
                 ┌──────────────────────────────────────┐
                 │   Next.js Dashboard  +  Browser Ext  │
                 └───────────────┬──────────────────────┘
                                 │ HTTP
                 ┌───────────────▼──────────────────────┐
                 │         FastAPI  (:8000)             │
                 │  /attack/*   /defend/*   /protect/*  │
                 └───────┬──────────┬──────────┬────────┘
                         │          │          │
              ┌──────────▼──┐  ┌────▼────┐  ┌──▼──────────┐
              │   Attack    │  │ Defend  │  │   Protect   │
              │  pipeline   │  │Sentinel │  │   detectors │
              └──────┬──────┘  └────┬────┘  └──────┬──────┘
                     │              │              │
                     └──────────────┼──────────────┘
                                    ▼
                     ┌──────────────────────────────┐
                     │  Shared Agent Core (agents/) │
                     │  LLMClient (OpenAI-compat)   │
                     │  local Ollama  or  hosted    │
                     └──────────────────────────────┘
```

See [`docs/architecture.md`](docs/architecture.md) for the Mermaid diagram and
request-flow notes. Attack mode details: [`docs/attack_mode.md`](docs/attack_mode.md). Defend / Sentinel details: [`docs/defend_mode.md`](docs/defend_mode.md). Protect / Kavach Shield details: [`docs/protect_mode.md`](docs/protect_mode.md).

## Tech stack

- **Backend:** Python 3.12+, FastAPI, Uvicorn, Pydantic, OpenAI-compatible client
- **Frontend:** Next.js 14 (App Router), React 18, Tailwind CSS, TypeScript
- **Agents:** Shared `Agent` + `LLMClient` (pluggable via env; default local)
- **Reports:** Markdown + ReportLab (PDF)
- **Lab:** OWASP Juice Shop / DVWA (Docker, Attack mode only)
- **Extension:** Chrome MV3 stub under `extension/`
- **Mobile:** Expo (React Native + TypeScript) companion app for Protect mode under `mobile/`
- **Ops:** Docker Compose + Makefile

## Repo layout

```
kavach/
├── agents/          # shared LLM agent core
├── backend/         # FastAPI app + routers
├── modes/           # attack / defend / protect pipelines
├── frontend/        # Next.js dashboard
├── extension/       # Kavach Shield browser-extension stub
├── mobile/          # Kavach Shield mobile app (Expo, Android + iOS)
├── datasets/        # public dataset placeholders + README
├── docker/          # Dockerfiles + compose
├── docs/            # architecture, etc.
├── Makefile
├── LICENSE          # MIT, author Shanmukh
└── README.md
```

## Quick start

### Prerequisites

- Python 3.11+ (3.12/3.13 fine)
- Node.js 18+ and npm
- (Optional) Docker + Docker Compose for one-command run
- (Optional) [Ollama](https://ollama.com) with `llama3.1:8b` for a local LLM

### 1. Clone & configure

```bash
git clone <your-repo-url> kavach
cd kavach
cp .env.example .env
# edit .env if you want a hosted LLM instead of local
```

### 2. Install

```bash
make install
# or:
#   python3 -m pip install -r backend/requirements.txt
#   cd frontend && npm install
```

### 3. Run (dev)

Terminal A — backend:

```bash
make backend
# → http://localhost:8000/docs
```

Terminal B — frontend:

```bash
make frontend
# → http://localhost:3000
```

Or one-command with Docker:

```bash
make up
```

### 4. Smoke check

```bash
make health
# {"status":"ok","app":"Kavach AI Platform", ...}
```

### 5. Mobile app (optional)

A phone companion for Protect mode (check URLs / scam SMS with EN+HI explanations). Run the backend with `--host 0.0.0.0`, then `cd mobile && npm install && npx expo start` and scan the QR with Expo Go. See [`mobile/README.md`](mobile/README.md).

## Safety / ethics (read this)

- **Attack mode is for authorized local labs only** (Juice Shop, DVWA, your own VMs).
  Do not point it at systems you do not own or have written permission to test.
- This is a **college final-year project**, not a production security product.
- Protect mode uses public datasets and uploaded samples — no live phone
  interception in v1.

## Future work / out of scope for v1

- Live phone-call listening / interception
- Real company-network / internet-facing pentests
- Fully automatic self-healing production model training loop
- Mobile app store release
- Multi-user auth, RBAC, and audit trails
- Paper-quality evaluation suite (planned as stretch if time allows)

## Author

**Shanmukh** — CSE / IT, cybersecurity + AI focus. Solo final-year project (~2 months).

## License

MIT — see [`LICENSE`](LICENSE).

## Attack mode (AI pentester) — quickstart

Attack mode is implemented end-to-end (Recon → Scanner → Exploit → Reporter),
runs offline with no paid APIs, and only scans local labs. See
[`docs/attack_mode.md`](docs/attack_mode.md) for full details.

```bash
# Offline test (spins up a bundled vulnerable mock target, no Docker needed):
PYTHONPATH=. .venv/bin/python -m pytest tests/ -v

# Realistic lab with OWASP Juice Shop:
docker compose -f docker/docker-compose.yml up juiceshop   # :3000
make backend                                               # :8000
curl -X POST http://localhost:8000/attack/scan \
  -H 'Content-Type: application/json' -d '{"target_url":"http://localhost:3000"}'
```

A sample generated report is checked in at
[`docs/sample_report/`](docs/sample_report/).
