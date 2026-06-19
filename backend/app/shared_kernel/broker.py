"""Generic in-memory pub/sub broker — a shared-kernel primitive.

Used for live fan-out of run/log events to WebSocket subscribers. Process-local: durable state
lives in each context's repository; this is only the live broadcast. A sentinel ``None`` put on a
subscriber's queue signals end-of-stream.
"""

from __future__ import annotations

import asyncio
from typing import Any


class AsyncBroker:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[Any]]] = {}

    def subscribe(self, key: str) -> asyncio.Queue[Any]:
        queue: asyncio.Queue[Any] = asyncio.Queue()
        self._subscribers.setdefault(key, []).append(queue)
        return queue

    def unsubscribe(self, key: str, queue: asyncio.Queue[Any]) -> None:
        subs = self._subscribers.get(key)
        if subs and queue in subs:
            subs.remove(queue)
        if subs is not None and not subs:
            self._subscribers.pop(key, None)

    async def publish(self, key: str, event: dict[str, Any]) -> None:
        for queue in list(self._subscribers.get(key, [])):
            await queue.put(event)

    async def close(self, key: str) -> None:
        for queue in list(self._subscribers.get(key, [])):
            await queue.put(None)
