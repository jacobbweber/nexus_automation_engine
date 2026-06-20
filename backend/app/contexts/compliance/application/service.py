"""ComplianceSweepService — drift-sweep published workflows, snapshot posture, raise incidents.

Read-only (compliance mode never mutates). Idempotent on incidents: a workflow already having an
open compliance incident is not re-raised (the capture hook de-dupes per open source).
"""

from __future__ import annotations

from app.contexts.compliance.domain.models import DriftedItem, PostureSnapshot
from app.contexts.compliance.infrastructure.repository import PostureRepository
from app.shared_kernel.ids import new_id


class ComplianceSweepService:
    def __init__(self, repository: PostureRepository | None = None) -> None:
        self.repo = repository or PostureRepository()

    def run_sweep(self) -> PostureSnapshot:
        """Evaluate every published workflow in compliance mode and snapshot estate posture."""
        from app.contexts.incident_management.application.service import capture_failure
        from app.contexts.orchestration_canvas.application.service import CanvasService
        from app.contexts.orchestration_canvas.domain.models import ReviewState

        canvas = CanvasService()
        workflows = [w for w in canvas.list_workflows() if w.review_state == ReviewState.PUBLISHED]

        evaluated = 0
        compliant = 0
        drifted = 0
        total_drift = 0
        drifted_items: list[DriftedItem] = []

        for wf in workflows:
            report = canvas.compliance(wf.id)
            evaluated += 1
            if report.drift_count > 0:
                drifted += 1
                total_drift += report.drift_count
                drifted_items.append(DriftedItem(target=wf.name, drift_count=report.drift_count))
                # raise/refresh an incident for this drifted workflow (de-duped per open source)
                capture_failure(
                    title=f"Config drift: {wf.name}",
                    source_type="compliance",
                    source_id=wf.id,
                    summary=report.summary,
                )
            else:
                compliant += 1

        drifted_items.sort(key=lambda d: d.drift_count, reverse=True)
        snapshot = PostureSnapshot(
            id=new_id("posture"),
            evaluated=evaluated,
            compliant=compliant,
            drifted=drifted,
            drift_count=total_drift,
            top_drifted=drifted_items[:5],
        )
        return self.repo.save(snapshot)

    def latest(self) -> PostureSnapshot | None:
        return self.repo.latest()

    def history(self, limit: int = 30) -> list[PostureSnapshot]:
        return self.repo.history(limit)
