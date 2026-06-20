"""Pinning rule repository."""

from __future__ import annotations

from app.contexts.determinism.domain.models import PinningRule
from app.contexts.determinism.infrastructure.orm import PinningRuleRow
from app.platform.database import get_sessionmaker


def _to_rule(row: PinningRuleRow) -> PinningRule:
    return PinningRule.model_validate_json(row.document_json)


class PinningRuleRepository:
    def list_all(self) -> list[PinningRule]:
        with get_sessionmaker()() as s:
            rows = (
                s.query(PinningRuleRow).order_by(PinningRuleRow.priority, PinningRuleRow.name).all()
            )
            return [_to_rule(r) for r in rows]

    def get(self, rule_id: str) -> PinningRule | None:
        with get_sessionmaker()() as s:
            row = s.get(PinningRuleRow, rule_id)
            return _to_rule(row) if row else None

    def upsert(self, rule: PinningRule) -> PinningRule:
        with get_sessionmaker()() as s:
            row = s.get(PinningRuleRow, rule.id) or PinningRuleRow(id=rule.id)
            row.name = rule.name
            row.enabled = rule.enabled
            row.priority = rule.priority
            row.document_json = rule.model_dump_json()
            s.add(row)
            s.commit()
        return rule

    def delete(self, rule_id: str) -> bool:
        with get_sessionmaker()() as s:
            row = s.get(PinningRuleRow, rule_id)
            if row is None:
                return False
            s.delete(row)
            s.commit()
            return True

    def count(self) -> int:
        with get_sessionmaker()() as s:
            return s.query(PinningRuleRow).count()
