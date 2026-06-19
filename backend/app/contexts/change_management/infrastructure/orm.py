"""ORM rows for change templates, policies, and records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base


class ChangeTemplateRow(Base):
    __tablename__ = "change_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    short_description: Mapped[str] = mapped_column(Text, default="")
    assignment_group: Mapped[str] = mapped_column(String, default="Automation")
    category: Mapped[str] = mapped_column(String, default="Standard")
    risk: Mapped[str] = mapped_column(String, default="low")
    impact: Mapped[str] = mapped_column(String, default="low")
    cab_required: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_fields_json: Mapped[str] = mapped_column(Text, default="{}")


class ChangePolicyRow(Base):
    __tablename__ = "change_policies"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    resource_type: Mapped[str] = mapped_column(String, nullable=False)
    resource_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    auto_change_control: Mapped[bool] = mapped_column(Boolean, default=True)
    change_template_id: Mapped[str | None] = mapped_column(String, nullable=True)
    require_approved_change: Mapped[bool] = mapped_column(Boolean, default=False)


class ChangeRecordRow(Base):
    __tablename__ = "change_records"

    number: Mapped[str] = mapped_column(String, primary_key=True)
    template_id: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(String, nullable=False, index=True)
    short_description: Mapped[str] = mapped_column(Text, default="")
    risk: Mapped[str] = mapped_column(String, default="low")
    assignment_group: Mapped[str] = mapped_column(String, default="Automation")
    cab_required: Mapped[bool] = mapped_column(Boolean, default=False)
    initiated_by: Mapped[str] = mapped_column(String, default="operator")
    resource_type: Mapped[str] = mapped_column(String, default="")
    resource_id: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    close_code: Mapped[str | None] = mapped_column(String, nullable=True)
