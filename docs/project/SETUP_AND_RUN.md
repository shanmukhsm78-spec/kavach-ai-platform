# Kavach AI Platform: Setup and Run

Clean quickstart for a fresh machine. The platform is **offline-first**: with the default `KAVACH_LLM=off` you need **no Internet after install**, no API key and no GPU.

> For the architecture, the viva demo script and examiner Q&A, see the other files in `docs/project/`.

---

## 0. Prerequisites

| Tool | Minimum | Notes |
|---|---|---|
| Python | 3.11+ | 3.12 / 3.13 fine. Docker image uses 3.12. |
| Node.js + npm | 18+ | Docker image uses Node 20. |
| Git | any recent | |
| (Optional) Docker + Docker Compose | recent | One-command run + Juice Shop lab |
| (Optional) Ollama | recent | Local LLM; default model `llama3.1:8b` |
| (Optional) Chrome / Edge | recent | For the Kavach Shield extension |

Check:
```bash
python3 --version    # >= 3.11
node --version       # >= 18
npm --version
```

---

## 1. Clone and configure

```bash
git clone <your-repo-url> kavach
cd kavach
cp .env.example .env
# Defaults are already offline-safe. Edit only if you want a hosted LLM later.
```

Key variables in `.env` / `.env.example`:

| Variable | Default | Meaning |
|---|---|---|
| `KAVACH_LLM` | `off` | `off` = never call an LLM (recommended for grading). `auto` = try, fall back on any error. |
| `LLM_PROVIDER` | `local` | `local` or `openai` (any OpenAI-compatible host) |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | Ollama's OpenAI-compatible endpoint |
| `LLM_MODEL` | `llama3.1:8b` | Model name the endpoint expects |
| `LLM_API_KEY` | `not-needed-for-local` | Required only for hosted endpoints |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | CORS allowlist for the dashboard |
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000` | Where the frontend sends API calls |

> The agent core reads LLM settings from **process environment variables** (`os.getenv`). `make backend` exports `KAVACH_LLM` for you. If you start uvicorn by hand and want a custom `LLM_BASE_URL`, export it in that shell (or rely on Docker Compose `environment:`).

---

## 2. Install

```bash
make install
```

This creates `.venv`, upgrades pip, installs `backend/requirements.txt`, and runs `npm install` in `frontend/`.

Manual equivalent:
```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

---

## 3. Run the tests (offline)

```bash
make test
# equivalent: KAVACH_LLM=off .venv/bin/pytest -q
```

**Expected:** `37 passed` (plus a few harmless uvicorn deprecation warnings).

What the suite covers: Attack scope guard + full pipeline against the in-process VulnShop mock; Defend injection / tools / red-team / self-heal / API; Protect URL / SMS / audio / bilingual explanations / sample eval / API. `tests/conftest.py` forces `KAVACH_LLM=off`, so no network or model is needed.

Also useful:
```bash
make protect-eval
# → URL / SMS (rules+NB leave-one-out and rules-only) / voice metrics
```

---

## 4. Run in development (two terminals)

**Terminal A — backend**
```bash
make backend
# → http://localhost:8000
# → interactive docs: http://localhost:8000/docs
```

**Terminal B — frontend**
```bash
make frontend
# → http://localhost:3000
```

Smoke check:
```bash
make health
# {"status": "ok", "app": "Kavach AI Platform", "version": "0.1.0", ...}
```

Open `http://localhost:3000` and use the Attack / Defend / Protect pages.

### Manual (without Make)
```bash
# backend
cd backend
KAVACH_LLM=off PYTHONPATH=.. ../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# frontend (other terminal)
cd frontend && npm run dev
```

---

## 5. One-command Docker run

```bash
make up
# equivalent: docker compose -f docker/docker-compose.yml up --build
```

Brings up:
- **backend** on `:8000` (`KAVACH_LLM=off` in the image)
- **frontend** on `:3000`

Stop:
```bash
make down
```

---

## 6. Optional: local vulnerable lab for Attack mode

### Option A — bundled mock target (no Docker, best for demos and CI)
```bash
PYTHONPATH=. .venv/bin/python -m modes.attack.mocktarget.app
# → http://127.0.0.1:8081
```
Then in the Attack page (or via curl) scan `http://127.0.0.1:8081`. Expected: **6 findings** (1 Critical, 3 High, 2 Medium).

### Option B — OWASP Juice Shop via Compose (realistic lab)
```bash
make lab
# starts backend + frontend + juiceshop (profile "lab")
# Juice Shop is on host port 3001 (so it does not clash with the frontend on 3000)
```
Point Attack mode at `http://localhost:3001`.

Standalone Juice Shop (without the rest of Compose):
```bash
docker run --rm -p 3001:3000 bkimminich/juice-shop
```

> Attack mode **refuses** any target that does not resolve entirely to loopback / RFC 1918 / link-local. Public sites return HTTP 400 `Out of scope`.

---

## 7. Optional: enable a local or hosted LLM

The LLM is never required. When enabled (`KAVACH_LLM=auto`) it may:
- **Attack:** rewrite the executive summary.
- **Defend:** escalate a borderline verdict (never downgrade a BLOCK); paraphrase stealth cases for the red team.
- **Protect:** rewrite the explanation in friendlier words (never change score/verdict).

### Local (Ollama)
```bash
# install from https://ollama.com , then:
ollama pull llama3.1:8b
ollama serve   # listens on :11434

# in .env (or export in the shell that runs the backend):
#   KAVACH_LLM=auto
#   LLM_PROVIDER=local
#   LLM_BASE_URL=http://localhost:11434/v1
#   LLM_MODEL=llama3.1:8b
make backend   # if you set KAVACH_LLM in .env, export it:  KAVACH_LLM=auto make backend
```
From Docker Compose, the backend reaches a host Ollama via `host.docker.internal:11434`.

### Hosted (OpenAI-compatible)
```bash
# in .env:
#   KAVACH_LLM=auto
#   LLM_PROVIDER=openai
#   LLM_BASE_URL=https://api.openai.com/v1
#   LLM_API_KEY=sk-...
#   LLM_MODEL=gpt-4o-mini
```
Any failure (no server, bad key, timeout) silently falls back to the deterministic path, so demos never break.

---

## 8. Load the Kavach Shield browser extension

1. Start the backend (`make backend`).
2. Chrome / Edge → `chrome://extensions` (or `edge://extensions`).
3. Enable **Developer mode**.
4. **Load unpacked** → select the `extension/` folder in this repo.
5. Open any page, optionally select some text, click the **Kavach Shield** icon.
6. Tick **हिंदी** to see warnings in Hindi.

The popup calls `POST http://localhost:8000/protect/url` (current tab URL) and, if text is selected, `POST /protect/sms`. Nothing is sent until you click the icon.

---

## 9. Useful Make targets

| Target | What it does |
|---|---|
| `make install` | Create `.venv`, install backend + frontend deps |
| `make backend` | Uvicorn on `:8000` with `KAVACH_LLM=off` by default |
| `make frontend` | Next.js dev server on `:3000` |
| `make test` | `pytest -q` offline |
| `make protect-eval` | Sample-set accuracy for URL / SMS / voice |
| `make voice-samples` | Regenerate the 8 synthetic `.wav` clips |
| `make health` | `curl` `/health` |
| `make up` | Docker Compose up --build (backend + frontend) |
| `make lab` | Compose with the Juice Shop profile |
| `make down` | Compose down |

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `make test` fails importing `modes` / `app` | Wrong working directory, or venv missing | Run from the **repo root**. Re-run `make install`. |
| `ModuleNotFoundError: openai` / `reportlab` / … | Backend deps not installed | `.venv/bin/pip install -r backend/requirements.txt` |
| Frontend: `Failed to fetch` / CORS error | Backend down, or frontend not on port 3000 | Start `make backend`. CORS allows only `FRONTEND_ORIGIN` (default `http://localhost:3000`). |
| Attack scan: `Out of scope: …` | Target resolves to a public IP | Use `http://127.0.0.1:8081` (mock) or `http://localhost:3001` (Juice Shop). |
| Attack scan: "Could not reach target" / empty findings | Lab not running | Start the mock target or `make lab`. |
| Defend self-heal shows 100 % → 100 % | Learned signatures already persisted | `rm -f data/defend/learned.jsonl data/defend/stats.json data/defend/events.jsonl && rm -rf data/defend/redteam`, then **restart** `make backend` (the firewall caches signatures in memory). |
| Protect audio: `path must be a .wav under datasets/voice/` | Path outside the allowlist, or file missing | Use a path like `datasets/voice/fake/fake_1.wav`, or upload a `.wav` file. |
| Extension: "Kavach backend not reachable" | Backend not on `:8000` | `make backend`, confirm `make health`. |
| Port 8000 / 3000 already in use | Another process (or an old Kavach) | `lsof -i :8000` / `lsof -i :3000`, then kill, or `make down`. |
| Docker backend cannot see host Ollama | Missing host gateway | Compose already sets `extra_hosts: host.docker.internal:host-gateway`. On Linux, confirm Docker ≥ 20.10. |
| `npm install` fails (peer deps / network) | Registry or Node version | Use Node 18 or 20. Retry. If needed: `cd frontend && npm install --legacy-peer-deps`. |
| PDF looks empty / won't open | Scan failed before the reporter | Re-run the scan; confirm `data/attack/<scan_id>/report.pdf` starts with `%PDF` (`xxd -l 4 …`). |
| Want a clean slate | Runtime artefacts | Deleting the *contents* of `data/attack/`, `data/defend/`, `data/protect/` is safe (keep the `.gitkeep` files). Modes recreate what they need. |

---

## 11. Project documentation map

| File | Contents |
|---|---|
| `README.md` | Project overview and quick start |
| `docs/architecture.md` | Short architecture + Mermaid overview |
| `docs/attack_mode.md` / `defend_mode.md` / `protect_mode.md` | Per-mode developer docs |
| `docs/sample_report/` | Sample Attack report (MD, PDF, JSON) |
| `docs/project/PROJECT_REPORT.md` | Full final-year project report |
| `docs/project/ARCHITECTURE.md` | Expanded diagrams, tech stack, data flow |
| `docs/project/DEMO_SCRIPT.md` | 8–10 minute viva demo |
| `docs/project/VIVA_QA.md` | Examiner Q&A prep |
| `docs/project/SETUP_AND_RUN.md` | This file |

---

## 12. Safety reminder

- Attack mode is for **authorised local labs only** (VulnShop, Juice Shop, DVWA, your own VMs). Do not point it at systems you do not own or have written permission to test.
- This is a **college final-year project**, not a production security product.
- Protect mode uses public / bundled samples and user-submitted inputs. There is **no live phone interception**.
