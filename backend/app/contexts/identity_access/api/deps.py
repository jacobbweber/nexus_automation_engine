"""FastAPI security dependencies: extract + verify the bearer token, enforce roles."""

from __future__ import annotations

from collections.abc import Callable

import jwt
from fastapi import Depends, Request

from app.contexts.identity_access.application.security import decode_token
from app.contexts.identity_access.domain.models import GlobalRole, UserContext
from app.shared_kernel.errors import AuthenticationError, EntitlementError


def get_current_user(request: Request) -> UserContext:
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        raise AuthenticationError("Missing bearer token")
    token = header.split(" ", 1)[1].strip()
    try:
        return decode_token(token)
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid or expired token") from exc


def require_role(*roles: GlobalRole) -> Callable[[UserContext], UserContext]:
    allowed = set(roles)

    def _dep(user: UserContext = Depends(get_current_user)) -> UserContext:
        if user.global_role not in allowed and user.global_role != GlobalRole.ADMIN:
            raise EntitlementError(
                f"Requires one of roles: {', '.join(sorted(r.value for r in allowed))}"
            )
        return user

    return _dep
