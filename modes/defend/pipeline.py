"""Defend mode orchestration.

Three public entry points used by the API and by tests:

  * inspect_one(...)              — single prompt/doc/tool_call check
  * run_redteam_batch(...)        — one red-team pass
  * run_self_heal_demo(...)       — red-team → heal → red-team (the viva demo)

Everything is deterministic with KAVACH_LLM=off.
"""
from __future__ import annotations

from typing import Any, Optional

from . import redteam, self_heal, store
from .firewall import Firewall, get_firewall, reset_firewall
from .protected_agent import run_indirect_injection_demo


def inspect_one(
    content: str = "",
    channel: str = "prompt",
    tool_name: Optional[str] = None,
    tool_args: Optional[dict[str, Any]] = None,
    firewall: Optional[Firewall] = None,
) -> dict:
    fw = firewall or get_firewall()
    result = fw.inspect(
        content=content,
        channel=channel,
        tool_name=tool_name,
        tool_args=tool_args,
        source="inspect",
    )
    return result.to_dict()


def run_redteam_batch(
    firewall: Optional[Firewall] = None,
    label: str = "redteam",
    persist: bool = True,
) -> dict:
    fw = firewall or get_firewall()
    summary = redteam.run_redteam(firewall=fw, persist=persist, label=label)
    # Strip the private helper key before returning to API callers.
    summary = dict(summary)
    summary.pop("_bypass_payloads", None)
    return summary


def run_self_heal_demo(persist: bool = True) -> dict:
    """The headline demo: measure detection before and after self-heal.

    Uses a fresh Firewall instance so the demo is self-contained, but still
    writes through the store so the dashboard can show the numbers.
    """
    store.ensure_layout()

    # Start from a firewall that already knows anything previously learned
    # (so repeated demos keep improving), but the *delta* of this run is what
    # we report as before/after.
    fw = Firewall(load_learned=True)

    before = redteam.run_redteam(
        firewall=fw, persist=persist, label="before_heal"
    )
    heal = self_heal.heal_from_redteam_summary(before)

    # New firewall instance picks up the just-learned signatures.
    fw_after = reset_firewall()
    after = redteam.run_redteam(
        firewall=fw_after, persist=persist, label="after_heal"
    )

    # Also run the indirect-injection chain demo once for the trace.
    chain = run_indirect_injection_demo(firewall=fw_after)

    stats = store.read_stats()
    stats["detection_before"] = before["detection_rate"]
    stats["detection_after"] = after["detection_rate"]
    store.write_stats(stats)

    return {
        "mode": "defend",
        "demo": "self_heal",
        "before": {
            "run_id": before["run_id"],
            "detection_rate": before["detection_rate"],
            "bypass_rate": before["bypass_rate"],
            "bypasses": before["bypasses"],
            "total": before["total"],
            "attack_total": before["attack_total"],
        },
        "heal": heal,
        "after": {
            "run_id": after["run_id"],
            "detection_rate": after["detection_rate"],
            "bypass_rate": after["bypass_rate"],
            "bypasses": after["bypasses"],
            "total": after["total"],
            "attack_total": after["attack_total"],
        },
        "improvement": {
            "detection_delta": round(
                after["detection_rate"] - before["detection_rate"], 4
            ),
            "bypass_delta": round(
                before["bypass_rate"] - after["bypass_rate"], 4
            ),
        },
        "indirect_injection_chain": {
            "status": chain["status"],
            "final_verdict": chain["final_verdict"],
            "final_reasons": chain["final_reasons"],
            "executed_dangerous": chain["executed_dangerous"],
        },
        # Full outcome lists kept for the API / tests that want them.
        "before_outcomes": before["outcomes"],
        "after_outcomes": after["outcomes"],
    }
