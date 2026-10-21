"""Attack mode — autonomous AI pentester (Recon → Scanner → Exploit → Reporter)."""
from .pipeline import run, build_agents, STAGES, data_root
from .safety import assert_local_target, ScopeError

__all__ = ["run", "build_agents", "STAGES", "data_root",
           "assert_local_target", "ScopeError"]
