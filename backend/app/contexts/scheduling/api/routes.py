"""Scheduling routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.contexts.identity_access.api.deps import require_role
from app.contexts.identity_access.domain.models import GlobalRole, UserContext
from app.contexts.scheduling.application.service import ScheduleService
from app.contexts.scheduling.domain.models import MaintenanceWindow, Schedule, ScheduleKind

router = APIRouter(prefix="/schedules", tags=["scheduling"])


@router.get("", response_model=list[Schedule])
def list_schedules() -> list[Schedule]:
    return ScheduleService().list_all()


class ScheduleRequest(BaseModel):
    name: str
    workflow_id: str
    inputs: dict[str, object] = Field(default_factory=dict)
    kind: ScheduleKind = ScheduleKind.INTERVAL
    interval_seconds: int = 3600
    daily_time: str = "02:00"
    window: MaintenanceWindow | None = None
    enabled: bool = True


@router.post("", response_model=Schedule)
def create_schedule(
    body: ScheduleRequest, _eng: UserContext = Depends(require_role(GlobalRole.ENGINEER))
) -> Schedule:
    return ScheduleService().create(**body.model_dump())


@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: str, _eng: UserContext = Depends(require_role(GlobalRole.ENGINEER))
) -> dict[str, str]:
    ScheduleService().delete(schedule_id)
    return {"status": "deleted"}


class RunNowResponse(BaseModel):
    run_id: str


@router.post("/{schedule_id}/run-now", response_model=RunNowResponse)
async def run_now(
    schedule_id: str, _eng: UserContext = Depends(require_role(GlobalRole.ENGINEER))
) -> RunNowResponse:
    return RunNowResponse(run_id=await ScheduleService().trigger(schedule_id))
