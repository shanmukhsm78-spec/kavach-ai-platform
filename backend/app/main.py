"""Kavach AI Platform - FastAPI entrypoint.

Exposes one backend for all three modes (Attack / Defend / Protect),
all sharing the agent core in ../agents.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import attack, defend, protect

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Self-defending AI security platform: Attack (pentester), "
    "Defend (Sentinel firewall), Protect (Kavach scam shield).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(attack.router)
app.include_router(defend.router)
app.include_router(protect.router)


@app.get("/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "0.1.0",
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
    }


@app.get("/", tags=["system"])
def root():
    return {
        "name": settings.app_name,
        "modes": ["attack", "defend", "protect"],
        "docs": "/docs",
    }
