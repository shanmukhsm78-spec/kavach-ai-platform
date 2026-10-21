"""Persistence for Protect mode under data/protect/ (checks.jsonl + stats.json)."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def data_root() -> Path:
    env = os.getenv("KAVACH_PROTECT_DIR")
    if env:
        return Path(env)
    base = os.getenv("KAVACH_DATA_DIR")
    return Path(base) / "protect" if base else _REPO_ROOT / "data" / "protect"


def _empty_stats() -> dict:
    return {"total": 0, "by_kind": {"url": 0, "sms": 0, "audio": 0},
            "by_verdict": {"safe": 0, "suspicious": 0, "dangerous": 0}}


def read_stats() -> dict:
    p = data_root() / "stats.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            pass
    return _empty_stats()


def record(result: dict) -> dict:
    """Append one check to checks.jsonl and bump counters. Returns the event."""
    root = data_root()
    (root / "uploads").mkdir(parents=True, exist_ok=True)
    event = {"check_id": uuid.uuid4().hex[:10],
             "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "kind": result["kind"], "verdict": result["verdict"],
             "risk_score": result["risk_score"], "preview": result["input"][:120]}
    with open(root / "checks.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    s = read_stats()
    s["total"] += 1
    s["by_kind"][result["kind"]] = s["by_kind"].get(result["kind"], 0) + 1
    s["by_verdict"][result["verdict"]] += 1
    s["last_check"] = event
    (root / "stats.json").write_text(json.dumps(s, indent=2, ensure_ascii=False))
    return event


def recent(limit: int = 20) -> list[dict]:
    p = data_root() / "checks.jsonl"
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").splitlines()[-limit:]
    return [json.loads(l) for l in reversed(lines) if l.strip()]
