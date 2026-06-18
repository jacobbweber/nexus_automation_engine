"""Nexus Automation Engine — backend application package.

Organized by Domain-Driven Design bounded contexts implemented as vertical slices
(see specs/00_foundation/architecture.md). Top-level packages:

- ``platform``      — composition root: FastAPI app, async DB, config, security middleware.
- ``shared_kernel`` — cross-context primitives only (ids, errors, VariablePool).
- ``contexts``      — one package per bounded context (each a full vertical slice).
"""

__version__ = "0.1.0"
