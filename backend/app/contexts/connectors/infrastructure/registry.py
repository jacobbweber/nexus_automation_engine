"""Connector registry — resolves a connector kind to its adapter instance.

The rest of the system asks the registry for a port (e.g. "the execution connector for
``ansible``") and never constructs adapters directly. Today it is populated with the simulation
adapters; swapping in real adapters is a registry change, nothing else.
"""

from __future__ import annotations

from app.contexts.connectors.domain.models import Capabilities, ConnectorKind
from app.contexts.connectors.domain.ports import (
    ApprovalPort,
    ConnectorError,
    DiscoveryPort,
    ExecutionConnector,
    SecretLeasePort,
    TelemetryPort,
)
from app.contexts.connectors.infrastructure.simulation.ansible import AnsibleSimConnector
from app.contexts.connectors.infrastructure.simulation.cyberark import CyberArkSimConnector
from app.contexts.connectors.infrastructure.simulation.dynatrace import DynatraceSimConnector
from app.contexts.connectors.infrastructure.simulation.script import ScriptSimConnector
from app.contexts.connectors.infrastructure.simulation.servicenow import ServiceNowSimConnector
from app.contexts.connectors.infrastructure.simulation.terraform import TerraformSimConnector


class ConnectorRegistry:
    def __init__(self) -> None:
        self._by_kind: dict[ConnectorKind, object] = {}

    def register(self, kind: ConnectorKind, adapter: object) -> None:
        self._by_kind[kind] = adapter

    def _require(self, kind: ConnectorKind) -> object:
        adapter = self._by_kind.get(kind)
        if adapter is None:
            raise ConnectorError(f"No connector registered for {kind.value!r}")
        return adapter

    def execution(self, kind: ConnectorKind) -> ExecutionConnector:
        adapter = self._require(kind)
        if not isinstance(adapter, ExecutionConnector):
            raise ConnectorError(f"Connector {kind.value!r} is not an execution connector")
        return adapter

    def discovery(self, kind: ConnectorKind) -> DiscoveryPort:
        adapter = self._require(kind)
        if not isinstance(adapter, DiscoveryPort):
            raise ConnectorError(f"Connector {kind.value!r} does not support discovery")
        return adapter

    def secret_lease(self, kind: ConnectorKind) -> SecretLeasePort:
        adapter = self._require(kind)
        if not isinstance(adapter, SecretLeasePort):
            raise ConnectorError(f"Connector {kind.value!r} does not support secret leasing")
        return adapter

    def approval(self, kind: ConnectorKind) -> ApprovalPort:
        adapter = self._require(kind)
        if not isinstance(adapter, ApprovalPort):
            raise ConnectorError(f"Connector {kind.value!r} does not support approval validation")
        return adapter

    def telemetry(self, kind: ConnectorKind) -> TelemetryPort:
        adapter = self._require(kind)
        if not isinstance(adapter, TelemetryPort):
            raise ConnectorError(f"Connector {kind.value!r} does not support telemetry")
        return adapter

    def capabilities(self, kind: ConnectorKind) -> Capabilities:
        adapter = self._require(kind)
        return adapter.capabilities()  # type: ignore[attr-defined]

    def all_capabilities(self) -> list[Capabilities]:
        return [a.capabilities() for a in self._by_kind.values()]  # type: ignore[attr-defined]


def build_simulation_registry() -> ConnectorRegistry:
    registry = ConnectorRegistry()
    registry.register(ConnectorKind.ANSIBLE, AnsibleSimConnector())
    registry.register(ConnectorKind.TERRAFORM, TerraformSimConnector())
    registry.register(ConnectorKind.SCRIPT, ScriptSimConnector())
    registry.register(ConnectorKind.SERVICENOW, ServiceNowSimConnector())
    registry.register(ConnectorKind.CYBERARK, CyberArkSimConnector())
    registry.register(ConnectorKind.DYNATRACE, DynatraceSimConnector())
    return registry


_registry: ConnectorRegistry | None = None


def get_registry() -> ConnectorRegistry:
    """Process-wide connector registry (simulation adapters pre-1.0)."""
    global _registry
    if _registry is None:
        _registry = build_simulation_registry()
    return _registry
