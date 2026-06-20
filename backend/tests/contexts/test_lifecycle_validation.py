"""Tests for origin-story / CMDB lifecycle validation (M18)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.contexts.lifecycle_validation.application.service import (
    ValidationRejected,
    ValidationService,
)
from app.contexts.lifecycle_validation.domain.models import (
    AutomationMeta,
    ValidationPolicy,
    check_cmdb,
    check_metadata,
)
from app.platform import database
from app.platform.app_factory import create_app
from fastapi.testclient import TestClient


def _ensure_schema():
    database.reset_for_tests()
    from app.platform.config import get_settings

    get_settings.cache_clear()
    import app.contexts.automation_catalog.infrastructure.orm  # noqa: F401
    import app.contexts.lifecycle_validation.infrastructure.orm  # noqa: F401

    engine = database.get_engine()
    database.Base.metadata.drop_all(engine)
    database.Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_db():
    _ensure_schema()
    yield
    database.reset_for_tests()


def _valid_meta(**over) -> AutomationMeta:
    base = dict(
        name="Patch",
        action="run_job_template",
        risk="low",
        authored_by="eng",
        approved_date=datetime.now(UTC),
        last_updated=datetime.now(UTC),
        last_reviewed=datetime.now(UTC),
        ci_type="vm",
        ci_heritage="Ansible",
    )
    base.update(over)
    return AutomationMeta(**base)


# --- pure rules -----------------------------------------------------------------------------


def test_metadata_missing_fields():
    policy = ValidationPolicy()
    reasons = check_metadata(AutomationMeta(name="x"), policy)
    assert any("authored_by" in r for r in reasons)
    assert any("ci_type" in r for r in reasons)


def test_metadata_stale_review():
    policy = ValidationPolicy(max_review_age_days=30)
    meta = _valid_meta(last_reviewed=datetime.now(UTC) - timedelta(days=90))
    reasons = check_metadata(meta, policy)
    assert any("stale" in r for r in reasons)


def test_cmdb_unknown_retired_mismatch_cluster():
    policy = ValidationPolicy()
    assert check_cmdb(_valid_meta(), None, policy)  # unknown CI
    assert check_cmdb(_valid_meta(), {"lifecycle_state": "retired", "name": "x"}, policy)
    assert check_cmdb(
        _valid_meta(ci_type="vm"), {"ci_type": "datastore", "name": "x"}, policy
    )  # type mismatch
    assert check_cmdb(
        _valid_meta(action="delete_datastore", ci_type="datastore"),
        {"ci_type": "datastore", "cluster_member": True, "cluster": "c1", "name": "ds"},
        policy,
    )  # destructive on cluster
    assert not check_cmdb(
        _valid_meta(), {"ci_type": "vm", "lifecycle_state": "operational", "name": "ok"}, policy
    )


# --- service against the simulated CMDB -----------------------------------------------------


async def test_execution_validation_passes_for_clean_target():
    svc = ValidationService()
    result = await svc.validate_for_execution(_valid_meta(ci_type="vm"), "web-prod-01")
    assert result.ok, result.reasons


async def test_execution_validation_rejects_retired_ci():
    svc = ValidationService()
    result = await svc.validate_for_execution(_valid_meta(ci_type="vm"), "legacy-app-02")
    assert not result.ok and any("retired" in r for r in result.reasons)


async def test_execution_validation_blocks_destructive_on_cluster_datastore():
    svc = ValidationService()
    meta = _valid_meta(
        name="Delete DS", action="delete_datastore", risk="critical", ci_type="datastore"
    )
    result = await svc.validate_for_execution(meta, "ds-vvol-01")
    assert not result.ok and any("cluster" in r for r in result.reasons)


async def test_enforce_raises():
    with pytest.raises(ValidationRejected):
        await ValidationService().enforce_for_execution(_valid_meta(), "does-not-exist")


async def test_health_gate_blocks_degraded_ci_when_required():
    from app.contexts.cmdb.application.seed import seed_cmdb_lineage, seed_cmdb_schemas

    seed_cmdb_schemas()
    seed_cmdb_lineage()
    svc = ValidationService()
    pol = svc.get_policy()
    pol.require_healthy_ci = True
    pol.min_health_score = 70
    svc.update_policy(pol)
    # app-stg-01 is an incomplete VM (missing relationships/tags) → blocked on health grounds
    bad = await svc.validate_for_execution(_valid_meta(ci_type="vm"), "app-stg-01")
    assert not bad.ok and any("health" in r for r in bad.reasons)
    # web-prod-01 is a fully-populated VM → passes
    good = await svc.validate_for_execution(_valid_meta(ci_type="vm"), "web-prod-01")
    assert good.ok, good.reasons


async def test_health_gate_off_by_default():
    from app.contexts.cmdb.application.seed import seed_cmdb_lineage, seed_cmdb_schemas

    seed_cmdb_schemas()
    seed_cmdb_lineage()
    # default policy does not require CI health → a degraded CI is not blocked on health grounds
    res = await ValidationService().validate_for_execution(_valid_meta(ci_type="vm"), "app-stg-01")
    assert res.ok, res.reasons


def test_build_validation_flags_incomplete():
    result = ValidationService().validate_for_build(AutomationMeta(name="bare"))
    assert not result.ok and result.stage == "build"


async def test_canvas_automation_task_node_is_gated():
    import os

    from app.contexts.orchestration_canvas.application.engine import execute_graph
    from app.contexts.orchestration_canvas.domain.models import Edge, Node, NodeType
    from app.platform.config import get_settings
    from app.shared_kernel.errors import NexusError
    from app.shared_kernel.variable_pool import VariablePool

    os.environ["NEXUS_ENFORCE_LIFECYCLE_VALIDATION"] = "true"
    get_settings.cache_clear()
    try:
        nodes = [
            Node(id="start", type=NodeType.START),
            Node(
                id="task",
                type=NodeType.AUTOMATION_TASK,
                data={
                    "connector": "vmware",
                    "action": "delete_datastore",
                    "params": {"target": "ds-vvol-01"},
                },
            ),  # cluster member -> blocked
            Node(id="end", type=NodeType.END),
        ]
        edges = [Edge(source="start", target="task"), Edge(source="task", target="end")]
        pool = VariablePool()
        pool.set("start", {})
        with pytest.raises(NexusError):
            await execute_graph(nodes, edges, pool, "r", persist=False)
    finally:
        os.environ["NEXUS_ENFORCE_LIFECYCLE_VALIDATION"] = "false"
        get_settings.cache_clear()


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


def test_policy_get_and_admin_update(client):
    assert client.get("/api/v1/governance/validation/policy").status_code == 200
    op = _token(client, "operator", "operator123")
    denied = client.put(
        "/api/v1/governance/validation/policy",
        headers={"Authorization": f"Bearer {op}"},
        json={"max_review_age_days": 90},
    )
    assert denied.status_code == 403
    admin = _token(client, "admin", "admin123")
    ok = client.put(
        "/api/v1/governance/validation/policy",
        headers={"Authorization": f"Bearer {admin}"},
        json={"max_review_age_days": 90},
    )
    assert ok.status_code == 200 and ok.json()["max_review_age_days"] == 90


def test_check_endpoint(client):
    resp = client.post(
        "/api/v1/governance/validation/check",
        json={"meta": {"name": "bare"}, "target": "web-prod-01"},
    )
    assert resp.status_code == 200 and resp.json()["ok"] is False


def test_review_status_dashboard(client):
    resp = client.get("/api/v1/governance/validation/review-status")
    assert resp.status_code == 200 and "fresh" in resp.json()
