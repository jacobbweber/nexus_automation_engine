"""Health & metadata endpoints (platform-level, not a business context)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.platform.config import get_settings

router = APIRouter(tags=["platform"])


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
