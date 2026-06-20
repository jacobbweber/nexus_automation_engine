"""Deterministic simulated compliance evaluation (M25.2).

Produces believable, *stable* drift for an ExecutionRequest without mutating — a single evaluator
rather than per-adapter code, since drift is simulated. The same request always yields the same
DriftReport (seeded by target+action), so compliance runs and sweeps are reproducible.
"""

from __future__ import annotations

import hashlib

from app.contexts.connectors.domain.models import (
    ComplianceState,
    DriftReport,
    ExecutionRequest,
    FieldDrift,
    ResourceDrift,
)
from app.shared_kernel.idempotency import IdempotencyClass, infer_idempotency

# Config fields we pretend each resource declares; a subset may drift.
_DESIRED: dict[str, str] = {
    "environment_tag": "Production",
    "owner_tag": "present",
    "patch_level": "current",
    "backup_enabled": "true",
    "config_baseline": "v2",
}
_OBSERVED_DRIFT: dict[str, str] = {
    "environment_tag": "(unset)",
    "owner_tag": "(missing)",
    "patch_level": "n-2",
    "backup_enabled": "false",
    "config_baseline": "v1",
}
_RECONCILE: dict[str, str] = {
    "environment_tag": "set tag environment=Production",
    "owner_tag": "set the owner tag",
    "patch_level": "apply pending patches",
    "backup_enabled": "enable backup policy",
    "config_baseline": "re-apply config baseline v2",
}


def _seed(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest(), 16)


def evaluate_compliance(request: ExecutionRequest) -> DriftReport:
    """Deterministically assess desired-vs-observed for a request. Never mutates."""
    target = str(request.params.get("target") or request.params.get("workspace") or "estate")
    action = request.action
    cls = infer_idempotency(action)

    fields_in_order = list(_DESIRED.keys())
    seed = _seed(target, action)

    # check-only actions are inherently compliant (they observe, never declare desired state).
    if cls == IdempotencyClass.CHECK_ONLY:
        return DriftReport(
            target=target,
            connector=str(request.kind),
            action=action,
            status=ComplianceState.COMPLIANT,
            drift_count=0,
            resources=[ResourceDrift(resource=target, state=ComplianceState.COMPLIANT)],
            summary=f"{target}: in compliance (read-only check).",
        )

    drifted: list[FieldDrift] = []
    for i, f in enumerate(fields_in_order):
        # deterministic: ~ every other field drifts based on the seed bit
        if (seed >> i) & 1:
            drifted.append(
                FieldDrift(
                    field=f,
                    desired=_DESIRED[f],
                    observed=_OBSERVED_DRIFT[f],
                    state=ComplianceState.DRIFTED,
                )
            )

    state = ComplianceState.DRIFTED if drifted else ComplianceState.COMPLIANT
    reconcile = "; ".join(_RECONCILE[fd.field] for fd in drifted) if drifted else ""
    resource = ResourceDrift(
        resource=target, state=state, fields=drifted, reconcile_action=reconcile
    )
    return DriftReport(
        target=target,
        connector=str(request.kind),
        action=action,
        status=state,
        drift_count=len(drifted),
        resources=[resource],
        summary=(
            f"{target}: {len(drifted)} field(s) drifted from desired state."
            if drifted
            else f"{target}: in compliance."
        ),
    )


def aggregate(reports: list[DriftReport], target: str = "workflow") -> DriftReport:
    """Roll up several reports (e.g. across a workflow's steps) into one."""
    resources: list[ResourceDrift] = []
    for r in reports:
        resources.extend(r.resources)
    drift_count = sum(r.drift_count for r in reports)
    status = ComplianceState.DRIFTED if drift_count else ComplianceState.COMPLIANT
    return DriftReport(
        target=target,
        connector="aggregate",
        action="compliance",
        status=status,
        drift_count=drift_count,
        resources=resources,
        summary=f"{drift_count} field(s) drifted across {len(reports)} step(s).",
    )
