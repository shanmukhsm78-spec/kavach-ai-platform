"""Attack mode routes — AI pentester (Recon → Scanner → Exploit → Reporter).

POST /attack/scan   -> run a scan against a local lab, return findings + paths
GET  /attack/report/{scan_id}         -> download the PDF report
GET  /attack/report/{scan_id}/markdown-> download the Markdown report
GET  /attack/result/{scan_id}         -> fetch the stored result JSON
"""
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# modes/ lives at the repo root, which is on PYTHONPATH (see Makefile/Dockerfile).
from modes.attack import pipeline
from modes.attack.safety import ScopeError

router = APIRouter(prefix="/attack", tags=["attack"])


class ScanRequest(BaseModel):
    target_url: str = "http://localhost:3000"  # local lab, e.g. Juice Shop
    scope: str = "web"  # web | api | network


@router.get("/status")
def status():
    return {"mode": "attack", "status": "ready", "agents": pipeline.STAGES}


@router.post("/scan")
def scan(req: ScanRequest):
    """Kick off a scan and return the findings + report paths synchronously."""
    try:
        return pipeline.run(req.target_url, req.scope)
    except ScopeError as exc:
        # Out-of-scope target: refuse clearly (safety feature, not a crash).
        raise HTTPException(status_code=400, detail=f"Out of scope: {exc}")
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Scan failed: {exc}")


def _scan_dir(scan_id: str) -> Path:
    d = pipeline.data_root() / scan_id
    if not d.exists():
        raise HTTPException(status_code=404, detail=f"Unknown scan_id '{scan_id}'")
    return d


@router.get("/report/{scan_id}")
def get_report_pdf(scan_id: str):
    pdf = _scan_dir(scan_id) / "report.pdf"
    if not pdf.exists():
        raise HTTPException(status_code=404, detail="PDF report not found")
    return FileResponse(str(pdf), media_type="application/pdf",
                        filename=f"kavach-attack-{scan_id}.pdf")


@router.get("/report/{scan_id}/markdown")
def get_report_md(scan_id: str):
    md = _scan_dir(scan_id) / "report.md"
    if not md.exists():
        raise HTTPException(status_code=404, detail="Markdown report not found")
    return FileResponse(str(md), media_type="text/markdown",
                        filename=f"kavach-attack-{scan_id}.md")


@router.get("/result/{scan_id}")
def get_result(scan_id: str):
    result = _scan_dir(scan_id) / "result.json"
    if not result.exists():
        raise HTTPException(status_code=404, detail="result.json not found")
    return json.loads(result.read_text(encoding="utf-8"))
