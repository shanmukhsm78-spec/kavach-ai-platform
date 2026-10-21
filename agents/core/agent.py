"""Minimal shared Agent abstraction used by all three modes.

An Agent = a role + a system prompt + optional tools. Mode-specific
pipelines (e.g. Recon/Scanner/Exploit/Reporter) compose several Agents.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

from .llm import LLMClient, get_llm


@dataclass
class Agent:
    name: str
    system_prompt: str
    tools: dict[str, Callable] = field(default_factory=dict)
    llm: LLMClient | None = None

    def __post_init__(self):
        self.llm = self.llm or get_llm()

    def run(self, user_input: str, **kwargs) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        return self.llm.chat(messages, **kwargs)
