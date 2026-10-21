"""Defend mode — Sentinel AI-agent firewall (inspect → red-team → self-heal)."""
from .firewall import Firewall, get_firewall, inspect, CHANNELS
from .pipeline import inspect_one, run_redteam_batch, run_self_heal_demo
from . import store

__all__ = [
    "Firewall",
    "get_firewall",
    "inspect",
    "CHANNELS",
    "inspect_one",
    "run_redteam_batch",
    "run_self_heal_demo",
    "store",
]
