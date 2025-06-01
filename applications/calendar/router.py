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


router = APIRouter(prefix='/calendar', tags=["Calendar"])
templates = Jinja2Templates(directory="templates")

get_current_user_dep = get_current_user()


def format_event(event, date_getter, event_type: str):
    return {
        "title": event.description[:30],
        "time": date_getter(event).strftime("%H:%M"),
        "type": event_type,
    }


def group_events_by_day(events, date_getter, event_type: str):
    grouped = {}
    for event in events:
        day_key = date_getter(event).date()
        grouped.setdefault(day_key, []).append(
            format_event(event, date_getter, event_type)
        )
    return grouped


@router.get("", name="calendar_view")
async def calendar_view(
    request: Request,
    year: int = Query(default=date.today().year),
    month: int = Query(default=date.today().month),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep),
    meeting_repo: MeetingRepository = Depends(get_meeting_repo),
    task_repo: TaskRepository = Depends(get_task_repo)
):
    today = date.today()
    current_date = date(year, month, 1)

    # Диапазон дат месяца
    month_start = datetime(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    month_end = datetime(year, month, last_day)

    # Встречи
    meetings = await meeting_repo.get_meeting_with_date(
        session, month_start, month_end, current_user.id
    )

    tasks = await task_repo.get_task_with_date(
        session, current_user.id, month_start, month_end
    )

    events_by_day = {}
    events_by_day.update(group_events_by_day(
        meetings, lambda m: m.date, "meeting"
    ))
    events_by_day.update(group_events_by_day(
        tasks, lambda t: t.deadline, "task"
    ))

    # Создаём календарную сетку
    cal = calendar.Calendar(firstweekday=0)
    month_weeks = cal.monthdatescalendar(year, month)

    calendar_grid = []
    for week in month_weeks:
        week_data = []
        for day in week:
            is_current_month = day.month == month
            week_data.append({
                "date": day if is_current_month else None,
                "events": (
                    events_by_day.get(day, []) if is_current_month else None
                )
            })
        calendar_grid.append(week_data)

    # Предстоящие события (на 7 дней вперёд)
    upcoming_range_end = today + timedelta(days=7)
    upcoming_meetings = await meeting_repo.get_meeting_with_date(
        session, today, upcoming_range_end, current_user.id
    )
    upcoming_tasks = await task_repo.get_task_with_date(
        session, current_user.id, today, upcoming_range_end
    )

    upcoming_by_day = {}
    upcoming_by_day.update(group_events_by_day(
        upcoming_meetings, lambda m: m.date, "meeting"
    ))
    upcoming_by_day.update(group_events_by_day(
        upcoming_tasks, lambda t: t.deadline, "task"
    ))

    upcoming_list = []
    for offset in range(7):
        d = today + timedelta(days=offset)
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
            "next_month": (current_date + timedelta(
                days=calendar.monthrange(
                    current_date.year, current_date.month
                )[1])
            ).replace(day=1),
            "upcoming_events": upcoming_list,
        },
        user=current_user
    )
