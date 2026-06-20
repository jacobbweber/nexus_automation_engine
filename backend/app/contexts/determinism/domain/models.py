"""Pinning rule domain models + the pure matcher.

A PinningRule binds a *selector* (CI type + tag/field predicates) to a *guaranteed workflow*, a
*trigger*, and an *enforcement mode*. The matcher decides which CIs a rule governs. Pure, no AI.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Trigger(StrEnum):
    ON_CREATE = "on_create"
    ON_CHANGE = "on_change"
    ON_SCHEDULE = "on_schedule"
    ON_DEMAND = "on_demand"


class Enforcement(StrEnum):
    ASSERT = "assert"  # run in compliance mode, report drift (no mutation)
    ENFORCE = "enforce"  # reconcile, routed through review (M26)
    GATE = "gate"  # block the triggering change until the pinned check passes


class Selector(BaseModel):
    """Predicates over a CI. All present predicates must match (logical AND)."""

    ci_type: str | None = None
    tag_predicates: dict[str, str] = Field(default_factory=dict)  # tag name -> required value
    field_predicates: dict[str, str] = Field(default_factory=dict)  # field name -> required value


class PinningRule(BaseModel):
    id: str
    name: str
    enabled: bool = True
    priority: int = 100  # lower runs first
    selector: Selector = Field(default_factory=Selector)
    workflow: str  # workflow id or name of the guaranteed workflow
    trigger: Trigger = Trigger.ON_SCHEDULE
    enforcement: Enforcement = Enforcement.ASSERT
    description: str = ""


def matches(rule: PinningRule, ci: dict[str, object]) -> bool:
    """True if the CI satisfies the rule's selector."""
    sel = rule.selector
    if sel.ci_type and str(ci.get("ci_type")) != sel.ci_type:
        return False
    _tags = ci.get("tags")
    tags: dict[str, object] = _tags if isinstance(_tags, dict) else {}
    for k, v in sel.tag_predicates.items():
        if str(tags.get(k)) != v:
            return False
    for k, v in sel.field_predicates.items():
        if str(ci.get(k)) != v:
            return False
    return True


def validate_rule(rule: PinningRule) -> list[str]:
    """Deterministically validate a pinning rule. Returns human-readable errors (empty = OK)."""
    errors: list[str] = []
    if not rule.name.strip():
        errors.append("rule 'name' must be non-empty")
    if not rule.workflow.strip():
        errors.append("rule must reference a guaranteed 'workflow'")
    sel = rule.selector
    if not sel.ci_type and not sel.tag_predicates and not sel.field_predicates:
        errors.append("selector must constrain at least one of ci_type / tags / fields")
    return errors


def match_rules(rules: list[PinningRule], ci: dict[str, object]) -> list[PinningRule]:
    """Enabled rules matching the CI, ordered by priority then name (deterministic)."""
    hits = [r for r in rules if r.enabled and matches(r, ci)]
    return sorted(hits, key=lambda r: (r.priority, r.name))
