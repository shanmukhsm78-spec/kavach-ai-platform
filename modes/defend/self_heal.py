"""Self-heal loop for Defend mode.

Whenever a red-team attack *bypasses* the firewall (expected block, got allow),
we append its payload to ``data/defend/learned.jsonl``. The detector engine
treats those payloads as new signatures, so the *same* attack is blocked on
the next run.

Viva demo:
  1. run red-team          -> detection_rate = X  (some stealth bypasses)
  2. self-heal             -> N new signatures learned
  3. run red-team again    -> detection_rate = Y  (Y > X)
"""
from __future__ import annotations

from typing import Iterable, Optional

from . import store
from .firewall import Firewall, reset_firewall


def ingest_bypasses(payloads: Iterable[str],
                    meta: Optional[dict] = None) -> dict:
    """Persist bypassed payloads and reload the live firewall's signatures."""
    payloads = [p for p in payloads if (p or "").strip()]
    added = store.append_learned(payloads, meta=meta or {"source": "self_heal"})
    # Refresh the process-wide firewall so subsequent inspects see new sigs.
    fw = reset_firewall()
    loaded = len(fw.engine.learned)
    return {
        "added": added,
        "learned_total": loaded,
        "payloads_submitted": len(payloads),
    }


def heal_from_redteam_summary(summary: dict) -> dict:
    """Convenience: pull bypass payloads out of a run_redteam() summary."""
    payloads = summary.get("_bypass_payloads") or []
    # Fall back to previews if the private key was stripped (e.g. reloaded JSON).
    if not payloads:
        for o in summary.get("outcomes", []):
            if o.get("bypassed") and o.get("payload_preview"):
                payloads.append(o["payload_preview"])
    result = ingest_bypasses(
        payloads,
        meta={"source": "self_heal", "from_run": summary.get("run_id")},
    )
    result["from_run"] = summary.get("run_id")
    return result
