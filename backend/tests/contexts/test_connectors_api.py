"""API tests for the connectors routes."""

from __future__ import annotations

from app.platform.app_factory import create_app
from fastapi.testclient import TestClient


def test_list_connectors_returns_all_kinds():
    with TestClient(create_app()) as client:
        resp = client.get("/api/v1/connectors")
    assert resp.status_code == 200
    kinds = {c["kind"] for c in resp.json()}
    assert {"ansible", "terraform", "script", "servicenow", "cyberark", "dynatrace"} <= kinds


def test_get_single_connector_capabilities():
    with TestClient(create_app()) as client:
        resp = client.get("/api/v1/connectors/ansible")
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "ansible"
    assert body["supports_check_mode"] is True
    assert body["actions"]


def test_cmdb_discovery_endpoint():
    with TestClient(create_app()) as client:
        resp = client.post(
            "/api/v1/connectors/servicenow/discover",
            json={"source": "cmdb_ci_server", "filters": {"env": "Production"}},
        )
    assert resp.status_code == 200
    rows = resp.json()
    assert rows and all(r["attributes"]["env"] == "Production" for r in rows)


def test_servicenow_changes_endpoint():
    with TestClient(create_app()) as client:
        resp = client.get("/api/v1/connectors/servicenow/changes")
    assert resp.status_code == 200
    changes = resp.json()
    assert len(changes) >= 5
    c = changes[0]
    assert {"number", "state", "start", "end", "assignment_group", "affected_cis"} <= c.keys()
    # sorted chronologically by start
    starts = [x["start"] for x in changes]
    assert starts == sorted(starts)


def test_unknown_connector_kind_is_422():
    with TestClient(create_app()) as client:
        resp = client.get("/api/v1/connectors/not-a-real-connector")
    assert resp.status_code == 422  # enum validation
