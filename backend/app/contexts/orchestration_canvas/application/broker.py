"""In-memory pub/sub for live canvas run streaming (per run_id). Mirrors the execution broker.

Kept context-local (small duplication) so the canvas slice stays independent of the execution
engine's internals — the architecture favors decoupling over DRY at context boundaries.
"""

from __future__ import annotations

import asyncio
from typing import Any


class RunBroker:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[Any]]] = {}

    def subscribe(self, run_id: str) -> asyncio.Queue[Any]:
        queue: asyncio.Queue[Any] = asyncio.Queue()
        self._subscribers.setdefault(run_id, []).append(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue[Any]) -> None:
        subs = self._subscribers.get(run_id)
        if subs and queue in subs:
            subs.remove(queue)
        if subs is not None and not subs:
            self._subscribers.pop(run_id, None)

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        for queue in list(self._subscribers.get(run_id, [])):
            await queue.put(event)

    async def close(self, run_id: str) -> None:
        for queue in list(self._subscribers.get(run_id, [])):
            await queue.put(None)


_broker: RunBroker | None = None


def get_run_broker() -> RunBroker:
    global _broker
    if _broker is None:
        _broker = RunBroker()
    return _broker
