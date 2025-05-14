import datetime
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse


from applications.auth.security import get_current_user
from database.models import User
from database.repositories import MeetingRepository, UserRepository
from database.database import AsyncSession, get_db
from dependencies import get_user_repo, get_meeting_repo
from utils import render_template


router = APIRouter(prefix='/meetings')
templates = Jinja2Templates(directory="templates")

get_current_user_dep = get_current_user()
get_current_user_dep_admin = get_current_user(admin=True)


@router.get('')
async def meeting_list_page(
    request: Request,
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    meeting_repo: MeetingRepository = Depends(get_meeting_repo)
):
    meetings = await meeting_repo.get_all(session)
    return render_template(
        request,
        templates,
        'meeting/meeting_list.html',
        {"meetings": meetings},
        current_user
    )


@router.get('/create')
async def create_meeting_page(
    request: Request,
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repo)
):
    users = await user_repo.get_all(session)
    return render_template(
        request,
        templates,
        'meeting/create_meeting.html',
        {"users": users},
        current_user
    )


@router.post('/create')
async def create_meeting(
    description: str = Form(...),
    members: list[int] = Form(...),
    date: datetime.datetime = Form(...),
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    meeting_repo: MeetingRepository = Depends(get_meeting_repo)
):
    try:
        await meeting_repo.add(
            session, date, description, current_user.id, members
        )
    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))
    return RedirectResponse('/meetings', status_code=status.HTTP_303_SEE_OTHER)


@router.get('/{meeting_id}')
async def meeting_detail_page(
    request: Request,
    meeting_id: int,
    current_user: User = Depends(get_current_user_dep),
    session: AsyncSession = Depends(get_db),
    meeting_repo: MeetingRepository = Depends(get_meeting_repo),
    user_repo: UserRepository = Depends(get_user_repo)
):
    meeting = await meeting_repo.get(session, meeting_id)
    all_users = await user_repo.get_all(session)
    meeting_member_ids = {member.user.id for member in meeting.participants}
    available_users = [u for u in all_users if u.id not in meeting_member_ids]
    return render_template(
        request,
        templates,
        'meeting/meeting_detail.html',
        {"meeting": meeting, "available_users": available_users},
        current_user
    )


@router.post('/{meeting_id}/add_meeting_member')
async def add_meeting_member(
    meeting_id: int,
    user_id: int = Form(...),
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    meeting_repo: MeetingRepository = Depends(get_meeting_repo)
):
    try:
        await meeting_repo.add_member(
            session,
            meeting_id,
            user_id
        )
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return RedirectResponse(
        f'/meetings/{meeting_id}',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post('/{meeting_id}/delete_meeting_member')
async def delete_meeting_member(
    meeting_id: int,
    user_id: int = Form(...),
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    meeting_repo: MeetingRepository = Depends(get_meeting_repo)
):
    try:
        await meeting_repo.delete_member(
            session, meeting_id, user_id
        )
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return RedirectResponse(
        f'/meetings/{meeting_id}',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post('/{meeting_id}/delete')
async def delete_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    meeting_repo: MeetingRepository = Depends(get_meeting_repo)
):
    try:
        await meeting_repo.delete(session, meeting_id)
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return RedirectResponse(
        '/meetings',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post('/{meeting_id}/edit')
async def edit_meeting(
    meeting_id: int,
    description: str = Form(...),
    date: datetime.datetime = Form(...),
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    meeting_repo: MeetingRepository = Depends(get_meeting_repo)
):
    try:
        await meeting_repo.update(session, meeting_id, {
            "description": description,
            "date": date
        })
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return RedirectResponse(
        f'/meetings/{meeting_id}',
        status_code=status.HTTP_303_SEE_OTHER
    )
