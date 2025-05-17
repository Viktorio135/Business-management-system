from datetime import datetime
import pytest
from httpx import ASGITransport, AsyncClient


from main import app
from database.models import User
from dependencies import get_task_repo, get_user_repo
from applications.task.router import (
    get_current_user_dep, get_current_user_dep_admin
)


@pytest.fixture
def test_user():
    return User(
        id=1,
        email="user@example.com",
        name="Test",
        lastname="User",
        role="user"
    )


@pytest.fixture
def test_admin_user():
    return User(
        id=2,
        email="admin@example.com",
        name="Admin",
        lastname="User",
        role="admin"
    )


@pytest.fixture
def override_get_current_user(test_user):
    async def _override():
        return test_user
    return _override


@pytest.fixture
def override_get_current_user_admin(test_admin_user):
    async def _override():
        return test_admin_user
    return _override


@pytest.mark.asyncio
async def test_tasks_list_page(override_get_current_user):
    class FakeUser:
        def __init__(self, name):
            self.name = name

    class FakeTask:
        def __init__(self):
            self.id = 1
            self.description = "Sample task"
            self.creator_user = FakeUser("Admin")
            self.performer_user = FakeUser("Performer")
            self.status = "open"
            self.assessment = 5
            self.deadline = datetime.now()

    class FakeTaskRepo:
        async def get_all_user_tasks(self, session, user_id):
            return {
                "tasks": [FakeTask()],
                "avg": 4.5
            }

    app.dependency_overrides[get_current_user_dep] = override_get_current_user
    app.dependency_overrides[get_task_repo] = lambda: FakeTaskRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/tasks")

    assert response.status_code == 200
    assert "Sample task" in response.text
    assert "Admin" in response.text


@pytest.mark.asyncio
async def test_create_task_page(override_get_current_user_admin):
    class FakeUserRepo:
        async def get_all(self, session):
            return [User(id=1), User(id=2)]

    app.dependency_overrides[
        get_current_user_dep_admin
    ] = override_get_current_user_admin
    app.dependency_overrides[get_user_repo] = lambda: FakeUserRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/tasks/create")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_task_detail_page(override_get_current_user):
    class FakeTask:
        def __init__(self):
            self.id = 1
            self.creator = 1
            self.performer = 2
            self.creator_user = "test"

    class FakeTaskRepo:
        async def get_user_tasks(self, session, task_id, user_id):
            return FakeTask()

    app.dependency_overrides[get_current_user_dep] = override_get_current_user
    app.dependency_overrides[get_task_repo] = lambda: FakeTaskRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/tasks/1")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_edit_task_page(override_get_current_user):
    class FakeTask:
        def __init__(self):
            self.id = 1
            self.creator = 1

    class FakeTaskRepo:
        async def get(self, session, task_id):
            return FakeTask()

    class FakeUserRepo:
        async def get_all(self, session):
            return [User(id=1), User(id=2)]

    app.dependency_overrides[get_current_user_dep] = override_get_current_user
    app.dependency_overrides[get_task_repo] = lambda: FakeTaskRepo()
    app.dependency_overrides[get_user_repo] = lambda: FakeUserRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/tasks/1/edit")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
