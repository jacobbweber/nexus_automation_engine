"""User & permission repository (sync SQLAlchemy)."""

from __future__ import annotations

from sqlalchemy import func, select

from app.contexts.identity_access.domain.models import (
    GlobalRole,
    PermissionLevel,
    ResourcePermission,
    User,
)
from app.contexts.identity_access.infrastructure.orm import (
    ResourcePermissionRow,
    UserRow,
)
from app.platform.database import get_sessionmaker


def _to_user(row: UserRow) -> User:
    return User(
        id=row.id,
        username=row.username,
        email=row.email,
        global_role=GlobalRole(row.global_role),
        is_active=row.is_active,
    )


class IdentityRepository:
    def add_user(
        self, *, user_id: str, username: str, email: str, hashed_password: str, role: GlobalRole
    ) -> User:
        row = UserRow(
            id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            global_role=str(role),
        )
        with get_sessionmaker()() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
            return _to_user(row)

    def get_by_username(self, username: str) -> tuple[User, str] | None:
        with get_sessionmaker()() as session:
            row = session.execute(
                select(UserRow).where(UserRow.username == username)
            ).scalar_one_or_none()
            if row is None:
                return None
            return _to_user(row), row.hashed_password

    def get(self, user_id: str) -> User | None:
        with get_sessionmaker()() as session:
            row = session.get(UserRow, user_id)
            return _to_user(row) if row else None

    def list_users(self) -> list[User]:
        with get_sessionmaker()() as session:
            return [_to_user(r) for r in session.execute(select(UserRow)).scalars().all()]

    def count_users(self) -> int:
        with get_sessionmaker()() as session:
            return int(session.execute(select(func.count(UserRow.id))).scalar() or 0)

    def grant(
        self,
        *,
        perm_id: str,
        resource_type: str,
        resource_id: str,
        level: PermissionLevel,
        user_id: str | None = None,
        team_id: str | None = None,
    ) -> None:
        with get_sessionmaker()() as session:
            session.add(
                ResourcePermissionRow(
                    id=perm_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    permission_level=str(level),
                    user_id=user_id,
                    team_id=team_id,
                )
            )
            session.commit()

    def permissions_for_user(self, user_id: str) -> list[ResourcePermission]:
        with get_sessionmaker()() as session:
            rows = (
                session.execute(
                    select(ResourcePermissionRow).where(ResourcePermissionRow.user_id == user_id)
                )
                .scalars()
                .all()
            )
            return [
                ResourcePermission(
                    id=r.id,
                    resource_type=r.resource_type,
                    resource_id=r.resource_id,
                    permission_level=PermissionLevel(r.permission_level),
                    user_id=r.user_id,
                    team_id=r.team_id,
                )
                for r in rows
            ]
