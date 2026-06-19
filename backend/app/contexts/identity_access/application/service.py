"""Identity application services: authentication and default-user seeding."""

from __future__ import annotations

import time

from app.contexts.identity_access.application.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.contexts.identity_access.domain.models import GlobalRole, User, UserContext
from app.contexts.identity_access.infrastructure.repository import IdentityRepository
from app.shared_kernel.errors import AuthenticationError, RateLimitError
from app.shared_kernel.ids import new_id

# In-memory login throttle (single-instance; documented ceiling). username -> recent failure ts.
_FAILURES: dict[str, list[float]] = {}
_MAX_FAILURES = 5
_WINDOW_SECONDS = 300.0

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
        self._check_throttle(username)
        found = self.repo.get_by_username(username)
        user_hash = found if found else None
        if (
            user_hash is None
            or not user_hash[0].is_active
            or not verify_password(password, user_hash[1])
        ):
            self._record_failure(username)
            raise AuthenticationError("Invalid username or password")
        _FAILURES.pop(username, None)  # clear on success
        user, _ = user_hash
        token = create_access_token(
            UserContext(id=user.id, username=user.username, global_role=user.global_role)
        )
        return user, token

    @staticmethod
    def _check_throttle(username: str) -> None:
        now = time.monotonic()
        recent = [t for t in _FAILURES.get(username, []) if now - t < _WINDOW_SECONDS]
        _FAILURES[username] = recent
        if len(recent) >= _MAX_FAILURES:
            raise RateLimitError("Too many failed login attempts; try again later")

    @staticmethod
    def _record_failure(username: str) -> None:
        _FAILURES.setdefault(username, []).append(time.monotonic())


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
