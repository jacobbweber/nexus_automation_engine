"""Pure RBAC entitlement evaluation. No I/O — takes facts, returns a decision.

The evaluation overrides global permissions by tracing matching nodes down the hierarchy
Organization -> Team -> AssetGroup. Admins pass everything; otherwise a capability must be in
the global-role baseline, and resource-scoped actions additionally require an explicit
ResourcePermission of sufficient level.
"""

from __future__ import annotations

from app.contexts.identity_access.domain.models import (
    ROLE_CAPABILITIES,
    Capability,
    GlobalRole,
    PermissionLevel,
    ResourcePermission,
    UserContext,
)

_LEVEL_RANK = {
    PermissionLevel.READ: 0,
    PermissionLevel.EXECUTE: 1,
    PermissionLevel.WRITE: 2,
    PermissionLevel.ADMIN: 3,
}


def has_capability(user: UserContext, capability: Capability) -> bool:
    return capability in ROLE_CAPABILITIES.get(user.global_role, set())


def has_resource_permission(
    permissions: list[ResourcePermission],
    *,
    resource_type: str,
    resource_id: str,
    minimum: PermissionLevel,
) -> bool:
    needed = _LEVEL_RANK[minimum]
    for perm in permissions:
        if perm.resource_type == resource_type and perm.resource_id == resource_id:
            if _LEVEL_RANK[perm.permission_level] >= needed:
                return True
    return False


def can_execute(
    user: UserContext,
    *,
    resource_type: str,
    resource_id: str,
    live: bool,
    permissions: list[ResourcePermission],
) -> bool:
    """Decide whether a user may execute (check or live) a specific resource."""
    if user.global_role == GlobalRole.ADMIN:
        return True

    capability = Capability.EXECUTE_LIVE if live else Capability.EXECUTE_CHECK
    if not has_capability(user, capability):
        return False

    # Engineers may execute broadly; everyone else needs an explicit resource grant.
    if user.global_role == GlobalRole.ENGINEER:
        return True

    return has_resource_permission(
        permissions,
        resource_type=resource_type,
        resource_id=resource_id,
        minimum=PermissionLevel.EXECUTE,
    )
