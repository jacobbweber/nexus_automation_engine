"""Workflow ownership metadata, usage telemetry/reporting, and the seeded enterprise library."""

from __future__ import annotations

import pytest
from app.contexts.orchestration_canvas.application.seed import seed_workflow_library
from app.contexts.orchestration_canvas.application.service import CanvasService
from app.contexts.orchestration_canvas.domain.models import (
    Edge,
    Node,
    NodeType,
    ReviewState,
    RunStatus,
    WorkflowGraph,
    WorkflowRun,
)
from app.contexts.orchestration_canvas.infrastructure.repository import CanvasRepository
from app.platform import database
from app.platform.app_factory import create_app
from app.shared_kernel.ids import new_id
from fastapi.testclient import TestClient


def _ensure_schema():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.orchestration_canvas.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_db():
    _ensure_schema()
    yield
    database.reset_for_tests()


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


def _graph() -> WorkflowGraph:
    return WorkflowGraph(
        nodes=[Node(id="start", type=NodeType.START), Node(id="end", type=NodeType.END)],
        edges=[Edge(source="start", target="end")],
    )


def test_save_persists_owner_team_tags():
    svc = CanvasService()
    wf = svc.save_workflow(
        name="Owned WF", graph=_graph(), owner="alice", team="Storage", tags=["pure", "x"]
    )
    fetched = svc.get_workflow(wf.id)
    assert fetched.owner == "alice"
    assert fetched.team == "Storage"
    assert fetched.tags == ["pure", "x"]


def test_metadata_preserved_across_graph_edit():
    svc = CanvasService()
    wf = svc.save_workflow(name="Edit WF", graph=_graph(), owner="bob", team="Compute")
    # Re-save with a new graph but no metadata — ownership must survive.
    svc.save_workflow(name="Edit WF", graph=WorkflowGraph(), workflow_id=wf.id)
    again = svc.get_workflow(wf.id)
    assert again.owner == "bob" and again.team == "Compute"


def test_usage_report_counts_runs_and_success_rate():
    svc = CanvasService()
    repo = CanvasRepository()
    wf = svc.save_workflow(name="Telemetry WF", graph=_graph(), owner="carol")
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    for status in (RunStatus.COMPLETED, RunStatus.COMPLETED, RunStatus.FAILED):
        repo.save_run(
            WorkflowRun(run_id=new_id("run"), workflow_id=wf.id, status=status, started_at=now)
        )
    report = {r.id: r for r in svc.report()}[wf.id]
    assert report.usage.run_count == 3
    assert report.usage.success_count == 2
    assert report.usage.failure_count == 1
    assert abs(report.usage.success_rate - (2 / 3)) < 1e-6
    assert report.owner == "carol"
    assert report.node_count == 2


def test_report_endpoint(client):
    svc = CanvasService()
    svc.save_workflow(name="Reportable", graph=_graph(), owner="dave", team="ITSM", tags=["t"])
    resp = client.get("/api/v1/canvas/workflows/report")
    assert resp.status_code == 200
    rows = resp.json()
    mine = next(r for r in rows if r["name"] == "Reportable")
    assert mine["team"] == "ITSM" and mine["owner"] == "dave"
    assert "usage" in mine and mine["usage"]["run_count"] == 0


def test_seed_library_is_substantial_and_governed():
    repo = CanvasRepository()
    created = seed_workflow_library(repo)
    assert created >= 12  # a full library, not a couple of examples
    workflows = repo.list_workflows()
    teams = {w.team for w in workflows}
    assert {"Storage", "Compute", "Backup", "ITSM", "Security", "Platform"} <= teams
    # Varied review states so the review inbox + library both have substance.
    states = {w.review_state for w in workflows}
    assert ReviewState.PUBLISHED in states
    assert ReviewState.SUBMITTED in states
    # Every seeded workflow carries ownership metadata.
    assert all(w.owner and w.team and w.tags for w in workflows)


def test_seed_library_is_idempotent():
    repo = CanvasRepository()
    first = seed_workflow_library(repo)
    assert first >= 12
    assert seed_workflow_library(repo) == 0


def test_seeded_workflows_have_usage_telemetry():
    repo = CanvasRepository()
    seed_workflow_library(repo)
    usage = repo.usage_by_workflow()
    # At least one published workflow accumulated runs.
    assert any(u.run_count > 0 for u in usage.values())
