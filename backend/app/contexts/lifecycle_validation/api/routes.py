"""Lifecycle validation routes: policy (admin-editable), check, and review dashboard."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.contexts.automation_catalog.application.service import CatalogService
from app.contexts.identity_access.api.deps import require_role
from app.contexts.identity_access.domain.models import GlobalRole, UserContext
from app.contexts.lifecycle_validation.application.service import ValidationService
from app.contexts.lifecycle_validation.domain.models import (
    AutomationMeta,
    ValidationPolicy,
    ValidationResult,
)

router = APIRouter(prefix="/governance/validation", tags=["lifecycle-validation"])


@router.get("/policy", response_model=ValidationPolicy)
def get_policy() -> ValidationPolicy:
    return ValidationService().get_policy()


@router.put("/policy", response_model=ValidationPolicy)
def update_policy(
    policy: ValidationPolicy, admin: UserContext = Depends(require_role(GlobalRole.ADMIN))
) -> ValidationPolicy:
    policy.updated_by = admin.username
    return ValidationService().update_policy(policy)


class CheckRequest(BaseModel):
    meta: AutomationMeta
    target: str | None = None


@router.post("/check", response_model=ValidationResult)
async def check(body: CheckRequest) -> ValidationResult:
    return await ValidationService().validate_for_execution(body.meta, body.target)


class ReviewBucket(BaseModel):
    fresh: int = 0
    stale: int = 0
    never_reviewed: int = 0
    total: int = 0
    oldest: list[dict] = []


@router.get("/review-status", response_model=ReviewBucket)
def review_status() -> ReviewBucket:
    """Pruning & review dashboard: break automations down by review freshness."""
    policy = ValidationService().get_policy()
    cutoff = datetime.now(UTC) - timedelta(days=policy.max_review_age_days)
    templates = CatalogService().list_all()  # approved building blocks
    bucket = ReviewBucket(total=len(templates))
    dated = []
    for t in templates:
        lr = t.last_reviewed
        if lr is None:
            bucket.never_reviewed += 1
            continue
        lr_aware = lr if lr.tzinfo else lr.replace(tzinfo=UTC)
        dated.append((lr_aware, t))
        if lr_aware < cutoff:
            bucket.stale += 1
        else:
            bucket.fresh += 1
    dated.sort(key=lambda x: x[0])
    bucket.oldest = [
        {"id": t.id, "name": t.name, "last_reviewed": lr.isoformat(), "vendor": t.vendor}
        for lr, t in dated[:10]
    ]
    return bucket
