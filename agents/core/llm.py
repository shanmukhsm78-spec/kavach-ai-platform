"""Pluggable LLM provider for the shared agent core.

Uses the OpenAI-compatible API, so it works with:
  - local servers (Ollama, LM Studio, vLLM) -> LLM_PROVIDER=local
  - hosted OpenAI-compatible endpoints      -> LLM_PROVIDER=openai

Configure entirely via environment variables (see .env.example).
"""
from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    provider: str = os.getenv("LLM_PROVIDER", "local")
    base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    api_key: str = os.getenv("LLM_API_KEY", "not-needed-for-local")
    model: str = os.getenv("LLM_MODEL", "llama3.1:8b")


class LLMClient:
    """Thin wrapper so modes don't depend on a specific vendor SDK."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            # Imported lazily so the scaffold imports even before deps resolve.
            from openai import OpenAI
            self._client = OpenAI(
                base_url=self.config.base_url,
                api_key=self.config.api_key,
            )
        return self._client

    def chat(self, messages: list[dict], **kwargs) -> str:
        client = self._ensure_client()
        resp = client.chat.completions.create(
            model=self.config.model, messages=messages, **kwargs
        )
        return resp.choices[0].message.content or ""


def get_llm() -> LLMClient:
    return LLMClient()
