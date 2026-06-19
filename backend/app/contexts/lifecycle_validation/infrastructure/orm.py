"""ORM row for the (singleton) validation policy."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base


class ValidationPolicyRow(Base):
    __tablename__ = "validation_policy"

    id: Mapped[str] = mapped_column(String, primary_key=True, default="default")
    required_fields_json: Mapped[str] = mapped_column(Text, default="[]")
    max_review_age_days: Mapped[int] = mapped_column(Integer, default=180)
    enforce_cmdb_consistency: Mapped[bool] = mapped_column(Boolean, default=True)
    reject_retired: Mapped[bool] = mapped_column(Boolean, default=True)
    reject_unknown_ci: Mapped[bool] = mapped_column(Boolean, default=True)
    block_destructive_on_cluster: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_by: Mapped[str] = mapped_column(String, default="system")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
