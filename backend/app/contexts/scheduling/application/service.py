"""ScheduleService — manage schedules and dispatch due workflow runs."""

from __future__ import annotations

import asyncio
import logging

from app.contexts.orchestration_canvas.application.service import CanvasService
from app.contexts.scheduling.domain.models import (
    MaintenanceWindow,
    Schedule,
    ScheduleKind,
    compute_next_run,
    in_window,
    now,
)
from app.contexts.scheduling.infrastructure.repository import ScheduleRepository
from app.shared_kernel.errors import NotFoundError
from app.shared_kernel.ids import new_id

log = logging.getLogger("nexus.scheduler")


class ScheduleService:
    def __init__(
        self, repository: ScheduleRepository | None = None, canvas: CanvasService | None = None
    ) -> None:
        self.repo = repository or ScheduleRepository()
        self.canvas = canvas or CanvasService()

    def create(
        self,
        *,
        name: str,
        workflow_id: str,
        inputs: dict | None = None,
        kind: ScheduleKind = ScheduleKind.INTERVAL,
        interval_seconds: int = 3600,
        daily_time: str = "02:00",
        window: MaintenanceWindow | None = None,
        enabled: bool = True,
    ) -> Schedule:
        first = compute_next_run(
            kind, interval_seconds=interval_seconds, daily_time=daily_time, after=now()
        )
        return self.repo.save(
            Schedule(
                id=new_id("sch"),
                name=name,
                workflow_id=workflow_id,
                inputs=inputs or {},
                kind=kind,
                interval_seconds=interval_seconds,
                daily_time=daily_time,
                window=window,
                enabled=enabled,
                next_run_at=first,
            )
        )

    def list_all(self) -> list[Schedule]:
        return self.repo.list_all()

    def get(self, schedule_id: str) -> Schedule:
        sched = self.repo.get(schedule_id)
        if sched is None:
            raise NotFoundError(f"Schedule {schedule_id} not found")
        return sched

    def delete(self, schedule_id: str) -> None:
        self.repo.delete(schedule_id)

    def _advance(self, sched: Schedule, *, ran: bool) -> None:
        sched.next_run_at = compute_next_run(
            sched.kind,
            interval_seconds=sched.interval_seconds,
            daily_time=sched.daily_time,
            after=now(),
        )
        if ran:
            sched.last_run_at = now()
        self.repo.save(sched)

    async def trigger(self, schedule_id: str) -> str:
        """Run a schedule's workflow now and advance its next_run_at. Returns the run id."""
        sched = self.get(schedule_id)
        run_id = self.canvas.start_run(sched.workflow_id, sched.inputs)
        self._advance(sched, ran=True)
        return run_id

    async def run_due(self) -> list[str]:
        """Dispatch all due schedules whose maintenance window currently allows it."""
        run_ids: list[str] = []
        for sched in self.repo.due(now()):
            if not in_window(now(), sched.window):
                self._advance(sched, ran=False)  # not in window — retry later
                continue
            try:
                run_ids.append(self.canvas.start_run(sched.workflow_id, sched.inputs))
                self._advance(sched, ran=True)
            except Exception as exc:  # noqa: BLE001 - one bad schedule shouldn't stop the rest
                log.warning("Schedule %s failed to dispatch: %s", sched.id, exc)
                self._advance(sched, ran=False)
        return run_ids


async def scheduler_loop(tick_seconds: float) -> None:
    """Background ticker: periodically dispatch due schedules."""
    service = ScheduleService()
    while True:
        try:
            await service.run_due()
        except Exception as exc:  # noqa: BLE001
            log.warning("Scheduler tick error: %s", exc)
        await asyncio.sleep(tick_seconds)
