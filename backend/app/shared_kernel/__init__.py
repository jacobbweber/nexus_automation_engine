"""Shared kernel — small, stable primitives shared across bounded contexts.

Nothing vendor-specific or context-specific belongs here. Currently:
- ``ids``           — identifier generation helpers.
- ``errors``        — base domain/application error types.
- ``variable_pool`` — the typed, expression-capable VariablePool used by the canvas engine.
"""

from app.shared_kernel.errors import (
    AuthenticationError,
    ConflictError,
    DomainError,
    EntitlementError,
    NexusError,
    NotFoundError,
    ValidationError,
)
from app.shared_kernel.ids import new_id
from app.shared_kernel.variable_pool import VariablePool

__all__ = [
    "new_id",
    "VariablePool",
    "NexusError",
    "DomainError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "EntitlementError",
    "AuthenticationError",
]
