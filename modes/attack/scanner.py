"""Scanner stage: run a set of safe, non-destructive web checks.

Every check returns zero or more ``Finding`` objects. All probes are GET-based,
read-only, and use harmless marker payloads. Nothing here writes, deletes, or
tries to gain a shell -- this is a *detector*, not a weaponised exploit.
"""
from __future__ import annotations

from urllib.parse import urljoin, urlparse, parse_qsl, urlencode, urlunparse

import httpx

from .mitre import map_check
from .models import Finding, ReconResult

# --- security headers we expect a well-configured app to send ---
EXPECTED_HEADERS = {
    "content-security-policy": "Content-Security-Policy",
    "x-frame-options": "X-Frame-Options",
    "x-content-type-options": "X-Content-Type-Options",
    "strict-transport-security": "Strict-Transport-Security",
    "referrer-policy": "Referrer-Policy",
}

# Unique markers so we can tell *our* reflected input apart from page content.
XSS_MARKER = "kv7xss"
XSS_PAYLOAD = f'"><svg/onload=alert({XSS_MARKER})>'
SQLI_PAYLOAD = "'"
SQL_ERROR_SIGNATURES = [
    "you have an error in your sql syntax",
    "warning: mysql",
    "unclosed quotation mark",
    "sqlite3.operationalerror",
    "sqlite error",
    "pg::syntaxerror",
    "psqlexception",
    "ora-00933",
    "sqlstate",
    "near \"'\": syntax error",
]
SENSITIVE_PATHS = {
    "/.env": ["secret", "password", "api_key", "key="],
    "/.git/config": ["[core]", "repositoryformatversion"],
    "/config.json": ["password", "secret", "token"],
    "/backup": ["password", "sql", "dump"],
}


def _mk(check_id: str, title: str, severity: str, cvss: str, desc: str,
        evidence: str, location: str, remediation: str) -> Finding:
    """Helper to build a Finding with its MITRE mapping attached."""
    return Finding(
        check_id=check_id, title=title, severity=severity,
        cvss_qualitative=cvss, description=desc, evidence=evidence,
        location=location, remediation=remediation, mitre=map_check(check_id),
    )


def _with_param(url: str, name: str, value: str) -> str:
    """Return ``url`` with query parameter ``name=value`` added/replaced."""
    parts = urlparse(url)
    q = dict(parse_qsl(parts.query))
    q[name] = value
    return urlunparse(parts._replace(query=urlencode(q)))


def _candidate_urls(recon: ReconResult) -> list[str]:
    """Same-origin URLs worth fuzzing with a parameter (root + routes + forms).

    We probe the home page plus a few likely dynamic endpoints and any GET
    form actions found during recon, so injectable endpoints that aren't the
    root (e.g. /search) are still covered.
    """
    base = urlparse(recon.target_url)
    urls: list[str] = [recon.target_url]
    for route in recon.routes:
        if urlparse(route).netloc == base.netloc and route not in urls:
            urls.append(route)
    for form in recon.forms:
        action = form.get("action", "")
        if action and urlparse(action).netloc == base.netloc and action not in urls:
            urls.append(action)
    # Keep it bounded so a scan stays quick.
    return urls[:15]


def check_security_headers(recon: ReconResult) -> list[Finding]:
    missing = [label for hdr, label in EXPECTED_HEADERS.items()
               if hdr not in recon.response_headers]
    if not missing:
        return []
    return [_mk(
        "missing_security_headers",
        "Missing HTTP security headers",
        "Medium", "Medium (5.3)",
        "The application does not send one or more recommended security "
        "response headers, leaving it exposed to clickjacking, MIME sniffing, "
        "and content-injection attacks.",
        "Missing header(s): " + ", ".join(missing),
        recon.target_url,
        "Add the missing headers (e.g. Content-Security-Policy, "
        "X-Frame-Options: DENY, X-Content-Type-Options: nosniff, "
        "Strict-Transport-Security, Referrer-Policy) at the app or reverse "
        "proxy layer.",
    )]


def check_server_banner(recon: ReconResult) -> list[Finding]:
    banner = recon.server_header or recon.powered_by
    if not banner:
        return []
    # Only flag if it leaks a version number (digits).
    if not any(ch.isdigit() for ch in banner):
        return []
    return [_mk(
        "verbose_server_banner",
        "Verbose server/version banner disclosure",
        "Low", "Low (3.1)",
        "Response headers disclose the exact server software and version, "
        "helping an attacker pick known exploits.",
        f"Server='{recon.server_header}' X-Powered-By='{recon.powered_by}'",
        recon.target_url,
        "Suppress or genericise Server / X-Powered-By headers.",
    )]


def check_cookie_flags(recon: ReconResult) -> list[Finding]:
    set_cookie = recon.response_headers.get("set-cookie", "")
    if not set_cookie:
        return []
    low = set_cookie.lower()
    missing = [flag for flag in ("httponly", "secure") if flag not in low]
    if not missing:
        return []
    return [_mk(
        "cookie_without_flags",
        "Session cookie missing security flags",
        "Medium", "Medium (5.4)",
        "A cookie is set without the HttpOnly and/or Secure flag, so it can be "
        "stolen via XSS or sent over plaintext HTTP.",
        f"Set-Cookie missing flag(s): {', '.join(missing)}",
        recon.target_url,
        "Set HttpOnly, Secure and SameSite on all session cookies.",
    )]


def check_reflected_xss(recon: ReconResult, client: httpx.Client) -> list[Finding]:
    # Try each candidate endpoint with a harmless marker payload on ?q=.
    for url in _candidate_urls(recon):
        probe_url = _with_param(url, "q", XSS_PAYLOAD)
        try:
            resp = client.get(probe_url)
        except httpx.HTTPError:
            continue
        if XSS_PAYLOAD in (resp.text or ""):
            return [_mk(
                "reflected_xss",
                "Reflected Cross-Site Scripting (XSS)",
                "High", "High (7.4)",
                "User-supplied input is reflected into the HTML response without "
                "encoding, allowing script execution in a victim's browser.",
                f"Payload reflected unescaped via '?q='. Marker: {XSS_MARKER}",
                probe_url,
                "Context-aware output encoding, a strict Content-Security-Policy, "
                "and input validation.",
            )]
    return []


def check_sqli(recon: ReconResult, client: httpx.Client) -> list[Finding]:
    # Probe each candidate endpoint with a single-quote on ?id=.
    for url in _candidate_urls(recon):
        probe_url = _with_param(url, "id", SQLI_PAYLOAD)
        try:
            resp = client.get(probe_url)
        except httpx.HTTPError:
            continue
        body = (resp.text or "").lower()
        hit = next((sig for sig in SQL_ERROR_SIGNATURES if sig in body), None)
        if hit:
            return [_mk(
                "sqli_error_based",
                "SQL Injection (error-based)",
                "Critical", "Critical (9.1)",
                "A single-quote probe triggers a database error, indicating input "
                "is concatenated into SQL and the app is injectable.",
                f"DB error signature observed: '{hit}' at {probe_url}",
                probe_url,
                "Use parameterised queries / prepared statements and an ORM; never "
                "build SQL by string concatenation. Disable verbose DB errors.",
            )]
    return []


def check_directory_listing(recon: ReconResult, client: httpx.Client) -> list[Finding]:
    findings = []
    for path in ("/uploads/", "/static/", "/files/", "/backup/"):
        url = urljoin(recon.target_url, path)
        try:
            resp = client.get(url)
        except httpx.HTTPError:
            continue
        if resp.status_code == 200 and "index of" in (resp.text or "").lower():
            findings.append(_mk(
                "directory_listing",
                "Directory listing enabled",
                "Medium", "Medium (5.3)",
                "The server returns an auto-generated directory index, exposing "
                "file names an attacker can harvest.",
                f"'Index of' page served at {path}",
                url,
                "Disable automatic directory indexing (e.g. 'Options -Indexes').",
            ))
    return findings


def check_sensitive_endpoints(recon: ReconResult, client: httpx.Client) -> list[Finding]:
    findings = []
    for path, needles in SENSITIVE_PATHS.items():
        url = urljoin(recon.target_url, path)
        try:
            resp = client.get(url)
        except httpx.HTTPError:
            continue
        body = (resp.text or "").lower()
        if resp.status_code == 200 and any(n in body for n in needles):
            findings.append(_mk(
                "exposed_sensitive_endpoint",
                f"Exposed sensitive file: {path}",
                "High", "High (7.5)",
                "A file that commonly contains secrets or source metadata is "
                "publicly readable.",
                f"HTTP 200 at {path} containing sensitive keywords.",
                url,
                "Block access to dotfiles/backups at the web server and remove "
                "them from the web root; rotate any leaked secrets.",
            ))
    return findings


def check_default_weak_config(recon: ReconResult, client: httpx.Client) -> list[Finding]:
    url = urljoin(recon.target_url, "/admin")
    try:
        resp = client.get(url)
    except httpx.HTTPError:
        return []
    body = (resp.text or "").lower()
    if resp.status_code == 200 and ("admin" in body or "dashboard" in body):
        return [_mk(
            "default_weak_config",
            "Admin interface reachable without authentication",
            "High", "High (8.0)",
            "An administrative endpoint is reachable and returns content "
            "without an authentication challenge.",
            f"HTTP 200 at /admin returning admin/dashboard content.",
            url,
            "Require authentication + authorisation on all admin routes, "
            "restrict by network, and change default credentials.",
        )]
    return []


def run_scanner(recon: ReconResult, client: httpx.Client) -> list[Finding]:
    """Run all checks and return the combined list of findings."""
    findings: list[Finding] = []
    findings += check_security_headers(recon)
    findings += check_server_banner(recon)
    findings += check_cookie_flags(recon)
    findings += check_reflected_xss(recon, client)
    findings += check_sqli(recon, client)
    findings += check_directory_listing(recon, client)
    findings += check_sensitive_endpoints(recon, client)
    findings += check_default_weak_config(recon, client)
    return findings
