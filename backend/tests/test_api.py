import pytest
from httpx import AsyncClient, ASGITransport

from app.services.task_store import TaskStore
from app.services.event_bus import EventBus


@pytest.fixture
def app():
    from app.main import app as _app

    # Manually setup app state (lifespan doesn't run in tests)
    _app.state.task_store = TaskStore()
    _app.state.event_bus = EventBus()
    return _app


@pytest.fixture
def client(app):
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_task(client):
    response = await client.post(
        "/api/v1/tasks",
        json={
            "github_url": "https://github.com/org/repo",
            "branch": "main",
            "prompt": "Build a todo app",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_resources(client):
    response = await client.get("/api/v1/resources")
    assert response.status_code == 200
    data = response.json()
    assert "resources" in data
    assert len(data["resources"]) > 0