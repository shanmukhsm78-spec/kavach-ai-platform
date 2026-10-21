"""Persistence for Defend mode under data/defend/.

Layout:
  data/defend/
    events.jsonl     - timeline of every inspect / red-team decision
    learned.jsonl    - payloads that bypassed the firewall (self-heal input)
    stats.json       - running counters + last red-team summary
    redteam/         - per-run JSON dumps (before / after self-heal)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Optional


_REPO_ROOT = Path(__file__).resolve().parents[2]


def data_root() -> Path:
    """Resolve the Defend data directory (overridable for tests)."""
    env = os.getenv("KAVACH_DEFEND_DIR")
    if env:
        return Path(env)
    base = os.getenv("KAVACH_DATA_DIR")
    if base:
        return Path(base) / "defend"
    return _REPO_ROOT / "data" / "defend"


def ensure_layout() -> Path:
    root = data_root()
    (root / "redteam").mkdir(parents=True, exist_ok=True)
    for name in ("events.jsonl", "learned.jsonl"):
        p = root / name
        if not p.exists():
            p.touch()
    stats = root / "stats.json"
    if not stats.exists():
        stats.write_text(json.dumps(_empty_stats(), indent=2), encoding="utf-8")
    return root


def _empty_stats() -> dict[str, Any]:
    return {
        "allowed": 0,
        "sanitized": 0,
        "blocked": 0,
        "total": 0,
        "learned_signatures": 0,
        "last_redteam": None,
        "detection_before": None,
        "detection_after": None,
    }


def append_event(event: dict[str, Any]) -> None:
    root = ensure_layout()
    with (root / "events.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    stats = read_stats()
    verdict = event.get("verdict", "allow")
    if verdict == "block":
        stats["blocked"] = int(stats.get("blocked", 0)) + 1
    elif verdict == "sanitize":
        stats["sanitized"] = int(stats.get("sanitized", 0)) + 1
    else:
        stats["allowed"] = int(stats.get("allowed", 0)) + 1
    stats["total"] = int(stats.get("total", 0)) + 1
    write_stats(stats)


def read_events(limit: int = 100) -> list[dict[str, Any]]:
    root = ensure_layout()
    path = root / "events.jsonl"
    if not path.exists() or path.stat().st_size == 0:
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    out.reverse()  # newest first for the timeline UI
    return out


def append_learned(payloads: Iterable[str], meta: Optional[dict] = None) -> int:
    """Append bypassed payloads to learned.jsonl. Returns how many were new."""
    root = ensure_layout()
    existing = {e["payload"].lower() for e in read_learned() if e.get("payload")}
    added = 0
    with (root / "learned.jsonl").open("a", encoding="utf-8") as fh:
        for p in payloads:
            p = (p or "").strip()
            if not p or p.lower() in existing:
                continue
            rec = {"payload": p, **(meta or {})}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            existing.add(p.lower())
            added += 1
    if added:
        stats = read_stats()
        stats["learned_signatures"] = len(existing)
        write_stats(stats)
    return added


def read_learned() -> list[dict[str, Any]]:
    root = ensure_layout()
    path = root / "learned.jsonl"
    if not path.exists() or path.stat().st_size == 0:
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def learned_payloads() -> list[str]:
    return [e["payload"] for e in read_learned() if e.get("payload")]


def read_stats() -> dict[str, Any]:
    root = ensure_layout()
    path = root / "stats.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return _empty_stats()


def write_stats(stats: dict[str, Any]) -> None:
    root = ensure_layout()
    (root / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")


def save_redteam_run(run_id: str, payload: dict[str, Any]) -> Path:
    root = ensure_layout()
    path = root / "redteam" / f"{run_id}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def reset_for_tests(tmp_dir: Path) -> None:
    """Point the store at a temp directory (used by pytest)."""
    os.environ["KAVACH_DEFEND_DIR"] = str(tmp_dir)
    ensure_layout()
