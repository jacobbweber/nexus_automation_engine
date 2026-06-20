"""Plain-summary metadata on building blocks (story 26.1)."""

from __future__ import annotations

import pytest
from app.contexts.automation_catalog.application.seed import seed_templates
from app.contexts.automation_catalog.application.service import CatalogService
from app.contexts.automation_catalog.domain.models import default_plain_summary
from app.platform import database


def test_default_plain_summary_classifies_outcome():
    delete = default_plain_summary(
        name="Delete Datastore",
        action="delete_datastore",
        vendor="VMware",
        domain="Storage",
        idempotent=False,
    )
    assert "removed" in delete.outcome
    assert "snapshot" in delete.rollback.lower() or "backup" in delete.rollback.lower()

    create = default_plain_summary(
        name="Provision VM",
        action="provision_vm",
        vendor="VMware",
        domain="Compute",
        idempotent=True,
    )
    assert "created" in create.outcome

    plan = default_plain_summary(
        name="Plan",
        action="plan",
        vendor="Terraform",
        domain="Compute",
        idempotent=True,
    )
    assert "nothing is changed" in plan.outcome


@pytest.fixture
def _db():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.automation_catalog.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    yield
    database.reset_for_tests()


def test_seeded_templates_carry_plain_summary(_db):
    seed_templates()
    templates = CatalogService().list_all()
    assert templates
    for t in templates:
        assert t.plain_summary is not None
        assert t.plain_summary.input and t.plain_summary.action and t.plain_summary.outcome
