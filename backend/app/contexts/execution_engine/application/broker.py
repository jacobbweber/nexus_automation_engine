"""In-memory pub/sub for live job log streaming to WebSocket subscribers.

A process-local broker: the worker publishes events for a job_id; WebSocket connections subscribe
to that job_id and drain the queue. Persisted logs (the repository) are the durable record; this
is only the live fan-out. A sentinel ``None`` signals end-of-stream to subscribers.
"""

from __future__ import annotations

import asyncio
from typing import Any


class LogBroker:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[Any]]] = {}

    def subscribe(self, job_id: str) -> asyncio.Queue[Any]:
        queue: asyncio.Queue[Any] = asyncio.Queue()
        self._subscribers.setdefault(job_id, []).append(queue)
        return queue

    def unsubscribe(self, job_id: str, queue: asyncio.Queue[Any]) -> None:
        subs = self._subscribers.get(job_id)
        if subs and queue in subs:
            subs.remove(queue)
        if subs is not None and not subs:
            self._subscribers.pop(job_id, None)

    async def publish(self, job_id: str, event: dict[str, Any]) -> None:
        for queue in list(self._subscribers.get(job_id, [])):
            await queue.put(event)

    async def close(self, job_id: str) -> None:
        for queue in list(self._subscribers.get(job_id, [])):
            await queue.put(None)


_broker: LogBroker | None = None


def get_broker() -> LogBroker:
    global _broker
    if _broker is None:
        _broker = LogBroker()
    return _broker
