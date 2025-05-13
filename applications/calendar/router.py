import calendar


from fastapi import APIRouter, Depends, Query, Request
from fastapi.templating import Jinja2Templates

from datetime import date, datetime, timedelta


from applications.auth.security import get_current_user
from database.database import get_db, AsyncSession
from database.models import User
from database.repositories import MeetingRepository, TaskRepository
from utils import render_template
from dependencies import get_meeting_repo, get_task_repo


router = APIRouter(prefix='/calendar')
templates = Jinja2Templates(directory="templates")


@router.get("", name="calendar_view")
async def calendar_view(
    request: Request,
    year: int = Query(default=datetime.today().year),
    month: int = Query(default=datetime.today().month),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user()),
    meeting_repo: MeetingRepository = Depends(get_meeting_repo),
    task_repo: TaskRepository = Depends(get_task_repo)
):
    today = date.today()
    current_date = date(year, month, 1)

    # Диапазон дат месяца
    month_start = datetime(year, month, 1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    month_end = next_month - timedelta(seconds=1)

    # Встречи
    meetings = await meeting_repo.get_meeting_with_date(
        session, month_start, month_end, current_user.id
    )

    tasks = await task_repo.get_task_with_date(
        session, current_user.id, month_start, month_end
    )

    events_by_day = {}

    for meeting in meetings:
        day_key = meeting.date.date()
        events_by_day.setdefault(day_key, []).append({
            "title": meeting.description[:30],
            "time": meeting.date.strftime("%H:%M"),
            "type": "meeting",
        })

    for task in tasks:
        day_key = task.deadline.date()
        events_by_day.setdefault(day_key, []).append({
            "title": task.description[:30],
            "time": task.deadline.strftime("%H:%M"),
            "type": "task",
        })

    cal = calendar.Calendar(firstweekday=0)
    month_weeks = cal.monthdatescalendar(year, month)

    calendar_grid = []
    for week in month_weeks:
        week_data = []
        for day in week:
            day_events = (
                events_by_day.get(day, []) if day.month == month else None
            )
            week_data.append({
                "date": day if day.month == month else None,
                "events": day_events
            })
        calendar_grid.append(week_data)

    upcoming_meetings = await meeting_repo.get_meeting_with_date(
        session, today, today + timedelta(days=7), current_user.id
    )

    upcoming_tasks = await task_repo.get_task_with_date(
        session, current_user.id, today, today + timedelta(days=7)
    )

    upcoming_by_day = {}

    for meeting in upcoming_meetings:
        day_key = meeting.date.date()
        upcoming_by_day.setdefault(day_key, []).append({
            "title": meeting.description[:30],
            "time": meeting.date.strftime("%H:%M"),
            "type": "meeting",
        })

    for task in upcoming_tasks:
        day_key = task.deadline.date()
        upcoming_by_day.setdefault(day_key, []).append({
            "title": task.description[:30],
            "time": task.deadline.strftime("%H:%M"),
            "type": "task",
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
