"""Tests for the automation catalog: lifecycle, execute-from-template, and API."""

from __future__ import annotations

import pytest
from app.contexts.automation_catalog.application.service import CatalogService
from app.contexts.automation_catalog.domain.models import (
    ApprovalState,
    SurveyField,
    TemplateDraft,
)
from app.contexts.connectors.domain.models import ConnectorKind
from app.contexts.identity_access.domain.models import GlobalRole, UserContext
from app.platform import database
from app.platform.app_factory import create_app
from app.shared_kernel.errors import ConflictError, EntitlementError
from fastapi.testclient import TestClient


def _ensure_schema():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    # Import every context's ORM so metadata is complete.
    import app.contexts.automation_catalog.infrastructure.orm  # noqa: F401
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


def _draft() -> TemplateDraft:
    return TemplateDraft(
        name="Patch Linux",
        connector=ConnectorKind.ANSIBLE,
        action="run_job_template",
        survey=[SurveyField(name="inventory", type="string", label="Inventory", required=True)],
        default_params={"playbooks": ["patch.yml"]},
    )


def test_create_approve_list_lifecycle():
    svc = CatalogService()
    t = svc.create(_draft(), owner="engineer")
    assert t.approval_state == ApprovalState.DRAFT
    assert svc.list(approval_state=ApprovalState.APPROVED) == []
    svc.approve(t.id)
    approved = svc.list(approval_state=ApprovalState.APPROVED)
    assert len(approved) == 1 and approved[0].id == t.id


async def test_execute_requires_approval():
    svc = CatalogService()
    t = svc.create(_draft(), owner="engineer")
    user = UserContext(id="e", username="eng", global_role=GlobalRole.ENGINEER)
    with pytest.raises(ConflictError):
        await svc.execute(t.id, user=user, survey_answers={"inventory": "h1"})


async def test_execute_maps_survey_and_defaults():
    svc = CatalogService()
    t = svc.create(_draft(), owner="engineer")
    svc.approve(t.id)
    user = UserContext(id="e", username="eng", global_role=GlobalRole.ENGINEER)
    job = await svc.execute(
        t.id, user=user, survey_answers={"inventory": "web-01"}, check_mode=True
    )
    persisted = svc.execution.get(job.id)
    assert persisted is not None
    assert persisted.params["inventory"] == "web-01"
    assert persisted.params["playbooks"] == ["patch.yml"]
    assert persisted.check_mode is True


async def test_consumer_cannot_execute_live():
    svc = CatalogService()
    t = svc.create(_draft(), owner="engineer")
    svc.approve(t.id)
    consumer = UserContext(id="c", username="cons", global_role=GlobalRole.CONSUMER)
    with pytest.raises(EntitlementError):
        await svc.execute(t.id, user=consumer, survey_answers={"inventory": "h1"}, check_mode=False)


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


def test_engineer_can_author_and_approve_then_operator_lists(client):
    eng = _token(client, "engineer", "engineer123")
    headers = {"Authorization": f"Bearer {eng}"}
    created = client.post(
        "/api/v1/catalog/templates",
        headers=headers,
        json={"name": "T1", "connector": "terraform", "action": "plan"},
    )
    assert created.status_code == 200
    tid = created.json()["id"]
    assert (
        client.post(f"/api/v1/catalog/templates/{tid}/approve", headers=headers).status_code == 200
    )

    listed = client.get("/api/v1/catalog/templates")
    assert any(t["id"] == tid for t in listed.json())


def test_operator_cannot_author(client):
    op = _token(client, "operator", "operator123")
    resp = client.post(
        "/api/v1/catalog/templates",
        headers={"Authorization": f"Bearer {op}"},
        json={"name": "X", "connector": "script", "action": "run"},
    )
    assert resp.status_code == 403


def test_execute_template_via_api(client):
    eng = _token(client, "engineer", "engineer123")
    headers = {"Authorization": f"Bearer {eng}"}
    tid = client.post(
        "/api/v1/catalog/templates",
        headers=headers,
        json={"name": "Plan", "connector": "terraform", "action": "plan"},
    ).json()["id"]
    client.post(f"/api/v1/catalog/templates/{tid}/approve", headers=headers)
    resp = client.post(
        f"/api/v1/catalog/templates/{tid}/execute",
        headers=headers,
        json={"survey_answers": {"workspace": "prod"}, "check_mode": True},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "PENDING"
