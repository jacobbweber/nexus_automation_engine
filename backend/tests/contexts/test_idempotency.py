"""Idempotency-class contract: inference, connector auto-classification, catalog seed (25.1)."""

from __future__ import annotations

import pytest
from app.contexts.automation_catalog.application.seed import seed_templates
from app.contexts.automation_catalog.application.service import CatalogService
from app.contexts.connectors.domain.models import ConnectorAction
from app.platform import database
from app.shared_kernel.idempotency import IdempotencyClass, infer_idempotency, is_flagged


def test_infer_classes():
    assert infer_idempotency("delete_datastore") == IdempotencyClass.NON_IDEMPOTENT
    assert infer_idempotency("eradicate_volume") == IdempotencyClass.NON_IDEMPOTENT
    assert infer_idempotency("plan") == IdempotencyClass.CHECK_ONLY
    assert infer_idempotency("cmdb_lookup") == IdempotencyClass.CHECK_ONLY
    assert infer_idempotency("run_job_template") == IdempotencyClass.IDEMPOTENT


def test_is_flagged():
    assert is_flagged(IdempotencyClass.NON_IDEMPOTENT)
    assert not is_flagged(IdempotencyClass.IDEMPOTENT)
    assert not is_flagged(IdempotencyClass.CHECK_ONLY)


def test_connector_action_auto_classifies():
    assert ConnectorAction(name="delete_datastore", label="x").idempotency == (
        IdempotencyClass.NON_IDEMPOTENT
    )
    assert ConnectorAction(name="plan", label="x").idempotency == IdempotencyClass.CHECK_ONLY
    assert ConnectorAction(name="apply", label="x").idempotency == IdempotencyClass.IDEMPOTENT


def test_connector_action_explicit_override_preserved():
    a = ConnectorAction(name="weird", label="x", idempotency=IdempotencyClass.NON_IDEMPOTENT)
    assert a.idempotency == IdempotencyClass.NON_IDEMPOTENT


def test_servicenow_actions_carry_idempotency():
    from app.contexts.connectors.infrastructure.simulation.servicenow import (
        ServiceNowSimConnector,
    )

    actions = {a.name: a.idempotency for a in ServiceNowSimConnector().capabilities().actions}
    assert actions["cmdb_lookup"] == IdempotencyClass.CHECK_ONLY
    assert actions["validate_request"] == IdempotencyClass.CHECK_ONLY


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


def test_seeded_templates_declare_idempotency(_db):
    seed_templates()
    templates = CatalogService().list_all()
    assert templates
    # destructive templates are flagged non-idempotent; plans are check-only; rest idempotent
    by_action = {t.action: t.idempotency for t in templates}
    # at least one non-idempotent (delete/eradicate/destroy) exists in the seed
    assert any(is_flagged(c) for c in by_action.values())
    # a terraform plan template is check-only
    assert any(
        t.idempotency == IdempotencyClass.CHECK_ONLY for t in templates if "plan" in t.action
    )
