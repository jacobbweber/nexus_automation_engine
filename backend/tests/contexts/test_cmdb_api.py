"""CMDB API: schema/lineage registry (admin-gated) + validate-ci + ci/health (story 24.4)."""

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
    # Fresh tables per test (demo-seeding is off in tests); seed cmdb schemas + lineage explicitly.
    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    from app.contexts.cmdb.application.seed import seed_cmdb_lineage, seed_cmdb_schemas

    seed_cmdb_schemas()
    seed_cmdb_lineage()
    with TestClient(create_app()) as c:  # lifespan seeds default users for auth
        yield c
    database.reset_for_tests()


def _token(client, user, pw):
    return client.post("/api/v1/auth/login", json={"username": user, "password": pw}).json()[
        "access_token"
    ]


def test_list_and_get_schemas(client):
    r = client.get("/api/v1/cmdb/schemas")
    assert r.status_code == 200
    types = {s["type"] for s in r.json()}
    assert {"vm", "datastore", "cluster"} <= types
    vm = client.get("/api/v1/cmdb/schemas/vm")
    assert vm.status_code == 200 and vm.json()["type"] == "vm"


def test_get_unknown_schema_404(client):
    assert client.get("/api/v1/cmdb/schemas/nope").status_code == 404


def test_put_schema_requires_admin(client):
    body = {"type": "vm", "label": "VM", "fields": []}
    op = _token(client, "operator", "operator123")
    assert (
        client.put(
            "/api/v1/cmdb/schemas/vm", headers={"Authorization": f"Bearer {op}"}, json=body
        ).status_code
        == 403
    )
    admin = _token(client, "admin", "admin123")
    ok = client.put(
        "/api/v1/cmdb/schemas/vm", headers={"Authorization": f"Bearer {admin}"}, json=body
    )
    assert ok.status_code == 200 and ok.json()["updated_by"] == "admin"


def test_put_invalid_schema_400(client):
    admin = _token(client, "admin", "admin123")
    bad = {
        "type": "vm",
        "label": "VM",
        "fields": [{"name": "t", "label": "T", "datatype": "enum"}],
    }  # enum w/o allowed_values
    r = client.put(
        "/api/v1/cmdb/schemas/vm", headers={"Authorization": f"Bearer {admin}"}, json=bad
    )
    assert r.status_code == 400


def test_lineage_endpoints(client):
    r = client.get("/api/v1/cmdb/lineage")
    assert r.status_code == 200 and any(s["type"] == "vm" for s in r.json())
    vm = client.get("/api/v1/cmdb/lineage/vm")
    assert vm.status_code == 200 and any(
        rel["name"] == "host" for rel in vm.json()["relationships"]
    )


def test_validate_ci_adhoc(client):
    # a vm missing required fields/relationships → not healthy, with hints
    ci = {"id": "x", "name": "bad name", "ci_type": "vm", "tags": {}, "relationships": {}}
    r = client.post("/api/v1/cmdb/validate-ci", json=ci)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("degraded", "unhealthy")
    assert body["remediation_hints"]


def test_ci_health_resolves_from_cmdb(client):
    # web-prod-01 is a fully-populated VM in the seeded sim → healthy
    healthy = client.get("/api/v1/cmdb/ci/web-prod-01/health")
    assert healthy.status_code == 200
    assert healthy.json()["ci_type"] == "vm"
    assert healthy.json()["status"] == "healthy"
    # app-stg-01 is intentionally incomplete → degraded/unhealthy
    degraded = client.get("/api/v1/cmdb/ci/app-stg-01/health")
    assert degraded.status_code == 200
    assert degraded.json()["status"] in ("degraded", "unhealthy")


def test_ci_health_unknown_404(client):
    assert client.get("/api/v1/cmdb/ci/ghost/health").status_code == 404
