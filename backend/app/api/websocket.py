from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
import json
import asyncio

from app.services.event_bus import EventBus

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections per task."""

    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self._connections:
            self._connections[task_id] = set()
        self._connections[task_id].add(websocket)

    def disconnect(self, task_id: str, websocket: WebSocket):
        self._connections[task_id].discard(websocket)
        if not self._connections[task_id]:
            del self._connections[task_id]

    async def broadcast(self, task_id: str, message: dict):
        if task_id not in self._connections:
            return
        dead = set()
        for ws in self._connections[task_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._connections[task_id].discard(ws)


manager = ConnectionManager()


@router.websocket("/ws/tasks/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: str, request: Request):
    await manager.connect(task_id, websocket)

    # Subscribe to redis event bus for this task
    event_bus: EventBus = request.app.state.event_bus
    queue = await event_bus.subscribe(event_bus.task_channel(task_id))

    # Forward redis messages to websocket
    async def redis_forwarder():
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=30)
                await manager.broadcast(task_id, msg)
            except asyncio.TimeoutError:
                continue
            except Exception:
                break

    forwarder_task = asyncio.create_task(redis_forwarder())

    try:
        while True:
            data = await websocket.receive_json()
            # Forward control panel messages to the event bus (which the agent listens to)
            await event_bus.publish(event_bus.task_channel(task_id), data)
    except WebSocketDisconnect:
        pass
    finally:
        forwarder_task.cancel()
        manager.disconnect(task_id, websocket)