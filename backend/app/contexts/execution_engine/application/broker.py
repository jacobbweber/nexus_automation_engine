"""Live job-log broadcast — a process-wide AsyncBroker keyed by job_id.

Thin wrapper over the shared-kernel ``AsyncBroker`` (was a duplicated class; see audit Q2).
``LogBroker`` is retained as an alias for existing type hints.
"""

from __future__ import annotations

from app.shared_kernel.broker import AsyncBroker

LogBroker = AsyncBroker  # backwards-compatible alias

_broker: AsyncBroker | None = None


def get_broker() -> AsyncBroker:
    global _broker
    if _broker is None:
        _broker = AsyncBroker()
    return _broker
