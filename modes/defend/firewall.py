"""Sentinel firewall — the heart of Defend mode.

Sits in front of a protected LLM agent and inspects three channels in real
time:

  * prompt     — what the user typed
  * document   — retrieved docs / tool outputs about to be fed to the model
  * tool_call  — what the agent is about to do

For each, it returns ALLOW / SANITIZE / BLOCK with a reason and a risk score.
The detector engine is layered (rules → learned signatures → optional LLM
judge); see detectors.py. Persistence of every decision goes through store.py
so the dashboard timeline stays in sync.
"""
from __future__ import annotations

import datetime as _dt
import uuid
from typing import Any, Optional, Union

from . import store
from .detectors import DetectorEngine
from .models import DefendEvent, InspectionResult, ToolCall


class Firewall:
    """Stateful firewall. One instance is shared by the API for a process."""

    def __init__(self, load_learned: bool = True):
        learned = store.learned_payloads() if load_learned else []
        self.engine = DetectorEngine(learned_signatures=learned)

    def reload_learned(self) -> int:
        """Re-read learned.jsonl into the detector (after self-heal)."""
        payloads = store.learned_payloads()
        # Replace, don't just append — keeps the engine in sync with the file.
        self.engine.learned = set()
        return self.engine.add_learned(payloads)

    def inspect(
        self,
        content: str = "",
        channel: str = "prompt",
        tool_name: Optional[str] = None,
        tool_args: Optional[dict[str, Any]] = None,
        source: str = "inspect",
        attack_id: Optional[str] = None,
        persist: bool = True,
    ) -> InspectionResult:
        """Inspect one item. ``channel='tool_call'`` uses tool_name/tool_args
        when provided; otherwise ``content`` is treated as a rendered call.
        """
        channel = (channel or "prompt").lower()
        if channel not in ("prompt", "document", "tool_call"):
            channel = "prompt"

        if channel == "tool_call" and tool_name:
            result = self.engine.inspect_tool_call(
                ToolCall(name=tool_name, arguments=tool_args or {})
            )
        elif channel == "tool_call":
            # Fallback: parse "name({...})" loosely, else treat as text.
            result = self.engine.inspect_text(content or "", channel="tool_call")
        else:
            result = self.engine.inspect_text(content or "", channel=channel)

        if persist:
            self._persist(result, source=source, attack_id=attack_id)
        return result

    def _persist(self, result: InspectionResult, source: str,
                 attack_id: Optional[str]) -> None:
        event = DefendEvent(
            event_id=_dt.datetime.now().strftime("%Y%m%d%H%M%S-") + uuid.uuid4().hex[:6],
            ts=_dt.datetime.now().isoformat(timespec="seconds"),
            channel=result.channel,
            verdict=result.verdict,
            risk_score=result.risk_score,
            reasons=result.reasons,
            categories=result.categories,
            preview=(result.original or "")[:180],
            source=source,
            attack_id=attack_id,
        )
        store.append_event(event.to_dict())


# Module-level singleton used by the API routers. Tests construct their own.
_FIREWALL: Optional[Firewall] = None


def get_firewall() -> Firewall:
    global _FIREWALL
    if _FIREWALL is None:
        store.ensure_layout()
        _FIREWALL = Firewall(load_learned=True)
    return _FIREWALL


def reset_firewall() -> Firewall:
    """Drop the singleton (used by tests / after self-heal reload)."""
    global _FIREWALL
    _FIREWALL = Firewall(load_learned=True)
    return _FIREWALL


# Back-compat helpers matching the original stub's public surface.
CHANNELS = ["prompt", "document", "tool_call"]


def inspect(content: str, channel: str = "prompt") -> dict:
    """Module-level convenience wrapper (used by older callers / stubs)."""
    return get_firewall().inspect(content, channel=channel).to_dict()
