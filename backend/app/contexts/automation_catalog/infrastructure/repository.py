"""Template repository (sync SQLAlchemy)."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func, select

from app.contexts.automation_catalog.domain.models import (
    ApprovalState,
    SurveyField,
    Template,
)
from app.contexts.automation_catalog.infrastructure.orm import TemplateRow
from app.contexts.connectors.domain.models import ConnectorKind
from app.platform.database import get_sessionmaker


def _to_template(row: TemplateRow) -> Template:
    return Template(
        id=row.id,
        name=row.name,
        description=row.description,
        connector=ConnectorKind(row.connector),
        action=row.action,
        markdown_documentation=row.markdown_documentation,
        supports_check_mode=row.supports_check_mode,
        supports_diff=row.supports_diff,
        survey=[SurveyField(**f) for f in json.loads(row.survey_json or "[]")],
        default_params=json.loads(row.default_params_json or "{}"),
        owner=row.owner,
        approval_state=ApprovalState(row.approval_state),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class TemplateRepository:
    def upsert(self, template: Template) -> Template:
        with get_sessionmaker()() as session:
            row = session.get(TemplateRow, template.id)
            if row is None:
                row = TemplateRow(id=template.id, created_at=template.created_at)
                session.add(row)
            row.name = template.name
            row.description = template.description
            row.connector = str(template.connector)
            row.action = template.action
            row.markdown_documentation = template.markdown_documentation
            row.supports_check_mode = template.supports_check_mode
            row.supports_diff = template.supports_diff
            row.survey_json = json.dumps([f.model_dump() for f in template.survey])
            row.default_params_json = json.dumps(template.default_params)
            row.owner = template.owner
            row.approval_state = str(template.approval_state)
            row.updated_at = template.updated_at
            session.commit()
            session.refresh(row)
            return _to_template(row)

    def get(self, template_id: str) -> Template | None:
        with get_sessionmaker()() as session:
            row = session.get(TemplateRow, template_id)
            return _to_template(row) if row else None

    def list(self, *, approval_state: ApprovalState | None = None) -> list[Template]:
        stmt = select(TemplateRow).order_by(TemplateRow.name)
        if approval_state is not None:
            stmt = stmt.where(TemplateRow.approval_state == str(approval_state))
        with get_sessionmaker()() as session:
            return [_to_template(r) for r in session.execute(stmt).scalars().all()]

    def count(self) -> int:
        with get_sessionmaker()() as session:
            return int(session.execute(select(func.count(TemplateRow.id))).scalar() or 0)

    def set_state(self, template_id: str, state: ApprovalState, *, updated_at: datetime) -> None:
        with get_sessionmaker()() as session:
            row = session.get(TemplateRow, template_id)
            if row is None:
                return
            row.approval_state = str(state)
            row.updated_at = updated_at
            session.commit()
