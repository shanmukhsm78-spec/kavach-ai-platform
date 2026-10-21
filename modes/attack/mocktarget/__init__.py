"""A tiny, deliberately-vulnerable web app used ONLY for offline testing.

This lets the whole Attack pipeline be exercised without Docker / Juice Shop.
It is intentionally insecure (reflected XSS, SQL error leak, missing headers,
open admin, exposed .env, directory listing) so the Scanner has something to
find. NEVER deploy this anywhere reachable.
"""
from .app import create_app, run_in_thread

__all__ = ["create_app", "run_in_thread"]
