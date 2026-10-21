"""Protect mode routes - Kavach scam shield.

POST /protect/url     -> phishing URL check            {"url": "..."}
POST /protect/sms     -> scam message check            {"text": "..."}
POST /protect/audio   -> voice-clone heuristic (multipart upload "file" OR form field "path")
GET  /protect/stats   -> counters + recent checks
GET  /protect/eval    -> sample-set accuracy (URL / SMS / voice)
GET  /protect/status  -> readiness
POST /protect/check   -> generic {kind, value} (kept for the old extension stub)
"""
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from modes.protect import DETECTORS, LANGUAGES, check as run_check, store
from modes.protect.evaluate import evaluate_all

router = APIRouter(prefix="/protect", tags=["protect"])
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ALLOWED_AUDIO_DIRS = [_REPO_ROOT / "datasets" / "voice"]   # 'path' must live here


class UrlRequest(BaseModel):
    url: str
    language: str = "en"


class SmsRequest(BaseModel):
    text: str
    language: str = "en"


class CheckRequest(BaseModel):
    kind: str = "url"  # url | sms
    value: str = ""
    language: str = "en"


def _run(kind: str, value: str, language: str) -> dict:
    try:
        result = run_check(kind, value, language)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    result["check_id"] = store.record(result)["check_id"]
    return result


@router.get("/status")
def status():
    return {"mode": "protect", "status": "ready", "detectors": DETECTORS,
            "languages": LANGUAGES, "total_checks": store.read_stats()["total"]}


@router.post("/url")
def check_url(req: UrlRequest):
    if not req.url.strip():
        raise HTTPException(400, "url is required")
    return _run("url", req.url, req.language)


@router.post("/sms")
def check_sms(req: SmsRequest):
    if not req.text.strip():
        raise HTTPException(400, "text is required")
    return _run("sms", req.text, req.language)


@router.post("/audio")
async def check_audio(file: Optional[UploadFile] = File(None),
                      path: Optional[str] = Form(None),
                      language: str = Form("en")):
    """Accept an uploaded .wav, or a path to one of the shipped sample clips."""
    if file is not None:
        if not (file.filename or "").lower().endswith(".wav"):
            raise HTTPException(400, "only .wav files are supported")
        up = store.data_root() / "uploads"
        up.mkdir(parents=True, exist_ok=True)
        target = up / f"{uuid.uuid4().hex[:8]}.wav"
        with open(target, "wb") as fh:
            shutil.copyfileobj(file.file, fh)
    elif path:
        target = (_REPO_ROOT / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
        # Safety: don't let the API read arbitrary files from the server.
        if not any(target.is_relative_to(d.resolve()) for d in _ALLOWED_AUDIO_DIRS) or not target.exists():
            raise HTTPException(400, "path must be a .wav under datasets/voice/")
    else:
        raise HTTPException(400, "upload a 'file' or give a 'path'")
    try:
        return _run("audio", str(target), language)
    except (ValueError, EOFError) as e:
        raise HTTPException(400, f"could not read wav: {e}")


@router.get("/stats")
def stats(limit: int = 20):
    return {**store.read_stats(), "recent": store.recent(limit)}


@router.get("/eval")
def evaluation():
    return evaluate_all()


@router.post("/check")
def check(req: CheckRequest):
    if req.kind not in ("url", "sms"):
        raise HTTPException(400, "kind must be url or sms (use /protect/audio for audio)")
    return _run(req.kind, req.value, req.language)
