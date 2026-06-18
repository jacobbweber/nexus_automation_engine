"""Identity application services: authentication and default-user seeding."""

from __future__ import annotations

from app.contexts.identity_access.application.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.contexts.identity_access.domain.models import GlobalRole, User, UserContext
from app.contexts.identity_access.infrastructure.repository import IdentityRepository
from app.shared_kernel.errors import AuthenticationError
from app.shared_kernel.ids import new_id

# Default local/demo users (dev-only passwords; never used in a real deployment).
_DEFAULT_USERS = [
    ("admin", "admin@nexus.local", GlobalRole.ADMIN, "admin123"),
    ("engineer", "engineer@nexus.local", GlobalRole.ENGINEER, "engineer123"),
    ("operator", "operator@nexus.local", GlobalRole.OPERATOR, "operator123"),
    ("consumer", "consumer@nexus.local", GlobalRole.CONSUMER, "consumer123"),
]


class AuthService:
    def __init__(self, repository: IdentityRepository | None = None) -> None:
        self.repo = repository or IdentityRepository()

    def authenticate(self, username: str, password: str) -> tuple[User, str]:
        found = self.repo.get_by_username(username)
        if found is None:
            raise AuthenticationError("Invalid username or password")
        user, hashed = found
        if not user.is_active or not verify_password(password, hashed):
            raise AuthenticationError("Invalid username or password")
        token = create_access_token(
            UserContext(id=user.id, username=user.username, global_role=user.global_role)
        )
        return user, token


def seed_default_users(repository: IdentityRepository | None = None) -> int:
    """Create the default users if none exist. Returns the number created."""
    repo = repository or IdentityRepository()
    if repo.count_users() > 0:
        return 0
    created = 0
    for username, email, role, password in _DEFAULT_USERS:
        repo.add_user(
            user_id=new_id("usr"),
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=role,
        )
        created += 1
    return created
