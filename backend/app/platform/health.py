"""Health & metadata endpoints (platform-level, not a business context)."""

from __future__ import annotations

import time

from fastapi import APIRouter
from pydantic import BaseModel

from app.platform.config import get_settings

router = APIRouter(tags=["platform"])

# Process start, for uptime reporting (monotonic so it's immune to wall-clock changes).
_START = time.monotonic()


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str
    simulation_mode: bool


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        simulation_mode=settings.simulation_mode,
    )


class PlatformStatus(BaseModel):
    app: str
    version: str
    environment: str
    simulation_mode: bool
    scheduler_enabled: bool
    uptime_seconds: int
    db_ok: bool
    workflows: int
    jobs: int


@router.get("/platform/status", response_model=PlatformStatus)
def platform_status() -> PlatformStatus:
    """Lightweight runtime status for the platform/admin view: uptime, DB reachability, counts."""
    settings = get_settings()
    workflows = 0
    jobs = 0
    db_ok = True
    try:
        from app.contexts.execution_engine.infrastructure.repository import JobRepository
        from app.contexts.orchestration_canvas.infrastructure.repository import CanvasRepository

        workflows = CanvasRepository().count_workflows()
        jobs = JobRepository().count()
    except Exception:  # noqa: BLE001 - status must never 500; report the DB as unhealthy instead
        db_ok = False
    return PlatformStatus(
        app=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        simulation_mode=settings.simulation_mode,
        scheduler_enabled=settings.scheduler_enabled,
        uptime_seconds=int(time.monotonic() - _START),
        db_ok=db_ok,
        workflows=workflows,
        jobs=jobs,
    )
