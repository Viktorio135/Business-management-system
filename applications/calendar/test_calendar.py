import pytest
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from dataclasses import dataclass
from typing import NamedTuple

from bs4 import BeautifulSoup

from dependencies import get_meeting_repo, get_task_repo
from main import app
from applications.calendar.router import get_current_user_dep


class FakeUser(NamedTuple):
    id: int
    email: str
    name: str
    lastname: str
    role: str
    is_authenticated: bool = True


@dataclass
class FakeMeeting:
    date: datetime
    description: str


@dataclass
class FakeTask:
    deadline: datetime
    description: str


class FakeMeetingRepo:
    async def get_meeting_with_date(self, session, start, end, user_id):
        return [
            FakeMeeting(
                datetime.today().replace(hour=10, minute=0),
                "Team Sync"
            )
        ]


class FakeTaskRepo:
    async def get_task_with_date(self, session, user_id, start, end):
        return [
            FakeTask(
                datetime.today().replace(hour=15, minute=30),
                "Finish Report"
            )
        ]


@pytest.mark.asyncio
async def test_calendar_view():
    test_user = FakeUser(
        id=1,
        email="test@example.com",
        name="Test",
        lastname="User",
        role="admin",
        is_authenticated=True
    )

    async def override_current_user():
        return test_user

    app.dependency_overrides[get_meeting_repo] = lambda: FakeMeetingRepo()
    app.dependency_overrides[get_task_repo] = lambda: FakeTaskRepo()
    app.dependency_overrides[get_current_user_dep] = override_current_user

    transport = ASGITransport(app=app, raise_app_exceptions=True)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/calendar")

    assert response.status_code == 200

    soup = BeautifulSoup(response.text, "html.parser")
    html_text = soup.get_text()

    assert "Finish Report" in html_text
