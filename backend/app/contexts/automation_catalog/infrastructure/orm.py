"""ORM row for catalog templates (survey + params stored as JSON)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base


class TemplateRow(Base):
    __tablename__ = "catalog_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    connector: Mapped[str] = mapped_column(String, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    markdown_documentation: Mapped[str] = mapped_column(Text, default="")
    supports_check_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_diff: Mapped[bool] = mapped_column(Boolean, default=False)
    survey_json: Mapped[str] = mapped_column(Text, default="[]")
    default_params_json: Mapped[str] = mapped_column(Text, default="{}")
    owner: Mapped[str] = mapped_column(String, default="engineer")
    approval_state: Mapped[str] = mapped_column(String, default="draft", index=True)
    domain: Mapped[str] = mapped_column(String, default="General", index=True)
    vendor: Mapped[str] = mapped_column(String, default="", index=True)
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    risk: Mapped[str] = mapped_column(String, default="low", index=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=5)
    prerequisites: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[str] = mapped_column(String, default="1.0.0")
    atomic: Mapped[bool] = mapped_column(Boolean, default=True)
    ci_type: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    ci_heritage: Mapped[str] = mapped_column(Text, default="")
    approved_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_reviewed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
