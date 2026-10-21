"""Shared data structures for Attack mode.

Keeping these in one place means every stage (Recon, Scanner, Exploit,
Reporter) speaks the same language. Everything is a plain ``dataclass`` so it
is easy to serialise to JSON for the API and easy to read in a viva.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


# Qualitative severity ladder (CVSS-ish). Numbers are only used for sorting
# the report so the scariest issues float to the top.
SEVERITY_ORDER = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1,
    "Info": 0,
}


@dataclass
class Finding:
    """A single vulnerability / weakness discovered by the Scanner."""

    check_id: str                 # stable id, e.g. "missing_security_headers"
    title: str                    # human friendly title
    severity: str                 # one of SEVERITY_ORDER keys
    description: str              # what the issue is
    evidence: str                 # concrete proof we observed
    location: str                # URL / endpoint where it was found
    remediation: str             # how to fix it
    mitre: dict[str, str] = field(default_factory=dict)  # {id, name, tactic}
    cvss_qualitative: str = ""    # e.g. "High (7.4)"
    exploit_proof: str = ""      # filled in by the Exploit stage (safe PoC)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReconResult:
    """Everything the Recon stage learned about the target."""

    target_url: str
    status_code: int = 0
    server_header: str = ""
    powered_by: str = ""
    detected_tech: list[str] = field(default_factory=list)
    response_headers: dict[str, str] = field(default_factory=dict)
    routes: list[str] = field(default_factory=list)
    forms: list[dict[str, Any]] = field(default_factory=list)
    title: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
