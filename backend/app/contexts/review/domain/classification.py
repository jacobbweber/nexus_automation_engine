"""Deterministic change classification + the review policy that maps a class to reviewer levels.

A run is classified standard | normal | emergency from its risk, blast radius, target environment,
and idempotency — then a policy says who must approve. No AI (ADR-0008): pure rules.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.shared_kernel.idempotency import IdempotencyClass


class ChangeClass(StrEnum):
    STANDARD = "standard"  # pre-approved, low-risk — no human gate
    NORMAL = "normal"  # needs review/approval
    EMERGENCY = "emergency"  # expedited, but still reviewed (post-hoc allowed)


class ReviewerLevel(StrEnum):
    NONE = "none"
    TEAM_LEAD = "team_lead"
    EXECUTIVE = "executive"


class ChangeContext(BaseModel):
    """The signals classification consults."""

    risk: str = "low"  # low | medium | high | critical
    blast_radius: int = 0  # number of CIs the run would touch (M24 impact)
    prod: bool = False  # targets a production environment
    idempotency: IdempotencyClass = IdempotencyClass.IDEMPOTENT
    emergency: bool = False  # operator-flagged break-glass


class ReviewPolicy(BaseModel):
    """Maps a change class to the reviewer level required. Admin-tunable (defaults shown)."""

    id: str = "default"
    standard_level: ReviewerLevel = ReviewerLevel.NONE
    normal_level: ReviewerLevel = ReviewerLevel.TEAM_LEAD
    emergency_level: ReviewerLevel = ReviewerLevel.EXECUTIVE
    # Any run at/above this risk escalates to executive regardless of class.
    exec_risk_threshold: str = "high"
    updated_by: str = "system"


_RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def classify(ctx: ChangeContext) -> ChangeClass:
    """Deterministically classify a change from its context."""
    if ctx.emergency:
        return ChangeClass.EMERGENCY
    risk = _RISK_ORDER.get(ctx.risk.lower(), 0)
    non_idempotent = ctx.idempotency == IdempotencyClass.NON_IDEMPOTENT
    # standard = safe, low-risk, small, non-prod, re-runnable
    if (
        risk == 0
        and not ctx.prod
        and not non_idempotent
        and ctx.blast_radius <= 1
        and ctx.idempotency != IdempotencyClass.NON_IDEMPOTENT
    ):
        return ChangeClass.STANDARD
    # check-only reads are always standard
    if ctx.idempotency == IdempotencyClass.CHECK_ONLY and not ctx.prod:
        return ChangeClass.STANDARD
    return ChangeClass.NORMAL


def required_level(ctx: ChangeContext, policy: ReviewPolicy | None = None) -> ReviewerLevel:
    """The reviewer level required for this change, given the policy."""
    policy = policy or ReviewPolicy()
    cls = classify(ctx)
    level = {
        ChangeClass.STANDARD: policy.standard_level,
        ChangeClass.NORMAL: policy.normal_level,
        ChangeClass.EMERGENCY: policy.emergency_level,
    }[cls]
    # escalate to executive for high/critical risk or a large blast radius
    risk = _RISK_ORDER.get(ctx.risk.lower(), 0)
    if risk >= _RISK_ORDER.get(policy.exec_risk_threshold, 2) or ctx.blast_radius >= 5:
        return ReviewerLevel.EXECUTIVE
    return level


def requires_approval(ctx: ChangeContext, policy: ReviewPolicy | None = None) -> bool:
    return required_level(ctx, policy) != ReviewerLevel.NONE


class Classification(BaseModel):
    """The full classification result (returned by the API)."""

    change_class: ChangeClass
    required_level: ReviewerLevel
    requires_approval: bool
    reasons: list[str] = Field(default_factory=list)


def assess(ctx: ChangeContext, policy: ReviewPolicy | None = None) -> Classification:
    policy = policy or ReviewPolicy()
    cls = classify(ctx)
    level = required_level(ctx, policy)
    reasons: list[str] = []
    if ctx.emergency:
        reasons.append("operator-flagged emergency / break-glass")
    if ctx.prod:
        reasons.append("targets production")
    if ctx.idempotency == IdempotencyClass.NON_IDEMPOTENT:
        reasons.append("non-idempotent (mutating, not safe to blindly re-run)")
    if _RISK_ORDER.get(ctx.risk.lower(), 0) >= 2:
        reasons.append(f"{ctx.risk} risk")
    if ctx.blast_radius >= 5:
        reasons.append(f"large blast radius ({ctx.blast_radius} CIs)")
    return Classification(
        change_class=cls,
        required_level=level,
        requires_approval=level != ReviewerLevel.NONE,
        reasons=reasons,
    )
