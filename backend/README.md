# Backend (FastAPI)

```bash
# from repo root
python3 -m pip install -r backend/requirements.txt
cd backend
PYTHONPATH=.. uvicorn app.main:app --reload --port 8000
```

Routes:
- `GET  /health`
- `GET  /attack/status`  `POST /attack/scan`
- `GET  /defend/status`  `POST /defend/inspect`  `GET /defend/stats`
- `GET  /protect/status` `POST /protect/check`
