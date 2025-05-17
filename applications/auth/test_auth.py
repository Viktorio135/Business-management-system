import pytest


from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from database.database import get_db
from database.models import User


@pytest.mark.asyncio
async def test_register_and_login(async_session: AsyncSession):
    async def override_db():
        yield async_session
    app.dependency_overrides[get_db] = override_db

    await async_session.execute(delete(User).where(
        User.email == "john@example.com")
    )
    await async_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/auth/register", data={
            "name": "John",
            "lastname": "Doe",
            "email": "john@example.com",
            "password1": "password",
            "password2": "password"
        }, follow_redirects=False)
        assert response.status_code == 303, response.text


@pytest.mark.asyncio
async def test_login_invalid(async_session: AsyncSession):
    async def override_db():
        yield async_session
    app.dependency_overrides[get_db] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/auth/login", data={
            "username": "wrong@example.com",
            "password": "wrongpass"
        }, follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"].startswith("/auth/login")
