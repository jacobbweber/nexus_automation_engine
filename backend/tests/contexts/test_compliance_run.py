"""Compliance-mode run intent: catalog template + canvas workflow endpoints (story 25.3)."""

from __future__ import annotations

import pytest
from app.platform import database
from app.platform.app_factory import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    from app.contexts.automation_catalog.application.seed import seed_templates
    from app.contexts.orchestration_canvas.application.seed import seed_workflow_library

    seed_templates()
    seed_workflow_library()
    with TestClient(create_app()) as c:
        yield c
    database.reset_for_tests()


def _token(client, user="operator", pw="operator123"):
    return client.post("/api/v1/auth/login", json={"username": user, "password": pw}).json()[
        "access_token"
    ]


def test_template_compliance_returns_drift_report(client):
    tid = client.get("/api/v1/catalog/templates").json()[0]["id"]
    r = client.post(
        f"/api/v1/catalog/templates/{tid}/compliance",
        headers={"Authorization": f"Bearer {_token(client)}"},
        json={"survey_answers": {"target": "web-prod-01"}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("compliant", "drifted", "unknown")
    assert "resources" in body and "drift_count" in body


def test_template_compliance_is_deterministic(client):
    tid = client.get("/api/v1/catalog/templates").json()[0]["id"]
    h = {"Authorization": f"Bearer {_token(client)}"}
    a = client.post(
        f"/api/v1/catalog/templates/{tid}/compliance",
        headers=h,
        json={"survey_answers": {"target": "db-prod-01"}},
    ).json()
    b = client.post(
        f"/api/v1/catalog/templates/{tid}/compliance",
        headers=h,
        json={"survey_answers": {"target": "db-prod-01"}},
    ).json()
    assert a == b


def test_workflow_compliance_aggregates(client):
    wfs = client.get("/api/v1/canvas/workflows").json()
    assert wfs
    wf_id = wfs[0]["id"]
    r = client.post(
        f"/api/v1/canvas/workflows/{wf_id}/compliance",
        headers={"Authorization": f"Bearer {_token(client)}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("compliant", "drifted", "unknown")
    assert body["drift_count"] >= 0


def test_compliance_requires_auth(client):
    tid = client.get("/api/v1/catalog/templates").json()[0]["id"]
    r = client.post(f"/api/v1/catalog/templates/{tid}/compliance", json={"survey_answers": {}})
    assert r.status_code == 401
