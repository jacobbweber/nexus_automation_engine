"""ChangeService — open/close change records and evaluate change-control policy for a run."""

from __future__ import annotations

from datetime import UTC, datetime

from app.contexts.change_management.domain.models import (
    ChangeControlPolicy,
    ChangeRecord,
    ChangeState,
    ChangeTemplate,
    Risk,
)
from app.contexts.change_management.infrastructure.repository import ChangeRepository
from app.shared_kernel.errors import ConflictError, NotFoundError
from app.shared_kernel.ids import new_id

_CHG_BASE = 1000


def _now() -> datetime:
    return datetime.now(UTC)


class ChangeService:
    def __init__(self, repository: ChangeRepository | None = None) -> None:
        self.repo = repository or ChangeRepository()

    # templates -------------------------------------------------------------------------------

    def create_template(self, template: ChangeTemplate) -> ChangeTemplate:
        return self.repo.upsert_template(template)

    def list_templates(self) -> list[ChangeTemplate]:
        return self.repo.list_templates()

    def get_template(self, tid: str) -> ChangeTemplate:
        t = self.repo.get_template(tid)
        if t is None:
            raise NotFoundError(f"Change template {tid} not found")
        return t

    # policies --------------------------------------------------------------------------------

    def set_policy(self, policy: ChangeControlPolicy) -> ChangeControlPolicy:
        return self.repo.upsert_policy(policy)

    def get_policy(self, resource_type: str, resource_id: str) -> ChangeControlPolicy | None:
        return self.repo.get_policy(resource_type, resource_id)

    # records ---------------------------------------------------------------------------------

    def list_records(self) -> list[ChangeRecord]:
        return self.repo.list_records()

    def get_record(self, number: str) -> ChangeRecord:
        rec = self.repo.get_record(number)
        if rec is None:
            raise NotFoundError(f"Change {number} not found")
        return rec

    def _next_number(self) -> str:
        return f"CHG{_CHG_BASE + self.repo.count_records() + 1:07d}"

    def open_change(
        self,
        *,
        resource_type: str,
        resource_id: str,
        initiated_by: str,
        template_id: str | None = None,
        description: str = "",
    ) -> ChangeRecord:
        template = self.repo.get_template(template_id) if template_id else None
        risk = template.risk if template else Risk.LOW
        cab = template.cab_required if template else False
        # Standard (non-CAB) changes auto-approve; CAB-required changes await assessment.
        state = ChangeState.ASSESS if cab else ChangeState.APPROVED
        record = ChangeRecord(
            number=self._next_number(),
            template_id=template_id,
            state=state,
            short_description=description
            or (template.short_description if template else "")
            or f"Automated change for {resource_type} {resource_id}",
            risk=risk,
            assignment_group=template.assignment_group if template else "Automation",
            cab_required=cab,
            initiated_by=initiated_by,
            resource_type=resource_type,
            resource_id=resource_id,
            created_at=_now(),
        )
        self.repo.save_record(record)
        return record

    def close_change(self, number: str, *, success: bool) -> ChangeRecord:
        rec = self.get_record(number)
        rec.state = ChangeState.CLOSED
        rec.closed_at = _now()
        rec.close_code = "successful" if success else "failed"
        self.repo.save_record(rec)
        return rec

    def evaluate_for_execution(
        self, *, resource_type: str, resource_id: str, initiated_by: str, live: bool
    ) -> str | None:
        """Apply change-control policy before a run. Returns a change number, or None.

        Raises ConflictError if policy requires an approved change but the opened change is not
        approved (e.g. a CAB-required high-risk change awaiting assessment).
        """
        policy = self.repo.get_policy(resource_type, resource_id)
        if policy is None or not policy.auto_change_control:
            return None
        record = self.open_change(
            resource_type=resource_type,
            resource_id=resource_id,
            initiated_by=initiated_by,
            template_id=policy.change_template_id,
        )
        if live and policy.require_approved_change and record.state != ChangeState.APPROVED:
            raise ConflictError(
                f"{record.number} requires CAB approval before live execution "
                f"(currently {record.state})"
            )
        return record.number


def seed_change_management(repo: ChangeRepository | None = None) -> int:
    """Seed a couple of standard change templates."""
    repo = repo or ChangeRepository()
    if repo.count_templates() > 0:
        return 0
    repo.upsert_template(
        ChangeTemplate(
            id=new_id("chgtpl"),
            name="Standard — Low Risk Automation",
            short_description="Pre-approved standard change for routine automation",
            assignment_group="Automation",
            category="Standard",
            risk=Risk.LOW,
            cab_required=False,
        )
    )
    repo.upsert_template(
        ChangeTemplate(
            id=new_id("chgtpl"),
            name="Normal — Production Mutation (CAB)",
            short_description="Production-affecting change requiring CAB approval",
            assignment_group="Change Advisory Board",
            category="Normal",
            risk=Risk.HIGH,
            cab_required=True,
        )
    )
    return 2
