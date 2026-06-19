"""Change management repository (sync SQLAlchemy)."""

from __future__ import annotations

import json

from sqlalchemy import func, select

from app.contexts.change_management.domain.models import (
    ChangeControlPolicy,
    ChangeRecord,
    ChangeState,
    ChangeTemplate,
    Risk,
)
from app.contexts.change_management.infrastructure.orm import (
    ChangePolicyRow,
    ChangeRecordRow,
    ChangeTemplateRow,
)
from app.platform.database import get_sessionmaker


def _to_template(r: ChangeTemplateRow) -> ChangeTemplate:
    return ChangeTemplate(
        id=r.id,
        name=r.name,
        short_description=r.short_description,
        assignment_group=r.assignment_group,
        category=r.category,
        risk=Risk(r.risk),
        impact=r.impact,
        cab_required=r.cab_required,
        extra_fields=json.loads(r.extra_fields_json or "{}"),
    )


def _to_policy(r: ChangePolicyRow) -> ChangeControlPolicy:
    return ChangeControlPolicy(
        id=r.id,
        resource_type=r.resource_type,
        resource_id=r.resource_id,
        auto_change_control=r.auto_change_control,
        change_template_id=r.change_template_id,
        require_approved_change=r.require_approved_change,
    )


def _to_record(r: ChangeRecordRow) -> ChangeRecord:
    return ChangeRecord(
        number=r.number,
        template_id=r.template_id,
        state=ChangeState(r.state),
        short_description=r.short_description,
        risk=Risk(r.risk),
        assignment_group=r.assignment_group,
        cab_required=r.cab_required,
        initiated_by=r.initiated_by,
        resource_type=r.resource_type,
        resource_id=r.resource_id,
        created_at=r.created_at,
        closed_at=r.closed_at,
        close_code=r.close_code,
    )


class ChangeRepository:
    # templates
    def upsert_template(self, t: ChangeTemplate) -> ChangeTemplate:
        with get_sessionmaker()() as s:
            row = s.get(ChangeTemplateRow, t.id) or ChangeTemplateRow(id=t.id)
            row.name = t.name
            row.short_description = t.short_description
            row.assignment_group = t.assignment_group
            row.category = t.category
            row.risk = str(t.risk)
            row.impact = t.impact
            row.cab_required = t.cab_required
            row.extra_fields_json = json.dumps(t.extra_fields)
            s.add(row)
            s.commit()
            s.refresh(row)
            return _to_template(row)

    def get_template(self, tid: str) -> ChangeTemplate | None:
        with get_sessionmaker()() as s:
            row = s.get(ChangeTemplateRow, tid)
            return _to_template(row) if row else None

    def list_templates(self) -> list[ChangeTemplate]:
        with get_sessionmaker()() as s:
            return [_to_template(r) for r in s.execute(select(ChangeTemplateRow)).scalars().all()]

    def count_templates(self) -> int:
        with get_sessionmaker()() as s:
            return int(s.execute(select(func.count(ChangeTemplateRow.id))).scalar() or 0)

    # policies
    def upsert_policy(self, p: ChangeControlPolicy) -> ChangeControlPolicy:
        with get_sessionmaker()() as s:
            existing = s.execute(
                select(ChangePolicyRow).where(
                    ChangePolicyRow.resource_type == p.resource_type,
                    ChangePolicyRow.resource_id == p.resource_id,
                )
            ).scalar_one_or_none()
            row = existing or ChangePolicyRow(id=p.id)
            row.resource_type = p.resource_type
            row.resource_id = p.resource_id
            row.auto_change_control = p.auto_change_control
            row.change_template_id = p.change_template_id
            row.require_approved_change = p.require_approved_change
            s.add(row)
            s.commit()
            s.refresh(row)
            return _to_policy(row)

    def get_policy(self, resource_type: str, resource_id: str) -> ChangeControlPolicy | None:
        with get_sessionmaker()() as s:
            row = s.execute(
                select(ChangePolicyRow).where(
                    ChangePolicyRow.resource_type == resource_type,
                    ChangePolicyRow.resource_id == resource_id,
                )
            ).scalar_one_or_none()
            return _to_policy(row) if row else None

    # records
    def save_record(self, rec: ChangeRecord) -> None:
        with get_sessionmaker()() as s:
            row = s.get(ChangeRecordRow, rec.number) or ChangeRecordRow(number=rec.number)
            row.template_id = rec.template_id
            row.state = str(rec.state)
            row.short_description = rec.short_description
            row.risk = str(rec.risk)
            row.assignment_group = rec.assignment_group
            row.cab_required = rec.cab_required
            row.initiated_by = rec.initiated_by
            row.resource_type = rec.resource_type
            row.resource_id = rec.resource_id
            row.created_at = rec.created_at
            row.closed_at = rec.closed_at
            row.close_code = rec.close_code
            s.add(row)
            s.commit()

    def get_record(self, number: str) -> ChangeRecord | None:
        with get_sessionmaker()() as s:
            row = s.get(ChangeRecordRow, number)
            return _to_record(row) if row else None

    def list_records(self, limit: int = 100) -> list[ChangeRecord]:
        with get_sessionmaker()() as s:
            rows = (
                s.execute(
                    select(ChangeRecordRow).order_by(ChangeRecordRow.created_at.desc()).limit(limit)
                )
                .scalars()
                .all()
            )
            return [_to_record(r) for r in rows]

    def count_records(self) -> int:
        with get_sessionmaker()() as s:
            return int(s.execute(select(func.count(ChangeRecordRow.number))).scalar() or 0)
