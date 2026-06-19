"""Scheduling domain models + pure trigger/window computation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel, Field


class ScheduleKind(StrEnum):
    INTERVAL = "interval"  # every N seconds
    DAILY = "daily"  # at a fixed HH:MM (UTC)


class MaintenanceWindow(BaseModel):
    """An allowed hour range [start_hour, end_hour) in UTC. Runs only fire inside it."""

    start_hour: int = 0
    end_hour: int = 24


class Schedule(BaseModel):
    id: str
    name: str
    workflow_id: str
    inputs: dict[str, object] = Field(default_factory=dict)
    kind: ScheduleKind = ScheduleKind.INTERVAL
    interval_seconds: int = 3600
    daily_time: str = "02:00"  # HH:MM UTC, used when kind == daily
    window: MaintenanceWindow | None = None
    enabled: bool = True
    next_run_at: datetime
    last_run_at: datetime | None = None


def in_window(when: datetime, window: MaintenanceWindow | None) -> bool:
    if window is None:
        return True
    return window.start_hour <= when.hour < window.end_hour


def compute_next_run(
    kind: ScheduleKind, *, interval_seconds: int, daily_time: str, after: datetime
) -> datetime:
    if kind == ScheduleKind.INTERVAL:
        return after + timedelta(seconds=max(1, interval_seconds))
    # daily
    hour, _, minute = daily_time.partition(":")
    target = after.replace(hour=int(hour), minute=int(minute or 0), second=0, microsecond=0)
    if target <= after:
        target = target + timedelta(days=1)
    return target


def now() -> datetime:
    return datetime.now(UTC)
