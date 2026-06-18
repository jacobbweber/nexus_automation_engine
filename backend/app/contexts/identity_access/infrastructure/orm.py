"""ORM rows for identity & access entities."""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    global_role: Mapped[str] = mapped_column(String, default="operator")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class OrganizationRow(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)


class TeamRow(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False)


class AssetGroupRow(Base):
    __tablename__ = "asset_groups"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, nullable=False)


class ResourcePermissionRow(Base):
    __tablename__ = "resource_permissions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    resource_type: Mapped[str] = mapped_column(String, nullable=False)
    resource_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    permission_level: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    team_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
