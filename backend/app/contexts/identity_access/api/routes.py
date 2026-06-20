"""Authentication & user routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.contexts.identity_access.api.deps import get_current_user, require_role
from app.contexts.identity_access.application.service import AuthService
from app.contexts.identity_access.domain.models import (
    ROLE_CAPABILITIES,
    Capability,
    GlobalRole,
    User,
    UserContext,
)
from app.contexts.identity_access.infrastructure.repository import IdentityRepository
from app.shared_kernel.errors import NotFoundError

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    user, token = AuthService().authenticate(body.username, body.password)
    return LoginResponse(access_token=token, user=user)


@router.get("/me", response_model=User)
def me(current: UserContext = Depends(get_current_user)) -> User:
    user = IdentityRepository().get(current.id)
    if user is None:
        raise NotFoundError("User not found")
    return user


@router.get("/users", response_model=list[User])
def list_users(_admin: UserContext = Depends(require_role(GlobalRole.ADMIN))) -> list[User]:
    return IdentityRepository().list_users()


class RbacMatrix(BaseModel):
    roles: list[str]
    capabilities: list[str]
    matrix: dict[str, dict[str, bool]]  # role -> capability -> granted


@router.get("/rbac-matrix", response_model=RbacMatrix)
def rbac_matrix(_user: UserContext = Depends(get_current_user)) -> RbacMatrix:
    """The role × capability matrix. Read-only: the baseline is code-defined (refined per resource
    by entitlements); changing it is an intentional security-model change, not a runtime toggle."""
    roles = [r.value for r in GlobalRole]
    caps = [c.value for c in Capability]
    matrix = {
        r.value: {c.value: (c in ROLE_CAPABILITIES.get(r, set())) for c in Capability}
        for r in GlobalRole
    }
    return RbacMatrix(roles=roles, capabilities=caps, matrix=matrix)
