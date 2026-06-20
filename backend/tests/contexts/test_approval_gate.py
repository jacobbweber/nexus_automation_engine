"""Run-level approval gate: request, decide, and the start_run gate (story 26.4)."""

from __future__ import annotations

import pytest
from app.contexts.orchestration_canvas.application.service import CanvasService
from app.contexts.orchestration_canvas.domain.models import Edge, Node, NodeType, WorkflowGraph
from app.contexts.review.application.service import ReviewService
from app.contexts.review.domain.approval import ApprovalDecision, ApprovalStatus
from app.platform import database
from app.shared_kernel.errors import ConflictError


def _ensure_schema():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.platform.app_factory  # noqa: F401  (registers all ORM)

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_db():
    _ensure_schema()
    yield
    database.reset_for_tests()


def _prod_workflow() -> str:
    """A workflow with a production-targeting automation task → requires approval."""
    graph = WorkflowGraph(
        nodes=[
            Node(id="start", type=NodeType.START),
            Node(
                id="task",
                type=NodeType.AUTOMATION_TASK,
                data={
                    "connector": "ansible",
                    "action": "rolling_os_patching",
                    "params": {"target": "web-prod-01"},
                },
            ),
            Node(id="end", type=NodeType.END, data={"outputs": {}}),
        ],
        edges=[Edge(source="start", target="task"), Edge(source="task", target="end")],
    )
    return CanvasService().save_workflow(name="Patch prod web", graph=graph).id


def test_prod_run_is_gated_until_approved():
    wf_id = _prod_workflow()
    review = ReviewService()
    # gate raises before approval
    with pytest.raises(ConflictError):
        review.enforce_run_allowed(wf_id)
    with pytest.raises(ConflictError):
        CanvasService().start_run(wf_id, {})

    # request + approve
    req = review.request_approval(wf_id, requested_by="op")
    assert req.status == ApprovalStatus.PENDING
    assert req.packet is not None and req.packet.requires_approval
    review.decide(req.id, ApprovalDecision.APPROVE, decided_by="lead")
    assert review.has_approval(wf_id)

    # now the gate passes (no raise)
    review.enforce_run_allowed(wf_id)


async def test_plan_run_is_exempt_from_gate():
    wf_id = _prod_workflow()
    # a plan/compliance run is read-only → not gated (async: start_run schedules a background task)
    run_id = CanvasService().start_run(wf_id, {}, plan=True)
    assert run_id


def test_request_dedupes_pending():
    wf_id = _prod_workflow()
    review = ReviewService()
    a = review.request_approval(wf_id)
    b = review.request_approval(wf_id)
    assert a.id == b.id
    assert len(review.pending()) == 1


def test_reject_does_not_grant_approval():
    wf_id = _prod_workflow()
    review = ReviewService()
    req = review.request_approval(wf_id)
    review.decide(req.id, ApprovalDecision.REJECT, decided_by="lead", comment="no")
    assert not review.has_approval(wf_id)
    with pytest.raises(ConflictError):
        review.enforce_run_allowed(wf_id)
