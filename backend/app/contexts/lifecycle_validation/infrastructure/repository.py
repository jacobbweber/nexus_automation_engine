"""Validation policy repository (singleton row)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from app.contexts.lifecycle_validation.domain.models import ValidationPolicy
from app.contexts.lifecycle_validation.infrastructure.orm import ValidationPolicyRow
from app.platform.database import get_sessionmaker

_SINGLETON = "default"


class ValidationPolicyRepository:
    def get(self) -> ValidationPolicy:
        with get_sessionmaker()() as s:
            row = s.get(ValidationPolicyRow, _SINGLETON)
            if row is None:
                return ValidationPolicy()  # defaults until saved
            return ValidationPolicy(
                id=row.id,
                required_fields=json.loads(row.required_fields_json or "[]"),
                max_review_age_days=row.max_review_age_days,
                enforce_cmdb_consistency=row.enforce_cmdb_consistency,
                reject_retired=row.reject_retired,
                reject_unknown_ci=row.reject_unknown_ci,
                block_destructive_on_cluster=row.block_destructive_on_cluster,
                require_healthy_ci=row.require_healthy_ci,
                min_health_score=row.min_health_score,
                updated_by=row.updated_by,
                updated_at=row.updated_at
                if row.updated_at.tzinfo
                else row.updated_at.replace(tzinfo=UTC),
            )

    def save(self, policy: ValidationPolicy) -> ValidationPolicy:
        with get_sessionmaker()() as s:
            row = s.get(ValidationPolicyRow, _SINGLETON) or ValidationPolicyRow(id=_SINGLETON)
            row.required_fields_json = json.dumps(policy.required_fields)
            row.max_review_age_days = policy.max_review_age_days
            row.enforce_cmdb_consistency = policy.enforce_cmdb_consistency
            row.reject_retired = policy.reject_retired
            row.reject_unknown_ci = policy.reject_unknown_ci
            row.block_destructive_on_cluster = policy.block_destructive_on_cluster
            row.require_healthy_ci = policy.require_healthy_ci
            row.min_health_score = policy.min_health_score
            row.updated_by = policy.updated_by
            row.updated_at = datetime.now(UTC)
            s.add(row)
            s.commit()
        return self.get()
