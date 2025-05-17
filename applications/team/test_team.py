import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from database.models import User
from dependencies import get_team_repo, get_user_repo
from applications.team.router import (
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
        id=1,
        email="admin@example.com",
        name="Admin",
        lastname="User",
        role="admin"
    )


@pytest.fixture
def override_get_current_user_admin(test_admin_user):
    async def _override():
        return test_admin_user
    return _override


@pytest.fixture
def override_get_current_user_user(test_user):
    async def _override():
        return test_user
    return _override


@pytest.mark.asyncio
async def test_team_list_page(override_get_current_user_admin):
    class FakeTeam:
        def __init__(self, id=1, name="Team Alpha"):
            self.id = id
            self.name = name

    class FakeTeamRepo:
        async def get_all(self, session):
            return [FakeTeam()]

    app.dependency_overrides[
        get_current_user_dep_admin
    ] = override_get_current_user_admin
    app.dependency_overrides[get_team_repo] = lambda: FakeTeamRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/teams")

    assert response.status_code == 200
    assert "Team Alpha" in response.text


@pytest.mark.asyncio
async def test_create_team_page(override_get_current_user_admin):
    class FakeUserRepo:
        async def get_all(self, session):
            return [User(id=1, name="Alice"), User(id=2, name="Bob")]

    app.dependency_overrides[
        get_current_user_dep_admin
    ] = override_get_current_user_admin
    app.dependency_overrides[get_user_repo] = lambda: FakeUserRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/teams/create")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_create_team_post(override_get_current_user_admin):
    class FakeTeamRepo:
        async def add(self, session, name, members):
            assert name == "New Team"
            assert members == [1, 2]

    app.dependency_overrides[
        get_current_user_dep_admin
    ] = override_get_current_user_admin
    app.dependency_overrides[get_team_repo] = lambda: FakeTeamRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/teams/create", data={"name": "New Team", "members": ["1", "2"]}
        )

    assert response.status_code == 303
    assert response.headers["location"] == "/teams"


@pytest.mark.asyncio
async def test_my_team_page(override_get_current_user_user):
    class FakeUserTeam:
        def __init__(self):
            self.id = 1
            self.name = "My Team"
            self.user_teams = []

    class FakeTeamRepo:
        async def get_user_team(self, session, user_id):
            return FakeUserTeam()

    app.dependency_overrides[
        get_current_user_dep
    ] = override_get_current_user_user
    app.dependency_overrides[get_team_repo] = lambda: FakeTeamRepo()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/teams/my_team")

    assert response.status_code == 200
    assert "My Team" in response.text
