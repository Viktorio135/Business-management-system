from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates


from applications.auth.security import get_current_user
from database.models import User
from database.repositories import TeamRepository, UserRepository
from database.database import AsyncSession, get_db
from dependencies import get_team_repo, get_user_repo
from utils import render_template


router = APIRouter(prefix='/teams')
templates = Jinja2Templates(directory="templates")


@router.get('')
async def team_list_page(
    request: Request,
    current_user: User = Depends(get_current_user(admin=True)),
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
    current_user: User = Depends(get_current_user(admin=True)),
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


# @router.post()
