import calendar
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


from datetime import date, datetime, timedelta

from sqlalchemy import select

from applications.auth.security import get_current_user
from database.database import get_db, AsyncSession
from database.models import Meeting, User
from utils import render_template


router = APIRouter(prefix='/calendar')
templates = Jinja2Templates(directory="templates")


@router.get("/{year}/{month}", name="calendar_view")
async def calendar_view(
    request: Request,
    year: int,
    month: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    today = date.today()
    current_date = date(year, month, 1)

    # Получаем встречи за месяц
    month_start = datetime(year, month, 1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    month_end = next_month - timedelta(seconds=1)

    meetings_query = await session.execute(
        select(Meeting).where(Meeting.date >= month_start, Meeting.date <= month_end)
    )
    meetings = meetings_query.scalars().all()

    events_by_day = {}
    for meeting in meetings:
        day_key = meeting.date.date()
        events_by_day.setdefault(day_key, []).append({
            "title": meeting.description[:30],  # или meeting.title, если есть
            "time": meeting.date.strftime("%H:%M"),
            "type": "meeting",
        })

    # Генерируем календарь
    cal = calendar.Calendar(firstweekday=0)
    month_weeks = cal.monthdatescalendar(year, month)

    calendar_grid = []
    for week in month_weeks:
        week_data = []
        for day in week:
            day_events = events_by_day.get(day, []) if day.month == month else []
            week_data.append({
                "date": day if day.month == month else None,
                "events": day_events
            })
        calendar_grid.append(week_data)

    # Ближайшие 7 дней
    upcoming_events_query = await session.execute(
        select(Meeting).where(
            Meeting.date >= today,
            Meeting.date <= today + timedelta(days=7)
        )
    )
    upcoming_meetings = upcoming_events_query.scalars().all()
    upcoming_by_day = {}
    for meeting in upcoming_meetings:
        day_key = meeting.date.date()
        upcoming_by_day.setdefault(day_key, []).append({
            "title": meeting.description[:30],
            "time": meeting.date.strftime("%H:%M"),
            "type": "meeting",
        })

    upcoming_list = []
    for i in range(7):
        d = today + timedelta(days=i)
        upcoming_list.append({
            "date": d.strftime("%d.%m.%Y"),
            "events": upcoming_by_day.get(d, [])
        })

    return render_template(
        request,
        templates,
        "calendar/calendar.html",
        {
            "calendar": calendar_grid,
            "current_date": current_date,
            "today": today,
            "prev_month": (current_date - timedelta(days=1)).replace(day=1),
            "next_month": (current_date + timedelta(days=31)).replace(day=1),
            "upcoming_events": upcoming_list,
        },
        user=current_user
    )
