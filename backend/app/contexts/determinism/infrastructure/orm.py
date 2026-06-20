"""ORM row for pinning rules (rule stored as a JSON document)."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base


class PinningRuleRow(Base):
    __tablename__ = "determinism_pinning_rule"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    document_json: Mapped[str] = mapped_column(Text, nullable=False)  # full PinningRule as JSON
