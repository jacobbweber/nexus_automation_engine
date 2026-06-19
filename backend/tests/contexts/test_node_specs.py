"""Node-type schema registry + rich condition operators + CMDB field picker."""

from __future__ import annotations

import pytest
from app.contexts.identity_access.application.security import create_access_token
from app.contexts.identity_access.domain.models import GlobalRole, UserContext
from app.contexts.orchestration_canvas.application.node_actions import _compare
from app.contexts.orchestration_canvas.domain.node_specs import NODE_SPECS, node_specs
from app.platform.app_factory import create_app
from fastapi.testclient import TestClient


def _auth() -> dict[str, str]:
    token = create_access_token(
        UserContext(id="u1", username="op", global_role=GlobalRole.ENGINEER)
    )
    return {"Authorization": f"Bearer {token}"}


# --- rich condition operators ---------------------------------------------------------------


@pytest.mark.parametrize(
    "a,b,op,case_sensitive,expected",
    [
        (5, "3", ">=", True, True),
        (3, "3", ">=", True, True),
        (2, "3", "<=", True, True),
        ("Prod", "prod", "==", False, True),
        ("Prod", "prod", "==", True, False),
        ("web-prod-01", "prod", "contains", True, True),
        ("web-dev-01", "prod", "not_contains", True, True),
        ("web-prod-01", "web", "starts_with", True, True),
        ("web-prod-01", "01", "ends_with", True, True),
        ("web-prod-01", r"prod-\d+", "matches_regex", True, True),
        ("staging", "prod,staging,dev", "in_list", True, True),
        ("", "", "is_empty", True, True),
        ("x", "", "is_not_empty", True, True),
    ],
)
def test_compare_operators(a, b, op, case_sensitive, expected):
    assert _compare(a, b, op, case_sensitive) is expected


def test_compare_numeric_on_non_numeric_is_false():
    assert _compare("abc", "3", ">", True) is False


# --- node-type schema registry --------------------------------------------------------------


def test_every_node_type_has_a_spec():
    from app.contexts.orchestration_canvas.domain.models import NodeType

    spec_types = {s.type for s in node_specs()}
    assert {t.value for t in NodeType} <= spec_types


def test_condition_spec_exposes_operator_choices_and_branch_outputs():
    cond = next(s for s in NODE_SPECS if s.type == "condition")
    operator = next(f for f in cond.fields if f.name == "operator")
    assert {"matches_regex", "in_list", ">=", "<="} <= set(operator.choices or [])
    assert cond.outputs == ["true", "false"]


def test_node_types_endpoint(monkeypatch):
    with TestClient(create_app()) as client:
        resp = client.get("/api/v1/canvas/node-types", headers=_auth())
    assert resp.status_code == 200
    types = {s["type"] for s in resp.json()}
    assert "cmdb_lookup" in types and "condition" in types


# --- CMDB field picker ----------------------------------------------------------------------


def test_cmdb_fields_endpoint_lists_tables_and_fields():
    with TestClient(create_app()) as client:
        resp = client.get("/api/v1/connectors/servicenow/fields", headers=_auth())
    assert resp.status_code == 200
    body = resp.json()
    assert "cmdb_ci_server" in body["tables"]
    names = {f["name"] for f in body["fields"]}
    assert {"name", "env", "lifecycle_state", "cluster"} <= names


def test_cmdb_fields_narrowed_by_table():
    with TestClient(create_app()) as client:
        resp = client.get(
            "/api/v1/connectors/servicenow/fields?table=cmdb_ci_storage_device", headers=_auth()
        )
    names = {f["name"] for f in resp.json()["fields"]}
    # datastores carry cluster but never an OS field.
    assert "cluster" in names and "os" not in names
