from fastapi import APIRouter, Form, HTTPException, Request, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse


from applications.auth.security import get_current_user
from database.models import User
from database.repositories import TeamRepository, UserRepository
from database.database import AsyncSession, get_db
from dependencies import get_team_repo, get_user_repo
from utils import render_template


router = APIRouter(prefix='/teams')
templates = Jinja2Templates(directory="templates")

get_current_user_dep = get_current_user()
get_current_user_dep_admin = get_current_user(admin=True)


@router.get('')
async def team_list_page(
    request: Request,
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    team_repo: TeamRepository = Depends(get_team_repo)
):
    teams = await team_repo.get_all(session)
    return render_template(
        request,
        templates,
        'team/teams_list.html',
        {"teams": teams},
        current_user
    )


@router.get('/create')
async def create_team_page(
    request: Request,
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repo),
):
    users = await user_repo.get_all(session)
    return render_template(
        request,
        templates,
        'team/create_team.html',
        {"users": users},
        current_user
    )


@router.post('/create')
async def create_team(
    name: str = Form(max_length=100),
    current_user: User = Depends(get_current_user_dep_admin),
    members: list[int] = Form(...),
    session: AsyncSession = Depends(get_db),
    team_repo: TeamRepository = Depends(get_team_repo)
):
    try:
        await team_repo.add(session, name, members)
    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))
    return RedirectResponse('/teams', status_code=status.HTTP_303_SEE_OTHER)


@router.get('/my_team')
async def my_team_page(
    request: Request,
    current_user: User = Depends(get_current_user_dep),
    session: AsyncSession = Depends(get_db),
    team_repo: TeamRepository = Depends(get_team_repo)
):
    team = await team_repo.get_user_team(
        session,
        current_user.id
    )
    if team:
        return render_template(
            request,
            templates,
            'team/team_detail.html',
            {"team": team},
            current_user
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail='Вы не состоите не в одной команде'
    )


@router.get('/{team_id}')
async def team_detail_page(
    request: Request,
    team_id: int,
    current_user: User = Depends(get_current_user_dep),
    session: AsyncSession = Depends(get_db),
    team_repo: TeamRepository = Depends(get_team_repo),
    user_repo: UserRepository = Depends(get_user_repo)
):
    team = await team_repo.get(session, team_id)
    all_users = await user_repo.get_all(session)
    team_member_ids = {member.user.id for member in team.user_teams}
    available_users = [u for u in all_users if u.id not in team_member_ids]
    return render_template(
        request,
        templates,
        'team/team_detail.html',
        {"team": team, "available_users": available_users},
        current_user
    )


@router.post('/{team_id}/add_team_member')
async def add_team_member(
    team_id: int,
    user_id: int = Form(...),
    role: str = Form('staff'),
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    team_repo: TeamRepository = Depends(get_team_repo)
):
    try:
        await team_repo.add_member(
            session,
            team_id,
            user_id,
            role
        )
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return RedirectResponse(
        f'/teams/{team_id}',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post('/{team_id}/delete_team_member')
async def delete_team_member(
    team_id: int,
    user_id: int = Form(...),
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    team_repo: TeamRepository = Depends(get_team_repo)
):
    try:
        await team_repo.delete_member(
            session, team_id, user_id
        )
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return RedirectResponse(
        f'/teams/{team_id}',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post('/{team_id}/delete')
async def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    team_repo: TeamRepository = Depends(get_team_repo)
):
    try:
        await team_repo.delete(session, team_id)
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return RedirectResponse(
        '/teams',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post('/{team_id}/rename')
async def rename_team(
    team_id: int,
    name: str = Form(..., max_length=100),
    current_user: User = Depends(get_current_user_dep_admin),
    session: AsyncSession = Depends(get_db),
    team_repo: TeamRepository = Depends(get_team_repo)
):
    try:
        await team_repo.update(session, team_id, {"name": name})
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return RedirectResponse(
        f'/teams/{team_id}',
        status_code=status.HTTP_303_SEE_OTHER
    )
