"""Defend mode routes — Sentinel AI-agent firewall.

POST /defend/inspect       -> inspect one prompt / document / tool_call
POST /defend/run-redteam   -> run the seeded (+ optional LLM) attack batch
POST /defend/self-heal     -> ingest bypasses (or run the full before/after demo)
POST /defend/demo-chain    -> indirect injection → dangerous tool demo
GET  /defend/stats         -> counters + last red-team summary
GET  /defend/events        -> timeline (newest first)
GET  /defend/status        -> readiness
"""
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from modes.defend import pipeline, store
from modes.defend.firewall import get_firewall, reset_firewall
from modes.defend.protected_agent import run_indirect_injection_demo
from modes.defend import self_heal as self_heal_mod

router = APIRouter(prefix="/defend", tags=["defend"])


class InspectRequest(BaseModel):
    content: str = ""
    channel: str = "prompt"  # prompt | document | tool_call
    tool_name: Optional[str] = None
    tool_args: dict[str, Any] = Field(default_factory=dict)


class SelfHealRequest(BaseModel):
    """Either pass explicit payloads, or set run_demo=True for the full loop."""
    payloads: list[str] = Field(default_factory=list)
    run_demo: bool = False


class RedteamRequest(BaseModel):
    label: str = "redteam"


@router.get("/status")
def status():
    stats = store.read_stats()
    return {
        "mode": "defend",
        "status": "ready",
        "capabilities": [
            "prompt_injection",
            "jailbreak",
            "data_exfiltration",
            "dangerous_tool",
            "red_team",
            "self_heal",
        ],
        "learned_signatures": stats.get("learned_signatures", 0),
        "events": stats.get("total", 0),
    }


@router.post("/inspect")
def inspect(req: InspectRequest):
    try:
        return pipeline.inspect_one(
            content=req.content,
            channel=req.channel,
            tool_name=req.tool_name,
            tool_args=req.tool_args,
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Inspect failed: {exc}")


@router.post("/run-redteam")
def run_redteam(req: RedteamRequest = RedteamRequest()):
    try:
        reset_firewall()
        return pipeline.run_redteam_batch(label=req.label)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Red-team failed: {exc}")


@router.post("/self-heal")
def self_heal(req: SelfHealRequest = SelfHealRequest()):
    """Ingest bypass payloads, OR run the full before/after demo.

    The dashboard's "Run self-heal demo" button sends ``{"run_demo": true}``.
    """
    try:
        if req.run_demo:
            return pipeline.run_self_heal_demo(persist=True)
        if not req.payloads:
            raise HTTPException(
                status_code=400,
                detail="Provide payloads=[] or set run_demo=true",
            )
        return self_heal_mod.ingest_bypasses(req.payloads)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Self-heal failed: {exc}")


@router.post("/demo-chain")
def demo_chain():
    """Show the indirect-injection → dangerous-tool chain being caught."""
    try:
        fw = get_firewall()
        return run_indirect_injection_demo(firewall=fw)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Demo failed: {exc}")


@router.get("/stats")
def stats():
    s = store.read_stats()
    s["mode"] = "defend"
    return s


@router.get("/events")
def events(limit: int = Query(50, ge=1, le=500)):
    ev = store.read_events(limit=limit)
    return {"mode": "defend", "count": len(ev), "events": ev}
