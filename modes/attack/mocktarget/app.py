"""Deliberately-vulnerable FastAPI app (test fixture for Attack mode).

Each route below models a classic web weakness so the Scanner's checks have a
realistic target offline. Do not copy these patterns into real code -- they
are anti-examples on purpose.
"""
from __future__ import annotations

import socket
import threading
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse


def create_app() -> FastAPI:
    app = FastAPI(title="VulnShop (test target)")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        # VULN: reflects the raw ?q= value with no encoding -> reflected XSS.
        q = request.query_params.get("q", "")
        # VULN: no security headers are set anywhere in this app.
        return f"""<!doctype html><html><head><title>VulnShop</title></head>
        <body>
          <h1>VulnShop</h1>
          <p>Powered by Express 4.17.1</p>
          <form action="/search" method="GET"><input name="q"></form>
          <a href="/login">Login</a> <a href="/admin">Admin</a>
          <p>You searched for: {q}</p>
        </body></html>"""

    @app.get("/search", response_class=HTMLResponse)
    def search(request: Request):
        # VULN: error-based SQL injection leak on ?id=' and reflected ?q=.
        q = request.query_params.get("q", "")
        _id = request.query_params.get("id")
        if _id is not None and "'" in _id:
            return HTMLResponse(
                "You have an error in your SQL syntax; check the manual that "
                f"corresponds to your MySQL server version near '{_id}'",
                status_code=500,
            )
        return f"<html><body>Results for: {q}</body></html>"

    @app.get("/admin", response_class=HTMLResponse)
    def admin():
        # VULN: admin dashboard with no authentication.
        return "<html><body><h1>Admin Dashboard</h1>Welcome, admin.</body></html>"

    @app.get("/.env", response_class=PlainTextResponse)
    def dotenv():
        # VULN: secrets file served publicly.
        return "DB_PASSWORD=supersecret\nAPI_KEY=sk-test-123\nSECRET=hunter2\n"

    @app.get("/uploads/", response_class=HTMLResponse)
    def uploads():
        # VULN: directory listing enabled.
        return "<html><body><h1>Index of /uploads/</h1><a href='a.txt'>a.txt</a></body></html>"

    @app.get("/login", response_class=HTMLResponse)
    def login():
        resp = HTMLResponse(
            "<html><body><form method='POST' action='/login'>"
            "<input name='user'><input name='pass' type='password'></form></body></html>")
        # VULN: session cookie without HttpOnly/Secure/SameSite.
        resp.set_cookie("session", "abc123")
        return resp

    return app


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def run_in_thread(port: int | None = None) -> tuple[str, "uvicorn.Server"]:
    """Start the mock target on 127.0.0.1 in a background thread.

    Returns (base_url, server). Call ``server.should_exit = True`` to stop.
    """
    port = port or _free_port()
    config = uvicorn.Config(create_app(), host="127.0.0.1", port=port,
                            log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    # Wait until the server is actually accepting connections.
    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.1)
    return base, server


if __name__ == "__main__":
    # Manual run: python -m modes.attack.mocktarget.app
    uvicorn.run(create_app(), host="127.0.0.1", port=8081)
