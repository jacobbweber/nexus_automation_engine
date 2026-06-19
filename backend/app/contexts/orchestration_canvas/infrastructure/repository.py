"""Workflow / run / step repository (sync SQLAlchemy)."""

from __future__ import annotations

import json

from sqlalchemy import delete, func, select

from app.contexts.orchestration_canvas.domain.models import (
    ReviewRecord,
    ReviewState,
    RunStatus,
    StepStatus,
    Workflow,
    WorkflowGraph,
    WorkflowRun,
    WorkflowStep,
    WorkflowVersion,
)
from app.contexts.orchestration_canvas.infrastructure.orm import (
    WorkflowReviewRow,
    WorkflowRow,
    WorkflowRunRow,
    WorkflowStepRow,
    WorkflowVersionRow,
)
from app.platform.database import get_sessionmaker


def _to_workflow(row: WorkflowRow) -> Workflow:
    return Workflow(
        id=row.id,
        name=row.name,
        description=row.description,
        graph=WorkflowGraph(**json.loads(row.graph_json or "{}")),
        review_state=ReviewState(row.review_state),
        submitted_by=row.submitted_by,
        reviewed_by=row.reviewed_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class CanvasRepository:
    # --- workflows ---------------------------------------------------------------------------

    def save_workflow(self, workflow: Workflow) -> Workflow:
        # Graph edits do NOT change review state; that flows through set_review_state().
        with get_sessionmaker()() as session:
            row = session.get(WorkflowRow, workflow.id)
            if row is None:
                row = WorkflowRow(
                    id=workflow.id, created_at=workflow.created_at, review_state="draft"
                )
                session.add(row)
            row.name = workflow.name
            row.description = workflow.description
            row.graph_json = workflow.graph.model_dump_json()
            row.updated_at = workflow.updated_at
            session.commit()
            session.refresh(row)
            return _to_workflow(row)

    def set_review_state(
        self,
        workflow_id: str,
        state: ReviewState,
        *,
        submitted_by: str | None = None,
        reviewed_by: str | None = None,
    ) -> None:
        with get_sessionmaker()() as session:
            row = session.get(WorkflowRow, workflow_id)
            if row is None:
                return
            row.review_state = str(state)
            if submitted_by is not None:
                row.submitted_by = submitted_by
            if reviewed_by is not None:
                row.reviewed_by = reviewed_by
            session.commit()

    def save_review(self, review: ReviewRecord) -> None:
        with get_sessionmaker()() as session:
            session.add(
                WorkflowReviewRow(
                    id=review.id,
                    workflow_id=review.workflow_id,
                    decision=review.decision,
                    actor=review.actor,
                    comment=review.comment,
                    created_at=review.created_at,
                )
            )
            session.commit()

    def list_reviews(self, workflow_id: str) -> list[ReviewRecord]:
        stmt = (
            select(WorkflowReviewRow)
            .where(WorkflowReviewRow.workflow_id == workflow_id)
            .order_by(WorkflowReviewRow.created_at)
        )
        with get_sessionmaker()() as session:
            return [
                ReviewRecord(
                    id=r.id,
                    workflow_id=r.workflow_id,
                    decision=r.decision,
                    actor=r.actor,
                    comment=r.comment,
                    created_at=r.created_at,
                )
                for r in session.execute(stmt).scalars().all()
            ]

    def list_pending_reviews(self) -> list[Workflow]:
        stmt = select(WorkflowRow).where(
            WorkflowRow.review_state.in_(["submitted", "in_review", "changes_requested"])
        )
        with get_sessionmaker()() as session:
            return [_to_workflow(r) for r in session.execute(stmt).scalars().all()]

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        with get_sessionmaker()() as session:
            row = session.get(WorkflowRow, workflow_id)
            return _to_workflow(row) if row else None

    def list_workflows(self) -> list[Workflow]:
        with get_sessionmaker()() as session:
            rows = session.execute(select(WorkflowRow).order_by(WorkflowRow.name)).scalars().all()
            return [_to_workflow(r) for r in rows]

    def delete_workflow(self, workflow_id: str) -> None:
        with get_sessionmaker()() as session:
            row = session.get(WorkflowRow, workflow_id)
            if row:
                session.delete(row)
                session.commit()

    def count_workflows(self) -> int:
        with get_sessionmaker()() as session:
            return int(session.execute(select(func.count(WorkflowRow.id))).scalar() or 0)

    # --- versions ----------------------------------------------------------------------------

    def save_version(self, version: WorkflowVersion) -> None:
        with get_sessionmaker()() as session:
            session.add(
                WorkflowVersionRow(
                    version_id=version.version_id,
                    workflow_id=version.workflow_id,
                    graph_json=version.graph.model_dump_json(),
                    description=version.description,
                    created_at=version.created_at,
                )
            )
            session.commit()

    def list_versions(self, workflow_id: str) -> list[WorkflowVersion]:
        stmt = (
            select(WorkflowVersionRow)
            .where(WorkflowVersionRow.workflow_id == workflow_id)
            .order_by(WorkflowVersionRow.created_at.desc())
        )
        with get_sessionmaker()() as session:
            return [
                WorkflowVersion(
                    version_id=r.version_id,
                    workflow_id=r.workflow_id,
                    graph=WorkflowGraph(**json.loads(r.graph_json or "{}")),
                    description=r.description,
                    created_at=r.created_at,
                )
                for r in session.execute(stmt).scalars().all()
            ]

    # --- runs & steps ------------------------------------------------------------------------

    def save_run(self, run: WorkflowRun) -> None:
        with get_sessionmaker()() as session:
            row = session.get(WorkflowRunRow, run.run_id)
            if row is None:
                row = WorkflowRunRow(run_id=run.run_id)
                session.add(row)
            row.workflow_id = run.workflow_id
            row.status = str(run.status)
            row.started_at = run.started_at
            row.completed_at = run.completed_at
            row.inputs_json = json.dumps(run.inputs)
            row.outputs_json = json.dumps(run.outputs) if run.outputs else None
            row.error_message = run.error_message
            session.commit()

    def save_step(self, step: WorkflowStep) -> None:
        with get_sessionmaker()() as session:
            row = session.get(WorkflowStepRow, step.step_id)
            if row is None:
                row = WorkflowStepRow(step_id=step.step_id)
                session.add(row)
            row.run_id = step.run_id
            row.node_id = step.node_id
            row.node_type = step.node_type
            row.status = str(step.status)
            row.started_at = step.started_at
            row.completed_at = step.completed_at
            row.inputs_json = json.dumps(step.inputs) if step.inputs else None
            row.outputs_json = json.dumps(step.outputs) if step.outputs else None
            row.error_message = step.error_message
            row.retry_count = step.retry_count
            session.commit()

    def get_run(self, run_id: str) -> WorkflowRun | None:
        with get_sessionmaker()() as session:
            row = session.get(WorkflowRunRow, run_id)
            if row is None:
                return None
            steps = (
                session.execute(
                    select(WorkflowStepRow)
                    .where(WorkflowStepRow.run_id == run_id)
                    .order_by(WorkflowStepRow.started_at)
                )
                .scalars()
                .all()
            )
            return WorkflowRun(
                run_id=row.run_id,
                workflow_id=row.workflow_id,
                status=RunStatus(row.status),
                started_at=row.started_at,
                completed_at=row.completed_at,
                inputs=json.loads(row.inputs_json or "{}"),
                outputs=json.loads(row.outputs_json) if row.outputs_json else {},
                error_message=row.error_message,
                steps=[
                    WorkflowStep(
                        step_id=s.step_id,
                        run_id=s.run_id,
                        node_id=s.node_id,
                        node_type=s.node_type,
                        status=StepStatus(s.status),
                        started_at=s.started_at,
                        completed_at=s.completed_at,
                        inputs=json.loads(s.inputs_json) if s.inputs_json else {},
                        outputs=json.loads(s.outputs_json) if s.outputs_json else {},
                        error_message=s.error_message,
                        retry_count=s.retry_count,
                    )
                    for s in steps
                ],
            )

    def list_runs(self, workflow_id: str, limit: int = 50) -> list[WorkflowRun]:
        stmt = (
            select(WorkflowRunRow)
            .where(WorkflowRunRow.workflow_id == workflow_id)
            .order_by(WorkflowRunRow.started_at.desc())
            .limit(limit)
        )
        with get_sessionmaker()() as session:
            rows = session.execute(stmt).scalars().all()
            return [
                WorkflowRun(
                    run_id=r.run_id,
                    workflow_id=r.workflow_id,
                    status=RunStatus(r.status),
                    started_at=r.started_at,
                    completed_at=r.completed_at,
                    inputs=json.loads(r.inputs_json or "{}"),
                    outputs=json.loads(r.outputs_json) if r.outputs_json else {},
                    error_message=r.error_message,
                )
                for r in rows
            ]

    def fail_orphaned_runs(self, reason: str = "Interrupted by a service restart") -> int:
        """Mark workflow runs left RUNNING by a previous process as FAILED. Returns the count."""
        from datetime import UTC, datetime

        from sqlalchemy import update

        stmt = (
            update(WorkflowRunRow)
            .where(WorkflowRunRow.status == str(RunStatus.RUNNING))
            .values(
                status=str(RunStatus.FAILED),
                completed_at=datetime.now(UTC),
                error_message=reason,
            )
        )
        with get_sessionmaker()() as session:
            result = session.execute(stmt)
            session.commit()
            return int(result.rowcount or 0)

    def prune_runs(self, workflow_id: str, keep: int = 50) -> None:
        with get_sessionmaker()() as session:
            old = (
                session.execute(
                    select(WorkflowRunRow.run_id)
                    .where(WorkflowRunRow.workflow_id == workflow_id)
                    .order_by(WorkflowRunRow.started_at.desc())
                    .offset(keep)
                )
                .scalars()
                .all()
            )
            if old:
                session.execute(delete(WorkflowRunRow).where(WorkflowRunRow.run_id.in_(old)))
                session.commit()
