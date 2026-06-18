"""Identity & Access domain models and the RBAC permission matrix."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class GlobalRole(StrEnum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    OPERATOR = "operator"
    CONSUMER = "consumer"


class PermissionLevel(StrEnum):
    READ = "read"
    EXECUTE = "execute"
    WRITE = "write"
    ADMIN = "admin"


class Capability(StrEnum):
    """Coarse capabilities gated by global role (refined by resource permissions)."""

    VIEW_JOBS = "view_jobs"
    CREATE_TEMPLATES = "create_templates"
    EXECUTE_CHECK = "execute_check"
    EXECUTE_LIVE = "execute_live"
    MANAGE_INTEGRATIONS = "manage_integrations"


# The global-role capability matrix (blueprint §7). Resource-level permissions can *grant*
# beyond this for specific resources, but the baseline is here.
ROLE_CAPABILITIES: dict[GlobalRole, set[Capability]] = {
    GlobalRole.ADMIN: set(Capability),
    GlobalRole.ENGINEER: {
        Capability.VIEW_JOBS,
        Capability.CREATE_TEMPLATES,
        Capability.EXECUTE_CHECK,
        Capability.EXECUTE_LIVE,
    },
    GlobalRole.OPERATOR: {
        Capability.VIEW_JOBS,
        Capability.EXECUTE_CHECK,
        Capability.EXECUTE_LIVE,  # restricted to entitled assets (resource permissions)
    },
    GlobalRole.CONSUMER: {
        Capability.VIEW_JOBS,
        Capability.EXECUTE_CHECK,  # selected assets only
    },
}


class User(BaseModel):
    id: str
    username: str
    email: str
    global_role: GlobalRole
    is_active: bool = True


class UserContext(BaseModel):
    """The authenticated principal carried through a request."""

    id: str
    username: str
    global_role: GlobalRole


class Organization(BaseModel):
    id: str
    name: str


class Team(BaseModel):
    id: str
    name: str
    organization_id: str


class AssetGroup(BaseModel):
    id: str
    name: str
    organization_id: str


class ResourcePermission(BaseModel):
    id: str
    resource_type: str  # "automation_template" | "terraform_config" | "script" | "workflow"
    resource_id: str
    permission_level: PermissionLevel
    user_id: str | None = None
    team_id: str | None = None
