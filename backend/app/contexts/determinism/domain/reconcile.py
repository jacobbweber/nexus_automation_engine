"""Pure reconciliation + coverage over pinning rules and CMDB CIs.

The reconciler turns rules + CIs into a deterministic *pinned-actions plan* (what is guaranteed to
happen, per CI × matching rule). Coverage answers "what is guaranteed about the estate, and where
does reality not match?" Both are pure — the application service supplies the CIs + a compliance fn.
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, Field

from app.contexts.determinism.domain.models import (
    Enforcement,
    PinningRule,
    Trigger,
    match_rules,
)


class PinnedAction(BaseModel):
    ci: str
    ci_type: str
    rule_id: str
    rule_name: str
    workflow: str
    enforcement: Enforcement
    trigger: Trigger
    note: str = ""


def _ci_name(ci: dict[str, object]) -> str:
    return str(ci.get("name") or ci.get("id") or "?")


def plan_actions(
    rules: list[PinningRule],
    cis: list[dict[str, object]],
    trigger: Trigger | None = None,
) -> list[PinnedAction]:
    """The deterministic plan: for each CI, each matching rule (optionally for one trigger)."""
    actions: list[PinnedAction] = []
    for ci in cis:
        for rule in match_rules(rules, ci):
            if trigger is not None and rule.trigger != trigger:
                continue
            note = {
                Enforcement.ASSERT: "assert compliance (no mutation)",
                Enforcement.ENFORCE: "reconcile via review-gated run",
                Enforcement.GATE: "block the change until the pinned check passes",
            }[rule.enforcement]
            actions.append(
                PinnedAction(
                    ci=_ci_name(ci),
                    ci_type=str(ci.get("ci_type", "")),
                    rule_id=rule.id,
                    rule_name=rule.name,
                    workflow=rule.workflow,
                    enforcement=rule.enforcement,
                    trigger=rule.trigger,
                    note=note,
                )
            )
    # stable ordering: by ci then rule
    actions.sort(key=lambda a: (a.ci, a.rule_id))
    return actions


class RuleCoverage(BaseModel):
    rule_id: str
    rule_name: str
    enforcement: Enforcement
    workflow: str
    workflow_exists: bool
    matched: int = 0
    compliant: int = 0
    drifted: int = 0
    unknown: int = 0


class Coverage(BaseModel):
    total_cis: int
    rules: list[RuleCoverage] = Field(default_factory=list)


def compute_coverage(
    rules: list[PinningRule],
    cis: list[dict[str, object]],
    *,
    workflow_exists: Callable[[str], bool],
    drift_of: Callable[[dict[str, object], PinningRule], str] | None = None,
) -> Coverage:
    """Per-rule coverage. ``drift_of`` (optional) gives drift state for assert rules."""
    out: list[RuleCoverage] = []
    for rule in rules:
        matched = [ci for ci in cis if _matches(rule, ci)]
        cov = RuleCoverage(
            rule_id=rule.id,
            rule_name=rule.name,
            enforcement=rule.enforcement,
            workflow=rule.workflow,
            workflow_exists=workflow_exists(rule.workflow),
            matched=len(matched),
        )
        if rule.enforcement == Enforcement.ASSERT and drift_of is not None:
            for ci in matched:
                state = drift_of(ci, rule)
                if state == "compliant":
                    cov.compliant += 1
                elif state == "drifted":
                    cov.drifted += 1
                else:
                    cov.unknown += 1
        out.append(cov)
    return Coverage(total_cis=len(cis), rules=out)


def _matches(rule: PinningRule, ci: dict[str, object]) -> bool:
    from app.contexts.determinism.domain.models import matches

    return rule.enabled and matches(rule, ci)
