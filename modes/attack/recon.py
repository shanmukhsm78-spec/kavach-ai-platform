"""Recon stage: learn about the target before probing it.

Fetches the home page, reads response headers to fingerprint the server/tech,
and parses the HTML for links (routes) and forms (input surface). We use only
the standard library + a small regex HTML parse so there is no heavy
dependency (no Selenium/BeautifulSoup needed).
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import httpx

from .models import ReconResult

# Common paths worth probing on a web app. Kept short + harmless (GET only).
COMMON_PATHS = [
    "/", "/robots.txt", "/sitemap.xml", "/.git/config", "/.env",
    "/admin", "/login", "/api", "/backup", "/config.json", "/server-status",
    "/uploads/", "/static/",
]

_LINK_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_FORM_RE = re.compile(r"<form\b(.*?)</form>", re.IGNORECASE | re.DOTALL)
_ACTION_RE = re.compile(r'action=["\']([^"\']*)["\']', re.IGNORECASE)
_METHOD_RE = re.compile(r'method=["\']([^"\']*)["\']', re.IGNORECASE)
_INPUT_NAME_RE = re.compile(r'<input\b[^>]*\bname=["\']([^"\']+)["\']',
                            re.IGNORECASE)


def _detect_tech(headers: dict[str, str], body: str) -> list[str]:
    """Cheap technology fingerprinting from headers + body hints."""
    tech: list[str] = []
    server = headers.get("server", "")
    powered = headers.get("x-powered-by", "")
    if server:
        tech.append(f"Server: {server}")
    if powered:
        tech.append(f"X-Powered-By: {powered}")
    lowered = body.lower()
    for name, needle in [
        ("Express", "express"), ("Flask", "flask"), ("Django", "csrfmiddlewaretoken"),
        ("Angular", "ng-version"), ("React", "react"), ("jQuery", "jquery"),
        ("OWASP Juice Shop", "juice shop"),
    ]:
        if needle in lowered:
            tech.append(name)
    return sorted(set(tech))


def _parse_forms(base_url: str, html: str) -> list[dict]:
    forms = []
    for raw in _FORM_RE.findall(html):
        action = _ACTION_RE.search(raw)
        method = _METHOD_RE.search(raw)
        inputs = _INPUT_NAME_RE.findall(raw)
        forms.append({
            "action": urljoin(base_url, action.group(1)) if action else base_url,
            "method": (method.group(1) if method else "GET").upper(),
            "inputs": inputs,
        })
    return forms


def run_recon(target_url: str, client: httpx.Client) -> ReconResult:
    """Fetch the target and enumerate routes, forms, headers, and tech."""
    result = ReconResult(target_url=target_url)
    try:
        resp = client.get(target_url)
    except httpx.HTTPError as exc:
        result.error = f"Could not reach target: {exc}"
        return result

    result.status_code = resp.status_code
    result.response_headers = {k.lower(): v for k, v in resp.headers.items()}
    result.server_header = result.response_headers.get("server", "")
    result.powered_by = result.response_headers.get("x-powered-by", "")

    body = resp.text or ""
    title = _TITLE_RE.search(body)
    result.title = title.group(1).strip() if title else ""
    result.detected_tech = _detect_tech(result.response_headers, body)
    result.forms = _parse_forms(target_url, body)

    # Collect in-scope routes: links from the page + a probe of common paths.
    base = urlparse(target_url)
    routes: set[str] = set()
    for href in _LINK_RE.findall(body):
        joined = urljoin(target_url, href)
        if urlparse(joined).netloc == base.netloc:
            routes.add(joined)
    for path in COMMON_PATHS:
        routes.add(urljoin(target_url, path))
    result.routes = sorted(routes)
    return result
