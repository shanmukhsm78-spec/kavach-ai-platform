"""A small, hardcoded MITRE ATT&CK mapping table.

Each Scanner check id maps to the ATT&CK technique that best describes how a
real attacker would abuse that weakness. We deliberately keep this small and
auditable (no external API) so it runs offline and is easy to defend in a
viva. Technique names/ids are from the MITRE ATT&CK Enterprise matrix.
"""
from __future__ import annotations

# check_id -> {id, name, tactic}
MITRE_MAP: dict[str, dict[str, str]] = {
    "missing_security_headers": {
        "id": "T1189",
        "name": "Drive-by Compromise",
        "tactic": "Initial Access",
    },
    "reflected_xss": {
        "id": "T1059.007",
        "name": "Command and Scripting Interpreter: JavaScript",
        "tactic": "Execution",
    },
    "sqli_error_based": {
        "id": "T1190",
        "name": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
    },
    "directory_listing": {
        "id": "T1083",
        "name": "File and Directory Discovery",
        "tactic": "Discovery",
    },
    "exposed_sensitive_endpoint": {
        "id": "T1552.001",
        "name": "Unsecured Credentials: Credentials In Files",
        "tactic": "Credential Access",
    },
    "default_weak_config": {
        "id": "T1078.001",
        "name": "Valid Accounts: Default Accounts",
        "tactic": "Defense Evasion",
    },
    "verbose_server_banner": {
        "id": "T1592.002",
        "name": "Gather Victim Host Information: Software",
        "tactic": "Reconnaissance",
    },
    "cookie_without_flags": {
        "id": "T1539",
        "name": "Steal Web Session Cookie",
        "tactic": "Credential Access",
    },
}

_UNKNOWN = {"id": "T0000", "name": "Unmapped Technique", "tactic": "N/A"}


def map_check(check_id: str) -> dict[str, str]:
    """Return the ATT&CK technique dict for a check id (never raises)."""
    return dict(MITRE_MAP.get(check_id, _UNKNOWN))
