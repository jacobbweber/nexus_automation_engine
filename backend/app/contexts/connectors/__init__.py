"""Connectors bounded context — the Anti-Corruption Layer over heterogeneous backends.

Every backend (execution engines and systems of record) is reached through a stable **port**
defined in ``domain.ports``. Concrete adapters live in ``infrastructure`` (today: simulation
adapters that satisfy the same ports as real ones will). This is what makes Nexus
vendor/platform-agnostic: adding a backend means writing one adapter; no other context changes.

See specs/00_foundation/architecture.md §5 and the canvas orchestration spec.
"""
