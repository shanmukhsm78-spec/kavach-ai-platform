"""Attack mode orchestration: Recon -> Scanner -> Exploit -> Reporter.

This is the conductor. It validates the target is a *local lab* (safety), then
runs each stage in order, maps findings to MITRE ATT&CK (done inside the
scanner), attaches safe proofs, and writes a Markdown + PDF report plus a
findings JSON under ``data/attack/<scan_id>/``.

The multi-agent framing: each stage is a specialised "agent" with its own job
(see ``build_agents`` for the LLM-backed personas). The orchestration below is
deterministic so it runs fully offline; the LLM is used only to polish the
report prose (see reporter.py / llm_assist.py).
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import uuid
from pathlib import Path

import httpx

from agents.core import Agent
from .exploit import run_exploit
from .models import Finding, ReconResult
from .recon import run_recon
from .reporter import write_reports
from .safety import ScopeError, assert_local_target
from .scanner import run_scanner

STAGES = ["recon", "scanner", "exploit", "reporter"]

# Repo root -> default data directory (override with KAVACH_DATA_DIR).
_REPO_ROOT = Path(__file__).resolve().parents[2]


def data_root() -> Path:
    return Path(os.getenv("KAVACH_DATA_DIR", _REPO_ROOT / "data" / "attack"))


def build_agents() -> dict[str, Agent]:
    """The four specialised agent personas (LLM-backed, used for narration)."""
    return {
        "recon": Agent("recon", "You enumerate a target web app you are "
                       "authorized to test in a local lab."),
        "scanner": Agent("scanner", "You identify likely web vulnerabilities "
                         "(SQLi, XSS, misconfig) from recon data."),
        "exploit": Agent("exploit", "You safely validate findings in an "
                         "isolated lab only. Never act outside scope."),
        "reporter": Agent("reporter", "You write a professional pentest report "
                          "mapped to MITRE ATT&CK with severity and fixes."),
    }


def run(target_url: str = "http://localhost:3000", scope: str = "web",
        scan_id: str | None = None) -> dict:
    """Run a full scan against a local-lab ``target_url``.

    Returns a JSON-serialisable dict with status, findings, recon data and
    report paths. Raises ScopeError (caught by the API) for out-of-scope
    targets *before* any traffic is sent.
    """
    # --- Safety gate: refuse anything that isn't a local lab ---
    assert_local_target(target_url)  # raises ScopeError if not local

    scan_id = scan_id or _dt.datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    out_dir = data_root() / scan_id

    # One client for the whole scan: short timeouts, don't follow to new hosts.
    with httpx.Client(timeout=8.0, follow_redirects=True,
                      headers={"User-Agent": "Kavach-AttackMode/1.0 (local-lab)"}) as client:
        recon: ReconResult = run_recon(target_url, client)
        findings: list[Finding] = run_scanner(recon, client)
        findings = run_exploit(findings, client)
        reports = write_reports(out_dir, target_url, scan_id, findings)

    result = {
        "mode": "attack",
        "scan_id": scan_id,
        "target": target_url,
        "scope": scope,
        "status": "completed",
        "recon": recon.to_dict(),
        "findings": [f.to_dict() for f in findings],
        "mitre_attack": sorted({f.mitre["id"] + " " + f.mitre["name"]
                                for f in findings}),
        "summary": reports["summary"],
        "summary_engine": "llm" if reports["used_llm"] else "rule-based",
        "report": {"markdown": reports["markdown"], "pdf": reports["pdf"],
                   "dir": str(out_dir)},
    }
    # Persist the machine-readable result alongside the human reports.
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").write_text(json.dumps(result, indent=2),
                                         encoding="utf-8")
    return result


__all__ = ["run", "build_agents", "STAGES", "ScopeError", "data_root"]
