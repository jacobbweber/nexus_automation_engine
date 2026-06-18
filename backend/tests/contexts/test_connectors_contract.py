"""Contract tests: every registered adapter satisfies its declared port + capabilities shape."""

from __future__ import annotations

from app.contexts.connectors.domain.models import ConnectorCategory, ConnectorKind
from app.contexts.connectors.domain.ports import (
    ApprovalPort,
    DiscoveryPort,
    ExecutionConnector,
    SecretLeasePort,
    TelemetryPort,
)
from app.contexts.connectors.infrastructure.registry import build_simulation_registry

EXECUTION_KINDS = {ConnectorKind.ANSIBLE, ConnectorKind.TERRAFORM, ConnectorKind.SCRIPT}


def test_execution_connectors_satisfy_port():
    registry = build_simulation_registry()
    for kind in EXECUTION_KINDS:
        conn = registry.execution(kind)
        assert isinstance(conn, ExecutionConnector)
        caps = conn.capabilities()
        assert caps.kind == kind
        assert caps.category == ConnectorCategory.EXECUTION
        assert caps.actions, f"{kind} should expose at least one action"


def test_servicenow_satisfies_discovery_and_approval():
    registry = build_simulation_registry()
    assert isinstance(registry.discovery(ConnectorKind.SERVICENOW), DiscoveryPort)
    assert isinstance(registry.approval(ConnectorKind.SERVICENOW), ApprovalPort)


def test_cyberark_satisfies_secret_lease():
    registry = build_simulation_registry()
    assert isinstance(registry.secret_lease(ConnectorKind.CYBERARK), SecretLeasePort)


def test_dynatrace_satisfies_telemetry():
    registry = build_simulation_registry()
    assert isinstance(registry.telemetry(ConnectorKind.DYNATRACE), TelemetryPort)


def test_all_capabilities_present():
    registry = build_simulation_registry()
    caps = registry.all_capabilities()
    kinds = {c.kind for c in caps}
    assert kinds == set(ConnectorKind)


def test_wrong_port_request_raises():
    from app.contexts.connectors.domain.ports import ConnectorError

    registry = build_simulation_registry()
    # Ansible is not a discovery connector.
    try:
        registry.discovery(ConnectorKind.ANSIBLE)
        raise AssertionError("expected ConnectorError")
    except ConnectorError:
        pass
