import pytest
from httpx import ASGITransport, AsyncClient
from datetime import datetime
from fastapi import status

from main import app
from database.models import User
from dependencies import get_meeting_repo, get_user_repo
from applications.meeting.router import (
    get_current_user_dep,
    get_current_user_dep_admin
)


@pytest.fixture
def test_admin_user():
    return User(
        id=1,
        email="admin@example.com",
        name="Admin",
        lastname="User",
        role="admin"
    )


@pytest.fixture
def override_get_current_user(test_admin_user):
    async def _override():
        return test_admin_user
    return _override


@pytest.mark.asyncio
async def test_meeting_list_page(override_get_current_user):
    class FakeMeetingRepo:
        async def get_all(self, session):
            return []

    app.dependency_overrides[
        get_current_user_dep_admin
    ] = override_get_current_user
    app.dependency_overrides[get_meeting_repo] = lambda: FakeMeetingRepo()
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/meetings")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_create_meeting_page(override_get_current_user):
    class FakeUserRepo:
        async def get_all(self, session):
            return []

    app.dependency_overrides[
        get_current_user_dep_admin
    ] = override_get_current_user
    app.dependency_overrides[get_user_repo] = lambda: FakeUserRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/meetings/create")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_create_meeting_post(override_get_current_user):
    class FakeMeetingRepo:
        async def add(self, session, date, description, user_id, members):
            pass

    app.dependency_overrides[
        get_current_user_dep_admin
    ] = override_get_current_user
    app.dependency_overrides[get_meeting_repo] = lambda: FakeMeetingRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/meetings/create",
            data={
                "description": "Test meeting",
                "members": [1, 2],
                "date": datetime.now().isoformat()
            }
        )

    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/meetings"


@pytest.mark.asyncio
async def test_meeting_detail_page(override_get_current_user):
    class FakeUser:
        def __init__(self, id):
            self.id = id

    class FakeParticipant:
        def __init__(self, user):
            self.user = user

    class FakeMeeting:
        def __init__(self):
            self.id = 1
            self.date = datetime.now()
            self.creator = 'test'
            self.participants = [FakeParticipant(FakeUser(1))]

    class FakeMeetingRepo:
        async def get(self, session, meeting_id):
            return FakeMeeting()

    class FakeUserRepo:
        async def get_all(self, session):
            return [FakeUser(1), FakeUser(2)]

    app.dependency_overrides[get_current_user_dep] = override_get_current_user
    app.dependency_overrides[get_meeting_repo] = lambda: FakeMeetingRepo()
    app.dependency_overrides[get_user_repo] = lambda: FakeUserRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/meetings/1")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_add_meeting_member(override_get_current_user):
    class FakeMeetingRepo:
        async def add_member(self, session, meeting_id, user_id):
            pass

    app.dependency_overrides[
        get_current_user_dep_admin
    ] = override_get_current_user
    app.dependency_overrides[get_meeting_repo] = lambda: FakeMeetingRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/meetings/1/add_meeting_member",
            data={"user_id": 2}
        )

    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/meetings/1"


@pytest.mark.asyncio
async def test_delete_meeting_member(override_get_current_user):
    class FakeMeetingRepo:
        async def delete_member(self, session, meeting_id, user_id):
            pass

    app.dependency_overrides[
        get_current_user_dep_admin
    ] = override_get_current_user
    app.dependency_overrides[get_meeting_repo] = lambda: FakeMeetingRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/meetings/1/delete_meeting_member",
            data={"user_id": 2}
        )

    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/meetings/1"


@pytest.mark.asyncio
async def test_edit_meeting(override_get_current_user):
    class FakeMeetingRepo:
        async def update(self, session, meeting_id, data: dict):
            pass

    app.dependency_overrides[
        get_current_user_dep_admin
    ] = override_get_current_user
    app.dependency_overrides[get_meeting_repo] = lambda: FakeMeetingRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/meetings/1/edit",
            data={
                "description": "Updated desc",
                "date": datetime.now().isoformat()
            }
        )

    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/meetings/1"
