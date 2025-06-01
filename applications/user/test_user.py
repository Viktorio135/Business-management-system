import pytest


from httpx import ASGITransport, AsyncClient


from main import app
from database.models import User
from dependencies import get_user_repo
from applications.user.router import get_current_user_dep


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
def override_get_current_user(test_user):
    async def _override():
        return test_user
    return _override


@pytest.fixture
def override_get_user_repo():
    class FakeUserRepo:
        async def update(self, session, user_id, data):
            assert user_id == 1
            assert data["name"] == "UpdatedName"
            assert data["lastname"] == "UpdatedLastname"
            assert data["email"] == "updated@example.com"

        async def update_password(self, session, user_id, new_password):
            assert user_id == 1
            assert new_password == "newpassword123"

        async def is_auth(self, session, email, password):
            assert email == "user@example.com"
            assert password == "correctpassword"
            return True

        async def delete(self, session, user_id):
            assert user_id == 1

    return FakeUserRepo


@pytest.mark.asyncio
async def test_profile_page(override_get_current_user):
    app.dependency_overrides[get_current_user_dep] = override_get_current_user
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get("/users/profile")

    assert response.status_code == 200
    assert "Test" in response.text


@pytest.mark.asyncio
async def test_profile_edit(override_get_current_user, override_get_user_repo):
    app.dependency_overrides[get_current_user_dep] = override_get_current_user
    app.dependency_overrides[get_user_repo] = override_get_user_repo

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/users/edit",
            data={
                "name": "UpdatedName",
                "lastname": "UpdatedLastname",
                "email": "updated@example.com",
                "new_password": "newpassword123"
            }
        )

    assert response.status_code == 303  # Redirect after successful update
    assert response.headers["location"] == "/users/profile"


@pytest.mark.asyncio
async def test_profile_delete(
    override_get_current_user, override_get_user_repo
):
    app.dependency_overrides[get_current_user_dep] = override_get_current_user
    app.dependency_overrides[get_user_repo] = override_get_user_repo

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post(
            "/users/delete",
            data={
                "password": "correctpassword"
            }
        )

    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login"
    assert "access_token" not in response.cookies
