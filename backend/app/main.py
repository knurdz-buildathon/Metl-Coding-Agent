from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import tasks, resources
from app.api.websocket import router as ws_router
from app.config import settings
from app.services.task_store import TaskStore
from app.services.event_bus import EventBus


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.task_store = TaskStore()

    # Initialize event bus (Redis pub/sub)
    event_bus = EventBus()
    try:
        await event_bus.connect()
    except Exception as e:
        print(f"Warning: Redis not available, running without event bus: {e}")
    app.state.event_bus = event_bus

    settings.validate()
    yield

    # Shutdown
    await app.state.task_store.close()
    await event_bus.close()


app = FastAPI(
    title="Metl Agent",
    version="0.1.0",
    description="Autonomous cloud coding agent API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api/v1")
app.include_router(resources.router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}