import asyncio
import json
from typing import Set
from backend.app.models.execution import ExecutionEvent

class EventBus:
    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    async def emit(self, event: ExecutionEvent) -> None:
        for queue in list(self._subscribers):
            try:
                await queue.put(event)
            except Exception:
                self._subscribers.discard(queue)

    @staticmethod
    def to_sse(event: ExecutionEvent) -> str:
        payload = event.model_dump_json()
        return f"event: {event.event_type}\ndata: {payload}\n\n"
