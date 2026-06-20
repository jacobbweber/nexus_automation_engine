"""Lifecycle validation domain models + pure validation rules."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field

# Actions considered destructive (extra scrutiny against CMDB lifecycle/cluster membership).
DESTRUCTIVE_ACTIONS = {"delete_datastore", "eradicate_volume", "destroy", "delete", "decommission"}
DESTRUCTIVE_RISKS = {"critical"}


class ValidationPolicy(BaseModel):
    """The single, admin-editable gate every automation is validated against."""

    id: str = "default"
    required_fields: list[str] = Field(
        default_factory=lambda: ["authored_by", "approved_date", "last_reviewed", "ci_type"]
    )
    max_review_age_days: int = 180
    enforce_cmdb_consistency: bool = True
    reject_retired: bool = True
    reject_unknown_ci: bool = True
    block_destructive_on_cluster: bool = True
    # CMDB schema/lineage health gating (M24.5): when enabled, a target CI must score at least
    # min_health_score against its CI type schema + lineage (see the `cmdb` context).
    require_healthy_ci: bool = False
    min_health_score: int = 70
    updated_by: str = "system"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AutomationMeta(BaseModel):
    """The metadata an automation must carry to be 'valid & approved'."""

    name: str
    action: str = ""
    risk: str = "low"
    authored_by: str | None = None
    approved_date: datetime | None = None
    last_updated: datetime | None = None
    last_reviewed: datetime | None = None
    ci_type: str | None = None
    ci_heritage: str = ""


class ValidationResult(BaseModel):
    ok: bool
    stage: str  # "build" | "prelaunch"
    reasons: list[str] = Field(default_factory=list)


def is_destructive(meta: AutomationMeta) -> bool:
    return meta.action in DESTRUCTIVE_ACTIONS or meta.risk in DESTRUCTIVE_RISKS


def check_metadata(meta: AutomationMeta, policy: ValidationPolicy) -> list[str]:
    """Pure metadata-completeness + freshness check. Returns a list of failure reasons."""
    reasons: list[str] = []
    values = meta.model_dump()
    for field in policy.required_fields:
        if not values.get(field):
            reasons.append(f"missing required metadata: {field}")
    if meta.last_reviewed is not None:
        age = datetime.now(UTC) - _aware(meta.last_reviewed)
        if age > timedelta(days=policy.max_review_age_days):
            reasons.append(f"review is stale ({age.days}d > {policy.max_review_age_days}d max)")
    return reasons


def check_cmdb(meta: AutomationMeta, ci: dict | None, policy: ValidationPolicy) -> list[str]:
    """Pure CMDB-consistency check given the resolved CI record (or None if not found)."""
    if not policy.enforce_cmdb_consistency:
        return []
    reasons: list[str] = []
    if ci is None:
        if policy.reject_unknown_ci:
            reasons.append("target CI not found in CMDB")
        return reasons
    if policy.reject_retired and str(ci.get("lifecycle_state")) == "retired":
        reasons.append(f"target CI lifecycle is 'retired' ({ci.get('name')})")
    if meta.ci_type and ci.get("ci_type") and meta.ci_type != ci.get("ci_type"):
        reasons.append(
            f"CI type contradiction: automation declares '{meta.ci_type}' but CMDB says "
            f"'{ci.get('ci_type')}'"
        )
    if policy.block_destructive_on_cluster and is_destructive(meta) and ci.get("cluster_member"):
        reasons.append(
            f"destructive action on cluster member '{ci.get('name')}' "
            f"(cluster {ci.get('cluster')}) is blocked"
        )
    return reasons


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
