"""Seed example pinning rules that demonstrate the guarantee model. Idempotent."""

from __future__ import annotations

from app.contexts.determinism.domain.models import (
    Enforcement,
    PinningRule,
    Selector,
    Trigger,
)
from app.contexts.determinism.infrastructure.repository import PinningRuleRepository


def _rules() -> list[PinningRule]:
    return [
        PinningRule(
            id="pin_vm_validate",
            name="Every VM: tag + CMDB validation",
            priority=10,
            selector=Selector(ci_type="vm"),
            workflow="CMDB CI Validation Sweep",
            trigger=Trigger.ON_SCHEDULE,
            enforcement=Enforcement.ASSERT,
            description="Continuously assert every VM is tag/CMDB-compliant.",
        ),
        PinningRule(
            id="pin_drtier0_zerto",
            name="DR-Tier-0 VM: guaranteed Zerto DR VPG",
            priority=20,
            selector=Selector(ci_type="vm", tag_predicates={"DR-Tier": "0"}),
            workflow="Zerto DR VPG",
            trigger=Trigger.ON_CHANGE,
            enforcement=Enforcement.ENFORCE,
            description="Any Tier-0 VM must have a Zerto VPG; enforce via review.",
        ),
    ]


def seed_pinning_rules(repo: PinningRuleRepository | None = None) -> int:
    repo = repo or PinningRuleRepository()
    if repo.count() > 0:
        return 0
    created = 0
    for rule in _rules():
        repo.upsert(rule)
        created += 1
    return created
