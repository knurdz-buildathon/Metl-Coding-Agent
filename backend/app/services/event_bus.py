import asyncio
import json
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings


class EventBus:
    """Redis pub/sub event bus for agent-control panel communication."""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub = None

    async def connect(self):
        self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        self._pubsub = self._redis.pubsub()

    async def publish(self, channel: str, message: dict):
        if self._redis:
            await self._redis.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str) -> asyncio.Queue:
        """Subscribe to a channel and return an async queue for messages."""
        queue: asyncio.Queue = asyncio.Queue()
        if self._pubsub:
            await self._pubsub.subscribe(channel)
            asyncio.create_task(self._relay(channel, queue))
        return queue

    async def _relay(self, channel: str, queue: asyncio.Queue):
        if not self._pubsub:
            return
        async for message in self._pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await queue.put(data)
                except json.JSONDecodeError:
                    pass

    async def close(self):
        if self._pubsub:
            await self._pubsub.unsubscribe()
        if self._redis:
            await self._redis.close()

    def task_channel(self, task_id: str) -> str:
        return f"metl:task:{task_id}"