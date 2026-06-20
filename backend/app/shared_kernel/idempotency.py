"""Idempotency classification — a small cross-context primitive (shared kernel).

The v4.0 mandate is that all automation is idempotent and re-runnable. We make that a *contract*:
every connector action and catalog building block declares an idempotency class, and a
deterministic check flags any mutating, non-idempotent block. See vision §3 / ADR-0010.
"""

from __future__ import annotations

from enum import StrEnum


class IdempotencyClass(StrEnum):
    IDEMPOTENT = "idempotent"  # converges to desired state; safe to re-run
    CHECK_ONLY = "check_only"  # reads / plans; never mutates
    NON_IDEMPOTENT = "non_idempotent"  # mutates and is not safe to blindly re-run — must be guarded


# Name heuristics used to infer a class when one isn't declared explicitly (seeding aid).
_CHECK_ONLY_HINTS = ("plan", "lookup", "discover", "validate", "status", "get", "list", "read")
_NON_IDEMPOTENT_HINTS = ("delete", "destroy", "eradicate", "decommission", "remove", "wipe")


def infer_idempotency(action: str) -> IdempotencyClass:
    """Best-effort class from an action name. Destructive verbs win, then read/plan verbs."""
    a = (action or "").lower()
    if any(h in a for h in _NON_IDEMPOTENT_HINTS):
        return IdempotencyClass.NON_IDEMPOTENT
    if any(h in a for h in _CHECK_ONLY_HINTS):
        return IdempotencyClass.CHECK_ONLY
    return IdempotencyClass.IDEMPOTENT


def is_flagged(cls: IdempotencyClass) -> bool:
    """A non-idempotent (mutating) block is flagged — it cannot be safely re-run for compliance."""
    return cls == IdempotencyClass.NON_IDEMPOTENT
