"""Tests for identity & access: security, entitlements, and the auth API."""

from __future__ import annotations

import pytest
from app.contexts.identity_access.application.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.contexts.identity_access.domain.entitlements import (
    can_execute,
    has_capability,
)
from app.contexts.identity_access.domain.models import (
    Capability,
    GlobalRole,
    PermissionLevel,
    ResourcePermission,
    UserContext,
)
from app.platform import database
from app.platform.app_factory import create_app
from fastapi.testclient import TestClient

# --- pure unit tests (no DB) ----------------------------------------------------------------


def test_password_hash_roundtrip():
    stored = hash_password("s3cret")
    assert verify_password("s3cret", stored)
    assert not verify_password("wrong", stored)
    assert stored != hash_password("s3cret")  # salted


def test_token_roundtrip():
    ctx = UserContext(id="u1", username="alice", global_role=GlobalRole.ENGINEER)
    token = create_access_token(ctx)
    decoded = decode_token(token)
    assert decoded.id == "u1"
    assert decoded.global_role == GlobalRole.ENGINEER


def test_capability_matrix():
    admin = UserContext(id="a", username="a", global_role=GlobalRole.ADMIN)
    consumer = UserContext(id="c", username="c", global_role=GlobalRole.CONSUMER)
    assert has_capability(admin, Capability.MANAGE_INTEGRATIONS)
    assert not has_capability(consumer, Capability.MANAGE_INTEGRATIONS)


def test_operator_execute_requires_resource_permission():
    operator = UserContext(id="o", username="o", global_role=GlobalRole.OPERATOR)
    # No permission -> denied for live execution.
    assert not can_execute(
        operator, resource_type="workflow", resource_id="wf1", live=True, permissions=[]
    )
    grant = ResourcePermission(
        id="p1",
        resource_type="workflow",
        resource_id="wf1",
        permission_level=PermissionLevel.EXECUTE,
        user_id="o",
    )
    assert can_execute(
        operator, resource_type="workflow", resource_id="wf1", live=True, permissions=[grant]
    )


def test_admin_and_engineer_execute_broadly():
    admin = UserContext(id="a", username="a", global_role=GlobalRole.ADMIN)
    engineer = UserContext(id="e", username="e", global_role=GlobalRole.ENGINEER)
    assert can_execute(admin, resource_type="workflow", resource_id="x", live=True, permissions=[])
    assert can_execute(
        engineer, resource_type="workflow", resource_id="x", live=True, permissions=[]
    )


# --- auth API tests (DB + seeded users) -----------------------------------------------------


@pytest.fixture
def client():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.identity_access.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)
    with TestClient(create_app()) as c:
        yield c
    database.reset_for_tests()


def _login(client, username, password):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def test_login_success_and_me(client):
    resp = _login(client, "engineer", "engineer123")
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    assert resp.json()["user"]["global_role"] == "engineer"

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "engineer"


def test_login_bad_credentials(client):
    assert _login(client, "engineer", "nope").status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_users_endpoint_admin_only(client):
    admin_token = _login(client, "admin", "admin123").json()["access_token"]
    op_token = _login(client, "operator", "operator123").json()["access_token"]

    ok = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert ok.status_code == 200 and len(ok.json()) >= 4

    forbidden = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {op_token}"})
    assert forbidden.status_code == 403
