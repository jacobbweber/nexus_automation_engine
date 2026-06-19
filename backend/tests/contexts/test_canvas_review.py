"""Tests for governed workflow submission & review (M15)."""

from __future__ import annotations

import pytest
from app.contexts.orchestration_canvas.application.service import CanvasService
from app.contexts.orchestration_canvas.domain.models import (
    Edge,
    Node,
    NodeType,
    ReviewState,
    WorkflowGraph,
)
from app.platform import database
from app.platform.app_factory import create_app
from app.shared_kernel.errors import ValidationError
from fastapi.testclient import TestClient


def _ensure_schema():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.identity_access.infrastructure.orm  # noqa: F401
    import app.contexts.orchestration_canvas.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_db():
    _ensure_schema()
    yield
    database.reset_for_tests()


def _make_wf() -> str:
    graph = WorkflowGraph(
        nodes=[Node(id="start", type=NodeType.START), Node(id="end", type=NodeType.END)],
        edges=[Edge(source="start", target="end")],
    )
    return CanvasService().save_workflow(name="Review WF", graph=graph).id


def test_submit_and_approve_lifecycle():
    svc = CanvasService()
    wf = _make_wf()
    assert svc.get_workflow(wf).review_state == ReviewState.DRAFT
    svc.submit_for_review(wf, submitted_by="operator")
    assert svc.get_workflow(wf).review_state == ReviewState.SUBMITTED
    assert any(w.id == wf for w in svc.pending_reviews())
    approved = svc.review(wf, "approve", reviewer="engineer", comment="LGTM")
    assert approved.review_state == ReviewState.APPROVED
    assert approved.reviewed_by == "engineer"
    decisions = [r.decision for r in svc.reviews(wf)]
    assert decisions == ["submit", "approve"]


def test_request_changes_keeps_it_pending():
    svc = CanvasService()
    wf = _make_wf()
    svc.submit_for_review(wf, submitted_by="operator")
    svc.review(wf, "request_changes", reviewer="engineer", comment="add an approval gate")
    assert svc.get_workflow(wf).review_state == ReviewState.CHANGES_REQUESTED
    assert any(w.id == wf for w in svc.pending_reviews())


def test_invalid_decision_raises():
    svc = CanvasService()
    wf = _make_wf()
    svc.submit_for_review(wf, submitted_by="operator")
    with pytest.raises(ValidationError):
        svc.review(wf, "nuke", reviewer="engineer")


def test_graph_save_preserves_review_state():
    svc = CanvasService()
    wf = _make_wf()
    svc.submit_for_review(wf, submitted_by="operator")
    svc.review(wf, "approve", reviewer="engineer")
    # Editing the graph must not silently reset the review state.
    svc.save_workflow(name="Review WF v2", graph=WorkflowGraph(), workflow_id=wf)
    assert svc.get_workflow(wf).review_state == ReviewState.APPROVED


# --- API ------------------------------------------------------------------------------------


@pytest.fixture
def client():
    _ensure_schema()
    with TestClient(create_app()) as c:
        yield c
    database.reset_for_tests()


def _token(client, user, pw):
    return client.post("/api/v1/auth/login", json={"username": user, "password": pw}).json()[
        "access_token"
    ]


def test_submit_review_api_rbac(client):
    wf_id = _make_wf()
    op = _token(client, "operator", "operator123")
    eng = _token(client, "engineer", "engineer123")

    submitted = client.post(
        f"/api/v1/canvas/workflows/{wf_id}/submit", headers={"Authorization": f"Bearer {op}"}
    )
    assert submitted.status_code == 200
    assert submitted.json()["review_state"] == "submitted"

    # Operator cannot review.
    denied = client.post(
        f"/api/v1/canvas/workflows/{wf_id}/review",
        headers={"Authorization": f"Bearer {op}"},
        json={"decision": "approve"},
    )
    assert denied.status_code == 403

    # Engineer reviews.
    ok = client.post(
        f"/api/v1/canvas/workflows/{wf_id}/review",
        headers={"Authorization": f"Bearer {eng}"},
        json={"decision": "approve", "comment": "ship it"},
    )
    assert ok.status_code == 200 and ok.json()["review_state"] == "approved"

    inbox = client.get("/api/v1/canvas/reviews/pending", headers={"Authorization": f"Bearer {eng}"})
    assert inbox.status_code == 200
