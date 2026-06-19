"""Schedule repository (sync SQLAlchemy)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import select

from app.contexts.scheduling.domain.models import (
    MaintenanceWindow,
    Schedule,
    ScheduleKind,
)
from app.contexts.scheduling.infrastructure.orm import ScheduleRow
from app.platform.database import get_sessionmaker


def _aware(dt: datetime | None) -> datetime | None:
    # SQLite returns naive datetimes; the domain works in UTC-aware time.
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _to_schedule(r: ScheduleRow) -> Schedule:
    return Schedule(
        id=r.id,
        name=r.name,
        workflow_id=r.workflow_id,
        inputs=json.loads(r.inputs_json or "{}"),
        kind=ScheduleKind(r.kind),
        interval_seconds=r.interval_seconds,
        daily_time=r.daily_time,
        window=MaintenanceWindow(**json.loads(r.window_json)) if r.window_json else None,
        enabled=r.enabled,
        next_run_at=_aware(r.next_run_at),
        last_run_at=_aware(r.last_run_at),
    )


class ScheduleRepository:
    def save(self, sched: Schedule) -> Schedule:
        with get_sessionmaker()() as s:
            row = s.get(ScheduleRow, sched.id) or ScheduleRow(id=sched.id)
            row.name = sched.name
            row.workflow_id = sched.workflow_id
            row.inputs_json = json.dumps(sched.inputs)
            row.kind = str(sched.kind)
            row.interval_seconds = sched.interval_seconds
            row.daily_time = sched.daily_time
            row.window_json = sched.window.model_dump_json() if sched.window else None
            row.enabled = sched.enabled
            row.next_run_at = sched.next_run_at
            row.last_run_at = sched.last_run_at
            s.add(row)
            s.commit()
            s.refresh(row)
            return _to_schedule(row)

    def get(self, schedule_id: str) -> Schedule | None:
        with get_sessionmaker()() as s:
            row = s.get(ScheduleRow, schedule_id)
            return _to_schedule(row) if row else None

    def list_all(self) -> list[Schedule]:
        with get_sessionmaker()() as s:
            rows = s.execute(select(ScheduleRow).order_by(ScheduleRow.next_run_at)).scalars().all()
            return [_to_schedule(r) for r in rows]

    def delete(self, schedule_id: str) -> None:
        with get_sessionmaker()() as s:
            row = s.get(ScheduleRow, schedule_id)
            if row:
                s.delete(row)
                s.commit()

    def due(self, as_of: datetime) -> list[Schedule]:
        stmt = select(ScheduleRow).where(
            ScheduleRow.enabled.is_(True), ScheduleRow.next_run_at <= as_of
        )
        with get_sessionmaker()() as s:
            return [_to_schedule(r) for r in s.execute(stmt).scalars().all()]
