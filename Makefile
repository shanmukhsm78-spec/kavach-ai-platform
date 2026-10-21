# Kavach AI Platform — common developer tasks
.PHONY: help install backend frontend up lab down health

VENV ?= .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn

help:
	@echo "Kavach AI Platform"
	@echo "  make install   - create .venv + install backend + frontend deps"
	@echo "  make backend   - run FastAPI (uvicorn) on :8000"
	@echo "  make frontend  - run Next.js on :3000"
	@echo "  make up        - docker compose up --build (backend + frontend)"
	@echo "  make lab       - docker compose up with the OWASP Juice Shop lab (profile lab)"
	@echo "  make down      - docker compose down"
	@echo "  make health    - curl /health"

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt
	cd frontend && npm install

backend:
	cd backend && KAVACH_LLM=$${KAVACH_LLM:-off} PYTHONPATH=..:$$PYTHONPATH ../$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

up:
	docker compose -f docker/docker-compose.yml up --build

lab:
	docker compose -f docker/docker-compose.yml --profile lab up --build

down:
	docker compose -f docker/docker-compose.yml down

health:
	curl -s http://localhost:8000/health | $(PY) -m json.tool

.PHONY: test protect-eval protect-download protect-bench voice-samples
test:
	KAVACH_LLM=off $(VENV)/bin/pytest -q

protect-eval:
	KAVACH_LLM=off $(PY) -m modes.protect.evaluate

voice-samples:
	$(PY) scripts/make_voice_samples.py

protect-download:
	$(PY) scripts/protect_download.py

protect-bench:
	KAVACH_LLM=off $(PY) -m modes.protect.evaluate --bench
