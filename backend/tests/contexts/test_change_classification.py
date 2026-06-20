"""Deterministic change classification + reviewer-level policy (story 26.2)."""

from __future__ import annotations

from app.contexts.review.domain.classification import (
    ChangeClass,
    ChangeContext,
    ReviewerLevel,
    ReviewPolicy,
    assess,
    classify,
    required_level,
    requires_approval,
)
from app.shared_kernel.idempotency import IdempotencyClass


def test_low_risk_nonprod_idempotent_is_standard():
    ctx = ChangeContext(
        risk="low", prod=False, blast_radius=1, idempotency=IdempotencyClass.IDEMPOTENT
    )
    assert classify(ctx) == ChangeClass.STANDARD
    assert not requires_approval(ctx)


def test_check_only_nonprod_is_standard():
    ctx = ChangeContext(risk="low", prod=False, idempotency=IdempotencyClass.CHECK_ONLY)
    assert classify(ctx) == ChangeClass.STANDARD


def test_production_is_normal_and_needs_review():
    ctx = ChangeContext(risk="low", prod=True, idempotency=IdempotencyClass.IDEMPOTENT)
    assert classify(ctx) == ChangeClass.NORMAL
    assert requires_approval(ctx)
    assert required_level(ctx) == ReviewerLevel.TEAM_LEAD


def test_high_risk_escalates_to_executive():
    ctx = ChangeContext(
        risk="high", prod=True, blast_radius=2, idempotency=IdempotencyClass.NON_IDEMPOTENT
    )
    assert required_level(ctx) == ReviewerLevel.EXECUTIVE


def test_large_blast_radius_escalates_to_executive():
    ctx = ChangeContext(risk="low", prod=True, blast_radius=6)
    assert required_level(ctx) == ReviewerLevel.EXECUTIVE


def test_emergency_flag():
    ctx = ChangeContext(risk="medium", emergency=True)
    assert classify(ctx) == ChangeClass.EMERGENCY
    assert required_level(ctx) == ReviewerLevel.EXECUTIVE  # emergency_level default


def test_assess_returns_reasons():
    ctx = ChangeContext(
        risk="critical", prod=True, blast_radius=8, idempotency=IdempotencyClass.NON_IDEMPOTENT
    )
    result = assess(ctx)
    assert result.requires_approval
    assert result.required_level == ReviewerLevel.EXECUTIVE
    assert any("production" in r for r in result.reasons)
    assert any("non-idempotent" in r for r in result.reasons)


def test_policy_is_tunable():
    ctx = ChangeContext(risk="low", prod=True)
    strict = ReviewPolicy(normal_level=ReviewerLevel.EXECUTIVE)
    assert required_level(ctx, strict) == ReviewerLevel.EXECUTIVE
