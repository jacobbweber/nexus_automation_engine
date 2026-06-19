"""ValidationService — the single gate consulted at build and pre-launch.

Resolves the target CI via the ServiceNow CMDB connector port (vendor-neutral) and applies the
admin-editable policy. Raising ``ValidationRejected`` blocks an execution.
"""

from __future__ import annotations

from app.contexts.connectors.domain.models import ConnectorKind, DiscoveryQuery
from app.contexts.connectors.infrastructure.registry import get_registry
from app.contexts.lifecycle_validation.domain.models import (
    AutomationMeta,
    ValidationPolicy,
    ValidationResult,
    check_cmdb,
    check_metadata,
)
from app.contexts.lifecycle_validation.infrastructure.repository import (
    ValidationPolicyRepository,
)
from app.shared_kernel.errors import NexusError


class ValidationRejected(NexusError):
    """Lifecycle validation rejected the automation. 422."""

    status_code = 422


class ValidationService:
    def __init__(self, repository: ValidationPolicyRepository | None = None) -> None:
        self.repo = repository or ValidationPolicyRepository()

    def get_policy(self) -> ValidationPolicy:
        return self.repo.get()

    def update_policy(self, policy: ValidationPolicy) -> ValidationPolicy:
        return self.repo.save(policy)

    def validate_for_build(self, meta: AutomationMeta) -> ValidationResult:
        reasons = check_metadata(meta, self.repo.get())
        return ValidationResult(ok=not reasons, stage="build", reasons=reasons)

    async def _resolve_ci(self, target: str | None) -> dict | None:
        if not target:
            return None
        resources = (
            await get_registry()
            .discovery(ConnectorKind.SERVICENOW)
            .discover(DiscoveryQuery(source="cmdb_ci_server", filters={"name": target}))
        )
        return dict(resources[0].attributes) if resources else None

    async def validate_for_execution(
        self, meta: AutomationMeta, target: str | None
    ) -> ValidationResult:
        policy = self.repo.get()
        reasons = check_metadata(meta, policy)
        ci = await self._resolve_ci(target)
        reasons += check_cmdb(meta, ci, policy)
        return ValidationResult(ok=not reasons, stage="prelaunch", reasons=reasons)

    async def enforce_for_execution(self, meta: AutomationMeta, target: str | None) -> None:
        result = await self.validate_for_execution(meta, target)
        if not result.ok:
            raise ValidationRejected(
                "Lifecycle validation rejected this run: " + "; ".join(result.reasons)
            )


def seed_default_policy(repo: ValidationPolicyRepository | None = None) -> None:
    repo = repo or ValidationPolicyRepository()
    # Persist the default policy row so admins have something to edit out of the box.
    repo.save(ValidationPolicy())
