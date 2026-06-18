"""Connector ports — the stable interfaces the rest of the system depends on.

Concrete adapters (simulation today, real backends later) implement these. Keeping them as
``Protocol`` types means adapters don't need to import a base class, and contract tests can
verify any object satisfies the shape.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from app.contexts.connectors.domain.models import (
    Capabilities,
    ChangeValidation,
    CredentialLease,
    DiscoveryQuery,
    ExecutionRequest,
    LogEvent,
    Resource,
    SecretRequest,
    TelemetrySeries,
)
from app.shared_kernel.errors import NexusError


class ConnectorError(NexusError):
    """A backend operation failed. The execution engine maps this to a FAILED run."""

    status_code = 502


@runtime_checkable
class ExecutionConnector(Protocol):
    """Runs work and streams logs (ansible / terraform / script)."""

    def capabilities(self) -> Capabilities: ...

    def execute(self, request: ExecutionRequest) -> AsyncIterator[LogEvent]:
        """Async-iterate log events as the work runs. Raise ConnectorError on failure."""
        ...


@runtime_checkable
class DiscoveryPort(Protocol):
    """Reads inventory / records from a system of record (e.g. ServiceNow CMDB)."""

    def capabilities(self) -> Capabilities: ...

    async def discover(self, query: DiscoveryQuery) -> list[Resource]: ...


@runtime_checkable
class SecretLeasePort(Protocol):
    """Leases short-lived credentials (e.g. CyberArk)."""

    def capabilities(self) -> Capabilities: ...

    async def lease(self, request: SecretRequest) -> CredentialLease: ...


@runtime_checkable
class ApprovalPort(Protocol):
    """Validates a change/request is approved before a mutating run (e.g. ServiceNow RITM)."""

    def capabilities(self) -> Capabilities: ...

    async def validate(
        self, reference: str, required_state: str = "approved"
    ) -> ChangeValidation: ...


@runtime_checkable
class TelemetryPort(Protocol):
    """Provides correlated metrics/events for a run window (e.g. Dynatrace)."""

    def capabilities(self) -> Capabilities: ...

    async def series(self, entity: str, seconds: int) -> TelemetrySeries: ...
