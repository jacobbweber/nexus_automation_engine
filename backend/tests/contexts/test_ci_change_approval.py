"""CI-change approval path: health-check + gated approval (story 26.5)."""

from __future__ import annotations

import pytest
from app.contexts.review.application.service import ReviewService
from app.contexts.review.domain.approval import ApprovalDecision, ApprovalStatus
from app.platform import database


@pytest.fixture(autouse=True)
def _db():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.platform.app_factory  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    from app.contexts.cmdb.application.seed import seed_cmdb_lineage, seed_cmdb_schemas

    seed_cmdb_schemas()
    seed_cmdb_lineage()
    yield
    database.reset_for_tests()


def test_ci_change_opens_pending_approval_with_health_summary():
    # an incomplete VM (missing relationships/fields) → unhealthy → needs review
    ci = {"id": "ci-new", "name": "newvm01", "ci_type": "vm", "tags": {}, "relationships": {}}
    req = ReviewService().request_ci_change(ci, requested_by="op")
    assert req.source_type == "ci_change"
    assert req.status == ApprovalStatus.PENDING
    assert "health" in req.comment.lower()


def test_ci_change_decision_flow():
    ci = {"id": "ci-new", "name": "newvm01", "ci_type": "vm", "tags": {}, "relationships": {}}
    review = ReviewService()
    req = review.request_ci_change(ci)
    decided = review.decide(req.id, ApprovalDecision.APPROVE, decided_by="lead")
    assert decided.status == ApprovalStatus.APPROVED
    # it appears in neither the pending queue afterward
    assert all(r.id != req.id for r in review.pending())
