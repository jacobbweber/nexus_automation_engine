"""Tests for the incident kanban: capture, board, move, remediate, auto-capture."""

from __future__ import annotations

import pytest
from app.contexts.connectors.domain.models import ConnectorKind
from app.contexts.execution_engine.application.service import ExecutionService
from app.contexts.execution_engine.domain.models import JobStatus, JobSubmission
from app.contexts.incident_management.application.service import IncidentService
from app.contexts.incident_management.domain.models import IncidentStatus
from app.contexts.orchestration_canvas.application.service import CanvasService
from app.contexts.orchestration_canvas.domain.models import Edge, Node, NodeType, WorkflowGraph
from app.platform import database
from app.platform.app_factory import create_app
from fastapi.testclient import TestClient


def _ensure_schema():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.execution_engine.infrastructure.orm  # noqa: F401
    import app.contexts.incident_management.infrastructure.orm  # noqa: F401
    import app.contexts.orchestration_canvas.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_db():
    _ensure_schema()
    yield
    database.reset_for_tests()


def test_capture_and_dedupe():
    svc = IncidentService()
    inc = svc.capture(title="x", source_type="job", source_id="j1", summary="boom")
    assert inc is not None and inc.status == IncidentStatus.NEW
    # Second open capture for the same source de-dupes.
    assert svc.capture(title="x", source_type="job", source_id="j1") is None


def test_board_groups_by_column():
    svc = IncidentService()
    svc.capture(title="a", source_type="job", source_id="j1")
    board = svc.board()
    assert "new" in board and len(board["new"]) == 1
    assert set(board.keys()) == {"new", "triage", "investigating", "resolved"}


def test_move_to_resolved_sets_timestamp():
    svc = IncidentService()
    inc = svc.capture(title="a", source_type="job", source_id="j1")
    moved = svc.move(inc.id, IncidentStatus.RESOLVED)
    assert moved.status == IncidentStatus.RESOLVED and moved.resolved_at is not None


def test_remediate_creates_linked_workflow():
    svc = IncidentService()
    inc = svc.capture(title="DB down", source_type="workflow", source_id="wf1")
    wf_id = svc.remediate(inc.id)
    assert wf_id
    assert svc.get(inc.id).remediation_workflow_id == wf_id
    wf = CanvasService().get_workflow(wf_id)
    assert "Remediate" in wf.name


async def test_failed_job_auto_captures_incident():
    exec_svc = ExecutionService()
    job = exec_svc.submit(
        JobSubmission(
            name="Risky apply",
            connector=ConnectorKind.TERRAFORM,
            action="apply",
            params={"workspace": "p", "force_fail": True},
        )
    )
    result = await exec_svc.run(job.id)
    assert result == JobStatus.FAILED
    incidents = IncidentService().list_all()
    assert any(i.source_type == "job" and i.source_id == job.id for i in incidents)


async def test_failed_workflow_auto_captures_incident():
    canvas = CanvasService()
    graph = WorkflowGraph(
        nodes=[
            Node(id="start", type=NodeType.START),
            Node(
                id="tf",
                type=NodeType.AUTOMATION_TASK,
                data={
                    "connector": "terraform",
                    "action": "apply",
                    "params": {"workspace": "p", "force_fail": True},
                },
            ),
            Node(id="end", type=NodeType.END),
        ],
        edges=[Edge(source="start", target="tf"), Edge(source="tf", target="end")],
    )
    wf = canvas.save_workflow(name="Failing WF", graph=graph)
    await canvas.run_workflow(wf.id, {})
    assert any(
        i.source_type == "workflow" and i.source_id == wf.id for i in IncidentService().list_all()
    )


# --- API ------------------------------------------------------------------------------------


@pytest.fixture
def client():
    _ensure_schema()
    with TestClient(create_app()) as c:
        yield c
    database.reset_for_tests()


def test_incident_board_and_move_api(client):
    IncidentService().capture(title="a", source_type="job", source_id="j1")
    board = client.get("/api/v1/incidents/board")
    assert board.status_code == 200 and len(board.json()["new"]) == 1

    inc_id = client.get("/api/v1/incidents").json()[0]["id"]
    moved = client.post(f"/api/v1/incidents/{inc_id}/move", json={"status": "investigating"})
    assert moved.status_code == 200 and moved.json()["status"] == "investigating"

    rem = client.post(f"/api/v1/incidents/{inc_id}/remediate")
    assert rem.status_code == 200 and rem.json()["workflow_id"]
