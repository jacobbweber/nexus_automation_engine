"""Tests for change management: templates, policy, records, and execution gating."""

from __future__ import annotations

import pytest
from app.contexts.automation_catalog.application.service import CatalogService
from app.contexts.automation_catalog.domain.models import TemplateDraft
from app.contexts.change_management.application.service import ChangeService
from app.contexts.change_management.domain.models import (
    ChangeControlPolicy,
    ChangeState,
    ChangeTemplate,
    Risk,
)
from app.contexts.connectors.domain.models import ConnectorKind
from app.contexts.identity_access.domain.models import GlobalRole, UserContext
from app.platform import database
from app.platform.app_factory import create_app
from app.shared_kernel.errors import ConflictError
from app.shared_kernel.ids import new_id
from fastapi.testclient import TestClient


def _ensure_schema():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.automation_catalog.infrastructure.orm  # noqa: F401
    import app.contexts.change_management.infrastructure.orm  # noqa: F401
    import app.contexts.execution_engine.infrastructure.orm  # noqa: F401
    import app.contexts.identity_access.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_db():
    _ensure_schema()
    yield
    database.reset_for_tests()


def _standard_template() -> ChangeTemplate:
    return ChangeTemplate(id=new_id("chgtpl"), name="Standard", risk=Risk.LOW, cab_required=False)


def _cab_template() -> ChangeTemplate:
    return ChangeTemplate(id=new_id("chgtpl"), name="CAB", risk=Risk.HIGH, cab_required=True)


def test_open_standard_change_is_auto_approved():
    svc = ChangeService()
    tpl = svc.create_template(_standard_template())
    rec = svc.open_change(
        resource_type="template", resource_id="t1", initiated_by="op", template_id=tpl.id
    )
    assert rec.number.startswith("CHG")
    assert rec.state == ChangeState.APPROVED


def test_open_cab_change_awaits_assessment():
    svc = ChangeService()
    tpl = svc.create_template(_cab_template())
    rec = svc.open_change(
        resource_type="template", resource_id="t1", initiated_by="op", template_id=tpl.id
    )
    assert rec.state == ChangeState.ASSESS


def test_close_change():
    svc = ChangeService()
    rec = svc.open_change(resource_type="template", resource_id="t1", initiated_by="op")
    closed = svc.close_change(rec.number, success=True)
    assert closed.state == ChangeState.CLOSED
    assert closed.close_code == "successful"


def test_evaluate_no_policy_returns_none():
    svc = ChangeService()
    assert (
        svc.evaluate_for_execution(
            resource_type="template", resource_id="x", initiated_by="op", live=True
        )
        is None
    )


def test_evaluate_auto_standard_returns_change_number():
    svc = ChangeService()
    tpl = svc.create_template(_standard_template())
    svc.set_policy(
        ChangeControlPolicy(
            id=new_id("p"),
            resource_type="template",
            resource_id="t1",
            auto_change_control=True,
            change_template_id=tpl.id,
        )
    )
    num = svc.evaluate_for_execution(
        resource_type="template", resource_id="t1", initiated_by="op", live=True
    )
    assert num and num.startswith("CHG")


def test_evaluate_cab_required_blocks_live():
    svc = ChangeService()
    tpl = svc.create_template(_cab_template())
    svc.set_policy(
        ChangeControlPolicy(
            id=new_id("p"),
            resource_type="template",
            resource_id="t1",
            auto_change_control=True,
            change_template_id=tpl.id,
            require_approved_change=True,
        )
    )
    with pytest.raises(ConflictError):
        svc.evaluate_for_execution(
            resource_type="template", resource_id="t1", initiated_by="op", live=True
        )
    # Check mode (not live) is allowed even with require_approved_change.
    assert svc.evaluate_for_execution(
        resource_type="template", resource_id="t1", initiated_by="op", live=False
    )


async def test_catalog_execute_stamps_change_number():
    catalog = CatalogService()
    change = ChangeService()
    tpl = catalog.create(
        TemplateDraft(name="Patch", connector=ConnectorKind.ANSIBLE, action="run_job_template"),
        owner="engineer",
    )
    catalog.approve(tpl.id)
    chg_tpl = change.create_template(_standard_template())
    change.set_policy(
        ChangeControlPolicy(
            id=new_id("p"),
            resource_type="template",
            resource_id=tpl.id,
            auto_change_control=True,
            change_template_id=chg_tpl.id,
        )
    )
    user = UserContext(id="e", username="eng", global_role=GlobalRole.ENGINEER)
    job = await catalog.execute(tpl.id, user=user, survey_answers={}, check_mode=True)
    persisted = catalog.execution.get(job.id)
    assert persisted is not None and persisted.change_number
    assert change.get_record(persisted.change_number).number == persisted.change_number


# --- API ------------------------------------------------------------------------------------


@pytest.fixture
def client():
    _ensure_schema()
    with TestClient(create_app()) as c:
        yield c
    database.reset_for_tests()


def _eng_headers(client):
    tok = client.post(
        "/api/v1/auth/login", json={"username": "engineer", "password": "engineer123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_change_api_template_and_records(client):
    headers = _eng_headers(client)
    created = client.post(
        "/api/v1/change/templates",
        headers=headers,
        json={"name": "Std", "risk": "low", "cab_required": False},
    )
    assert created.status_code == 200
    assert any(t["name"] == "Std" for t in client.get("/api/v1/change/templates").json())


def test_change_policy_requires_engineer(client):
    op = client.post(
        "/api/v1/auth/login", json={"username": "operator", "password": "operator123"}
    ).json()["access_token"]
    resp = client.put(
        "/api/v1/change/policies",
        headers={"Authorization": f"Bearer {op}"},
        json={"resource_type": "template", "resource_id": "t1"},
    )
    assert resp.status_code == 403
