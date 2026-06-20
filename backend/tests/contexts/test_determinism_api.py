"""Determinism API: rules CRUD (admin), coverage, reconcile + CI-change trigger (story 27.4)."""

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
    from app.contexts.cmdb.application.seed import seed_cmdb_lineage, seed_cmdb_schemas
    from app.contexts.determinism.application.seed import seed_pinning_rules
    from app.contexts.orchestration_canvas.application.seed import seed_workflow_library

    seed_templates()
    seed_cmdb_schemas()
    seed_cmdb_lineage()
    seed_workflow_library()
    seed_pinning_rules()
    with TestClient(create_app()) as c:
        yield c
    database.reset_for_tests()


def _tok(client, user="admin", pw="admin123"):
    return client.post("/api/v1/auth/login", json={"username": user, "password": pw}).json()[
        "access_token"
    ]


def test_list_rules(client):
    r = client.get("/api/v1/determinism/rules", headers={"Authorization": f"Bearer {_tok(client)}"})
    assert r.status_code == 200
    assert any("DR-Tier" in str(rule["selector"]) for rule in r.json())


def test_rule_crud_admin_gated(client):
    op = _tok(client, "operator", "operator123")
    rule = {
        "id": "r_test",
        "name": "Test",
        "workflow": "X",
        "selector": {"ci_type": "datastore"},
        "trigger": "on_schedule",
        "enforcement": "assert",
    }
    assert (
        client.put(
            "/api/v1/determinism/rules/r_test", headers={"Authorization": f"Bearer {op}"}, json=rule
        ).status_code
        == 403
    )
    admin = _tok(client)
    ok = client.put(
        "/api/v1/determinism/rules/r_test", headers={"Authorization": f"Bearer {admin}"}, json=rule
    )
    assert ok.status_code == 200
    assert (
        client.delete(
            "/api/v1/determinism/rules/r_test", headers={"Authorization": f"Bearer {admin}"}
        ).json()["deleted"]
        is True
    )


def test_invalid_rule_rejected(client):
    admin = _tok(client)
    bad = {
        "id": "bad",
        "name": "",
        "workflow": "",
        "selector": {},
        "trigger": "on_schedule",
        "enforcement": "assert",
    }
    assert (
        client.put(
            "/api/v1/determinism/rules/bad", headers={"Authorization": f"Bearer {admin}"}, json=bad
        ).status_code
        == 400
    )


def test_coverage_and_reconcile(client):
    h = {"Authorization": f"Bearer {_tok(client)}"}
    cov = client.get("/api/v1/determinism/coverage", headers=h)
    assert cov.status_code == 200 and cov.json()["total_cis"] > 0
    rec = client.post("/api/v1/determinism/reconcile", headers=h)
    assert rec.status_code == 200 and isinstance(rec.json(), list)
