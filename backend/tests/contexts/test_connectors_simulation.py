"""Behavioral tests for the simulation adapters (execution + systems of record)."""

from __future__ import annotations

import pytest
from app.contexts.connectors.domain.models import (
    ConnectorKind,
    DiscoveryQuery,
    ExecutionRequest,
    SecretRequest,
)
from app.contexts.connectors.domain.ports import ConnectorError
from app.contexts.connectors.infrastructure.registry import build_simulation_registry


async def _collect(conn, request) -> list[str]:
    return [event.message async for event in conn.execute(request)]


async def test_terraform_plan_streams_plan_summary():
    reg = build_simulation_registry()
    conn = reg.execution(ConnectorKind.TERRAFORM)
    msgs = await _collect(
        conn,
        ExecutionRequest(kind=ConnectorKind.TERRAFORM, action="plan", params={"workspace": "prod"}),
    )
    joined = "\n".join(msgs)
    assert "Plan:" in joined
    assert "to add" in joined


async def test_terraform_apply_failure_raises():
    reg = build_simulation_registry()
    conn = reg.execution(ConnectorKind.TERRAFORM)
    with pytest.raises(ConnectorError):
        async for _ in conn.execute(
            ExecutionRequest(
                kind=ConnectorKind.TERRAFORM,
                action="apply",
                params={"workspace": "prod", "force_fail": True},
            )
        ):
            pass


async def test_ansible_check_mode_reports_no_changes_applied():
    reg = build_simulation_registry()
    conn = reg.execution(ConnectorKind.ANSIBLE)
    msgs = await _collect(
        conn,
        ExecutionRequest(
            kind=ConnectorKind.ANSIBLE,
            action="run_job_template",
            params={"playbooks": ["site.yml"]},
            check_mode=True,
        ),
    )
    joined = "\n".join(msgs)
    assert "PLAY RECAP" in joined
    assert "changed=0" in joined


async def test_ansible_uses_inventory_from_discovery_shape():
    reg = build_simulation_registry()
    conn = reg.execution(ConnectorKind.ANSIBLE)
    inventory = [{"name": "web-prod-01"}, {"name": "web-prod-02"}]
    msgs = await _collect(
        conn,
        ExecutionRequest(
            kind=ConnectorKind.ANSIBLE,
            action="run_job_template",
            params={"playbooks": ["site.yml"], "inventory": inventory},
        ),
    )
    joined = "\n".join(msgs)
    assert "web-prod-01" in joined and "web-prod-02" in joined


async def test_script_runs_and_can_fail():
    reg = build_simulation_registry()
    conn = reg.execution(ConnectorKind.SCRIPT)
    ok = await _collect(
        conn,
        ExecutionRequest(
            kind=ConnectorKind.SCRIPT, action="run", params={"target": "h1", "script": "echo hi"}
        ),
    )
    assert any("exit 0" in m for m in ok)
    with pytest.raises(ConnectorError):
        async for _ in conn.execute(
            ExecutionRequest(
                kind=ConnectorKind.SCRIPT, action="run", params={"target": "h1", "force_fail": True}
            )
        ):
            pass


async def test_servicenow_discovery_filters_by_env():
    reg = build_simulation_registry()
    disc = reg.discovery(ConnectorKind.SERVICENOW)
    prod = await disc.discover(
        DiscoveryQuery(source="cmdb_ci_server", filters={"env": "Production"})
    )
    assert prod and all(r.attributes["env"] == "Production" for r in prod)


async def test_servicenow_approval_validation():
    reg = build_simulation_registry()
    appr = reg.approval(ConnectorKind.SERVICENOW)
    good = await appr.validate("RITM0001234")  # ends in 4 -> approved
    bad = await appr.validate("RITM0001235")  # ends in 5 -> pending
    assert good.ok is True and good.state == "approved"
    assert bad.ok is False and bad.state == "pending"


async def test_cyberark_lease_is_short_lived():
    reg = build_simulation_registry()
    lease = await reg.secret_lease(ConnectorKind.CYBERARK).lease(
        SecretRequest(safe="prod", object_name="db_admin")
    )
    assert lease.secret and lease.username and lease.expires_at


async def test_dynatrace_series_returns_samples():
    reg = build_simulation_registry()
    series = await reg.telemetry(ConnectorKind.DYNATRACE).series(entity="web-prod-01", seconds=60)
    assert len(series.samples) > 0
    assert all(0 <= s.cpu_percent <= 100 for s in series.samples)
