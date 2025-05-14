import pytest

from datetime import datetime
from httpx import AsyncClient
from httpx import ASGITransport


from dependencies import get_meeting_repo, get_task_repo
from database.models import User
from main import app
from applications.calendar.router import get_current_user_dep


@pytest.mark.asyncio
async def test_calendar_view():
    test_user = User(
        id=1,
        email="test@example.com",
        name="Test",
        lastname="User",
        role="admin"
    )

    async def override_current_user():
        return test_user

    class FakeMeeting:
        def __init__(self, date, description):
            self.date = date
            self.description = description

    class FakeTask:
        def __init__(self, deadline, description):
            self.deadline = deadline
            self.description = description

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

    app.dependency_overrides[get_meeting_repo] = lambda: FakeMeetingRepo()
    app.dependency_overrides[get_task_repo] = lambda: FakeTaskRepo()
    app.dependency_overrides[get_current_user_dep] = override_current_user
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/calendar")

    assert response.status_code == 200
    assert "Team Sync" in response.text
    assert "Finish Report" in response.text
