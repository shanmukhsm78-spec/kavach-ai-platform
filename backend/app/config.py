"""Central configuration, loaded from environment (.env)."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Kavach AI Platform"
    environment: str = "development"

    # --- LLM provider (OpenAI-compatible) ---
    # Default points at a local model server (e.g. Ollama / LM Studio / vLLM).
    # Set LLM_PROVIDER=openai + LLM_API_KEY to use a hosted endpoint.
    llm_provider: str = "local"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "not-needed-for-local"
    llm_model: str = "llama3.1:8b"

    # CORS for the Next.js dashboard
    frontend_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
