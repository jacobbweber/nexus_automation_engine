"""Canvas service persistence + API (workflow CRUD, run persistence, versions)."""

from __future__ import annotations

import pytest
from app.contexts.orchestration_canvas.application.service import CanvasService, _apply_plan
from app.contexts.orchestration_canvas.domain.models import (
    Edge,
    Node,
    NodeType,
    RunStatus,
    WorkflowGraph,
)
from app.platform import database
from app.platform.app_factory import create_app
from fastapi.testclient import TestClient


def test_apply_plan_forces_check_mode_on_automation_tasks_only():
    nodes = [
        Node(id="start", type=NodeType.START),
        Node(
            id="t",
            type=NodeType.AUTOMATION_TASK,
            data={"connector": "ansible", "check_mode": False},
        ),
        Node(id="c", type=NodeType.CONDITION, data={"variable": "{{x}}"}),
    ]
    planned = {n.id: n for n in _apply_plan(nodes)}
    assert planned["t"].data["check_mode"] is True
    assert "check_mode" not in planned["c"].data  # non-task nodes untouched
    assert nodes[1].data["check_mode"] is False  # original not mutated


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


def _graph() -> WorkflowGraph:
    return WorkflowGraph(
        nodes=[
            Node(id="start", type=NodeType.START),
            Node(
                id="tf",
                type=NodeType.AUTOMATION_TASK,
                data={"connector": "terraform", "action": "plan", "params": {"workspace": "p"}},
            ),
            Node(id="end", type=NodeType.END, data={"outputs": {"ok": "{{tf.completed}}"}}),
        ],
        edges=[Edge(source="start", target="tf"), Edge(source="tf", target="end")],
    )


def test_save_get_list_delete_workflow():
    svc = CanvasService()
    wf = svc.save_workflow(name="Pipeline", graph=_graph(), description="demo")
    assert svc.get_workflow(wf.id).name == "Pipeline"
    assert len(svc.list_workflows()) == 1
    svc.delete_workflow(wf.id)
    assert svc.list_workflows() == []


async def test_run_workflow_persists_run_and_steps():
    svc = CanvasService()
    wf = svc.save_workflow(name="Pipeline", graph=_graph())
    run = await svc.run_workflow(wf.id, {})
    assert run.status == RunStatus.COMPLETED
    assert run.outputs.get("ok") is True

    persisted = svc.get_run(run.run_id)
    assert persisted.status == RunStatus.COMPLETED
    assert len(persisted.steps) == 3  # start, tf, end
    assert {s.node_id for s in persisted.steps} == {"start", "tf", "end"}


async def test_failed_run_is_recorded():
    svc = CanvasService()
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
    wf = svc.save_workflow(name="Failing", graph=graph)
    run = await svc.run_workflow(wf.id, {})
    assert run.status == RunStatus.FAILED
    assert run.error_message


def test_version_snapshot():
    svc = CanvasService()
    wf = svc.save_workflow(name="Pipeline", graph=_graph())
    svc.snapshot_version(wf.id, "v1")
    versions = svc.list_versions(wf.id)
    assert len(versions) == 1 and versions[0].description == "v1"


# --- API --------------------------------------------------------------------------------------


@pytest.fixture
def client():
    _ensure_schema()
    with TestClient(create_app()) as c:
        yield c
    database.reset_for_tests()


def test_workflow_crud_api(client):
    payload = {
        "name": "API WF",
        "graph": {
            "nodes": [
                {"id": "start", "type": "start", "data": {}},
                {"id": "end", "type": "end", "data": {"outputs": {}}},
            ],
            "edges": [{"source": "start", "target": "end"}],
        },
    }
    created = client.post("/api/v1/canvas/workflows", json=payload)
    assert created.status_code == 200
    wf_id = created.json()["id"]

    assert client.get(f"/api/v1/canvas/workflows/{wf_id}").status_code == 200
    listed = client.get("/api/v1/canvas/workflows").json()
    assert any(w["id"] == wf_id for w in listed)

    tok = client.post(
        "/api/v1/auth/login", json={"username": "operator", "password": "operator123"}
    ).json()["access_token"]
    run = client.post(
        f"/api/v1/canvas/workflows/{wf_id}/run",
        json={"inputs": {}},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert run.status_code == 200
    assert run.json()["run_id"].startswith("run_")


def test_approval_resolve_endpoint_unknown_is_false(client):
    resp = client.post(
        "/api/v1/canvas/approvals/resolve",
        json={"run_id": "nope", "node_id": "x", "approved": True},
    )
    assert resp.status_code == 200
    assert resp.json()["resolved"] is False
