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
    jwt_secret: str = "dev-only-not-a-secret-change-me-in-prod"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60

    # CORS for the local Vite dev server.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # When true, connectors run in simulation mode (the only supported mode pre-1.0).
    simulation_mode: bool = True
    # Realistic inter-log jitter for simulation adapters. Tests disable it for speed.
    sim_jitter: bool = True
    sim_jitter_max_seconds: float = 1.8
    # Seed a lived-in job history on startup so the dashboard looks real. Tests disable it.
    seed_demo_data: bool = True
    # When set to a built frontend dist directory, the API also serves the SPA (single container).
    static_dir: str | None = None
    # Background scheduler (dispatches due schedules). Tests disable it.
    scheduler_enabled: bool = True
    scheduler_tick_seconds: float = 30.0
    # Origin-story validation: gate executions on metadata + CMDB lifecycle consistency.
    enforce_lifecycle_validation: bool = True
    # SSRF guard: allow the http_request canvas node to reach private/loopback/link-local hosts.
    http_allow_private: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
