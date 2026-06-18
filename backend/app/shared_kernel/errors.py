"""Base error types shared across contexts.

Contexts raise these (or subclasses) from their domain/application layers; the platform
api layer maps them to HTTP responses, so domain code never imports FastAPI/HTTP concerns.
"""

from __future__ import annotations


class NexusError(Exception):
    """Root of all Nexus application errors. Carries an HTTP-ish status hint."""

    status_code: int = 500

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.__class__.__name__)
        self.message = message or self.__class__.__name__


class DomainError(NexusError):
    """A domain invariant was violated. Default 422 (unprocessable)."""

    status_code = 422


class ValidationError(NexusError):
    """Input failed validation. 400."""

    status_code = 400


class NotFoundError(NexusError):
    """A referenced resource does not exist. 404."""

    status_code = 404


class ConflictError(NexusError):
    """The request conflicts with current state. 409."""

    status_code = 409


class EntitlementError(NexusError):
    """The caller is not entitled to perform this action (RBAC). 403."""

    status_code = 403


class AuthenticationError(NexusError):
    """Authentication failed or is missing. 401."""

    status_code = 401
