"""Shared data structures for Defend mode (Sentinel).

Plain dataclasses so every stage (firewall, red-team, self-heal, API) speaks
the same language and everything serialises cleanly to JSON for the dashboard
and for viva demos.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional


# Channels the firewall inspects. Matching the viva story:
#   prompt    -> what the user types
#   document  -> retrieved docs / tool outputs fed into the agent
#   tool_call -> what the agent is about to do
Channel = Literal["prompt", "document", "tool_call"]

# Three possible decisions. SANITIZE means "allow a cleaned version".
Verdict = Literal["allow", "sanitize", "block"]


@dataclass
class InspectionResult:
    """What the firewall decided about one piece of content."""

    channel: str
    verdict: str                    # allow | sanitize | block
    risk_score: float               # 0.0 (safe) .. 1.0 (definitely attack)
    reasons: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)  # e.g. prompt_injection
    sanitized: str = ""             # cleaned content (equals original if allow)
    original: str = ""              # original content (truncated for storage)
    engine: str = "rules"           # "rules" | "llm" | "rules+llm"
    matched_signatures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ToolCall:
    """A proposed tool invocation from the protected agent."""

    name: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def render(self) -> str:
        """Flat string form used by signature matching."""
        import json
        return f"{self.name}({json.dumps(self.arguments, sort_keys=True)})"


@dataclass
class DefendEvent:
    """One timeline entry persisted under data/defend/events.jsonl."""

    event_id: str
    ts: str
    channel: str
    verdict: str
    risk_score: float
    reasons: list[str]
    categories: list[str]
    preview: str                    # short snippet of the content
    source: str = "inspect"         # inspect | redteam | protected_agent
    attack_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AttackCase:
    """One red-team attack case (seeded corpus + optional LLM variants)."""

    attack_id: str
    name: str
    channel: str                    # prompt | document | tool_call
    payload: str
    expected: str                   # "block" | "sanitize" (what a good firewall does)
    category: str                   # prompt_injection | jailbreak | exfil | dangerous_tool
    tags: list[str] = field(default_factory=list)
    # Optional tool_call structured form (used when channel == "tool_call")
    tool_name: Optional[str] = None
    tool_args: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AttackOutcome:
    """Result of running one AttackCase through the firewall."""

    attack_id: str
    name: str
    channel: str
    category: str
    expected: str
    verdict: str
    risk_score: float
    reasons: list[str]
    bypassed: bool                  # True if expected block/sanitize but got allow
    payload_preview: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
