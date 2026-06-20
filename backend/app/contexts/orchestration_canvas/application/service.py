"""CanvasService — workflow CRUD, versioning, run execution, and approval resume."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.contexts.orchestration_canvas.application.broker import RunBroker, get_run_broker
from app.contexts.orchestration_canvas.application.engine import execute_graph
from app.contexts.orchestration_canvas.application.node_actions import resolve_approval
from app.contexts.orchestration_canvas.domain.models import (
    Node,
    NodeType,
    ReviewRecord,
    ReviewState,
    RunStatus,
    Workflow,
    WorkflowGraph,
    WorkflowReport,
    WorkflowRun,
    WorkflowUsage,
    WorkflowVersion,
)
from app.contexts.orchestration_canvas.infrastructure.repository import CanvasRepository
from app.shared_kernel.errors import NotFoundError, ValidationError
from app.shared_kernel.ids import new_id
from app.shared_kernel.variable_pool import VariablePool


def _now() -> datetime:
    return datetime.now(UTC)


def _apply_plan(nodes: list[Node]) -> list[Node]:
    """Return a copy of the graph with every automation task forced into check/dry-run mode, so a
    plan run exercises the whole DAG (conditions, gates, lookups) without mutating anything."""
    return [
        node.model_copy(update={"data": {**node.data, "check_mode": True}})
        if node.type == NodeType.AUTOMATION_TASK
        else node
        for node in nodes
    ]


def _capture_workflow_failure(workflow_id: str, name: str, error: str) -> None:
    """Best-effort: open an incident when a workflow run fails."""
    from app.contexts.incident_management.application.service import capture_failure

    capture_failure(
        title=f"Workflow failed: {name}",
        source_type="workflow",
        source_id=workflow_id,
        summary=error,
    )


class CanvasService:
    def __init__(
        self, repository: CanvasRepository | None = None, broker: RunBroker | None = None
    ) -> None:
        self.repo = repository or CanvasRepository()
        self.broker = broker or get_run_broker()

    # --- workflow CRUD -----------------------------------------------------------------------

    def save_workflow(
        self,
        *,
        name: str,
        graph: WorkflowGraph,
        description: str = "",
        workflow_id: str | None = None,
        owner: str | None = None,
        team: str | None = None,
        tags: list[str] | None = None,
    ) -> Workflow:
        existing = self.repo.get_workflow(workflow_id) if workflow_id else None
        now = _now()
        workflow = Workflow(
            id=workflow_id or new_id("wf"),
            name=name,
            description=description,
            graph=graph,
            # Preserve existing ownership metadata across graph edits unless explicitly overridden.
            owner=owner if owner is not None else (existing.owner if existing else ""),
            team=team if team is not None else (existing.team if existing else ""),
            tags=tags if tags is not None else (existing.tags if existing else []),
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        return self.repo.save_workflow(workflow)

    def get_workflow(self, workflow_id: str) -> Workflow:
        wf = self.repo.get_workflow(workflow_id)
        if wf is None:
            raise NotFoundError(f"Workflow {workflow_id} not found")
        return wf

    def list_workflows(self) -> list[Workflow]:
        return self.repo.list_workflows()

    def report(self) -> list[WorkflowReport]:
        """Workflow library: each workflow's metadata joined with its run telemetry."""
        usage = self.repo.usage_by_workflow()
        reports: list[WorkflowReport] = []
        for wf in self.repo.list_workflows():
            reports.append(
                WorkflowReport(
                    id=wf.id,
                    name=wf.name,
                    description=wf.description,
                    owner=wf.owner,
                    team=wf.team,
                    tags=wf.tags,
                    review_state=wf.review_state,
                    node_count=len(wf.graph.nodes),
                    created_at=wf.created_at,
                    updated_at=wf.updated_at,
                    usage=usage.get(wf.id, WorkflowUsage(workflow_id=wf.id)),
                )
            )
        return reports

    def delete_workflow(self, workflow_id: str) -> None:
        self.repo.delete_workflow(workflow_id)

    # --- versions ----------------------------------------------------------------------------

    def snapshot_version(self, workflow_id: str, description: str = "") -> WorkflowVersion:
        wf = self.get_workflow(workflow_id)
        version = WorkflowVersion(
            version_id=new_id("ver"),
            workflow_id=workflow_id,
            graph=wf.graph,
            description=description,
            created_at=_now(),
        )
        self.repo.save_version(version)
        return version

    def list_versions(self, workflow_id: str) -> list[WorkflowVersion]:
        return self.repo.list_versions(workflow_id)

    # --- runs --------------------------------------------------------------------------------

    def get_run(self, run_id: str) -> WorkflowRun:
        run = self.repo.get_run(run_id)
        if run is None:
            raise NotFoundError(f"Run {run_id} not found")
        return run

    def list_runs(self, workflow_id: str) -> list[WorkflowRun]:
        return self.repo.list_runs(workflow_id)

    async def run_workflow(self, workflow_id: str, inputs: dict[str, Any], ws=None) -> WorkflowRun:
        wf = self.get_workflow(workflow_id)
        run_id = new_id("run")
        started = _now()
        run = WorkflowRun(
            run_id=run_id,
            workflow_id=workflow_id,
            status=RunStatus.RUNNING,
            started_at=started,
            inputs=inputs,
        )
        self.repo.save_run(run)
        if ws:
            await ws({"type": "run_started", "run_id": run_id, "workflow_id": workflow_id})

        pool = VariablePool()
        pool.set("start", inputs)
        try:
            outputs = await execute_graph(
                wf.graph.nodes, wf.graph.edges, pool, run_id, ws=ws, repo=self.repo
            )
            run = WorkflowRun(
                run_id=run_id,
                workflow_id=workflow_id,
                status=RunStatus.COMPLETED,
                started_at=started,
                completed_at=_now(),
                inputs=inputs,
                outputs=outputs,
            )
            self.repo.save_run(run)
            if ws:
                await ws({"type": "run_completed", "run_id": run_id, "outputs": outputs})
            return run
        except Exception as exc:  # noqa: BLE001
            run = WorkflowRun(
                run_id=run_id,
                workflow_id=workflow_id,
                status=RunStatus.FAILED,
                started_at=started,
                completed_at=_now(),
                inputs=inputs,
                error_message=str(exc),
            )
            self.repo.save_run(run)
            _capture_workflow_failure(workflow_id, wf.name, str(exc))
            if ws:
                await ws({"type": "run_failed", "run_id": run_id, "error": str(exc)})
            return run
        finally:
            self.repo.prune_runs(workflow_id)

    def start_run(self, workflow_id: str, inputs: dict[str, Any], plan: bool = False) -> str:
        """Create a run and execute it in the background, streaming to the broker. Returns run_id.

        The run_id is allocated up front so a client can subscribe to the WebSocket before the
        first event is published. ``plan=True`` forces every automation task into check/dry-run mode
        so nothing mutates — a safe "plan" of the whole workflow.
        """
        self.get_workflow(workflow_id)  # validate existence eagerly
        run_id = new_id("run")

        async def _runner() -> None:
            try:
                await self._run_with_fixed_id(workflow_id, inputs, run_id, plan=plan)
            finally:
                await self.broker.close(run_id)

        asyncio.create_task(_runner())
        return run_id

    async def _run_with_fixed_id(
        self, workflow_id: str, inputs: dict[str, Any], run_id: str, plan: bool = False
    ) -> WorkflowRun:
        wf = self.get_workflow(workflow_id)
        nodes = _apply_plan(wf.graph.nodes) if plan else wf.graph.nodes
        started = _now()
        self.repo.save_run(
            WorkflowRun(
                run_id=run_id,
                workflow_id=workflow_id,
                status=RunStatus.RUNNING,
                started_at=started,
                inputs=inputs,
            )
        )

        async def _ws(event: dict[str, Any]) -> None:
            event.setdefault("run_id", run_id)
            await self.broker.publish(run_id, event)

        await _ws({"type": "run_started", "workflow_id": workflow_id, "plan": plan})
        pool = VariablePool()
        pool.set("start", inputs)
        try:
            outputs = await execute_graph(
                nodes, wf.graph.edges, pool, run_id, ws=_ws, repo=self.repo
            )
            self.repo.save_run(
                WorkflowRun(
                    run_id=run_id,
                    workflow_id=workflow_id,
                    status=RunStatus.COMPLETED,
                    started_at=started,
                    completed_at=_now(),
                    inputs=inputs,
                    outputs=outputs,
                )
            )
            await _ws({"type": "run_completed", "outputs": outputs})
        except Exception as exc:  # noqa: BLE001
            self.repo.save_run(
                WorkflowRun(
                    run_id=run_id,
                    workflow_id=workflow_id,
                    status=RunStatus.FAILED,
                    started_at=started,
                    completed_at=_now(),
                    inputs=inputs,
                    error_message=str(exc),
                )
            )
            _capture_workflow_failure(workflow_id, wf.name, str(exc))
            await _ws({"type": "run_failed", "error": str(exc)})
        finally:
            self.repo.prune_runs(workflow_id)
        return self.get_run(run_id)

    def resume_approval(
        self, run_id: str, node_id: str, approved: bool, response: str = ""
    ) -> bool:
        return resolve_approval(run_id, node_id, approved, response)

    # --- governed submission / review (M15) --------------------------------------------------

    _DECISIONS = {
        "approve": ReviewState.APPROVED,
        "request_changes": ReviewState.CHANGES_REQUESTED,
        "reject": ReviewState.REJECTED,
        "publish": ReviewState.PUBLISHED,
    }

    def submit_for_review(self, workflow_id: str, submitted_by: str) -> Workflow:
        self.get_workflow(workflow_id)
        self.repo.set_review_state(workflow_id, ReviewState.SUBMITTED, submitted_by=submitted_by)
        self.repo.save_review(
            ReviewRecord(
                id=new_id("rev"),
                workflow_id=workflow_id,
                decision="submit",
                actor=submitted_by,
                comment="",
                created_at=_now(),
            )
        )
        return self.get_workflow(workflow_id)

    def review(self, workflow_id: str, decision: str, reviewer: str, comment: str = "") -> Workflow:
        if decision not in self._DECISIONS:
            raise ValidationError(f"Unknown review decision: {decision}")
        self.get_workflow(workflow_id)
        self.repo.set_review_state(workflow_id, self._DECISIONS[decision], reviewed_by=reviewer)
        self.repo.save_review(
            ReviewRecord(
                id=new_id("rev"),
                workflow_id=workflow_id,
                decision=decision,
                actor=reviewer,
                comment=comment,
                created_at=_now(),
            )
        )
        return self.get_workflow(workflow_id)

    def pending_reviews(self) -> list[Workflow]:
        return self.repo.list_pending_reviews()

    def reviews(self, workflow_id: str) -> list[ReviewRecord]:
        return self.repo.list_reviews(workflow_id)
