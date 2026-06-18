"""Authentication & user routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.contexts.identity_access.api.deps import get_current_user, require_role
from app.contexts.identity_access.application.service import AuthService
from app.contexts.identity_access.domain.models import GlobalRole, User, UserContext
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
