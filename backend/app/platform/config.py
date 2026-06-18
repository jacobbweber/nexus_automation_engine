"""Application configuration (environment-driven, with safe local defaults).

No secrets are committed; all sensitive values come from the environment at runtime. Defaults
are tuned for local/simulation use so the app runs out of the box.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NEXUS_", env_file=".env", extra="ignore")

    app_name: str = "Nexus Automation Engine"
    environment: str = "local"
    version: str = "0.1.0"

    # Synchronous SQLite by default; WAL mode is applied on connect (see database.py / ADR-0004).
    database_url: str = "sqlite:///./nexus.db"

    # Auth (used from M4 onward). Dev-only default; override via NEXUS_JWT_SECRET in real use.
    jwt_secret: str = "dev-only-not-a-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60

    # CORS for the local Vite dev server.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # When true, connectors run in simulation mode (the only supported mode pre-1.0).
    simulation_mode: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
