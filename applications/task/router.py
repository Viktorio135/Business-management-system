import datetime

from fastapi import APIRouter, Form, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates


from database.database import AsyncSession, get_db
from database.repositories import TaskRepository, UserRepository
from database.models import User
from dependencies import get_task_repo, get_user_repo
from applications.auth.security import get_current_user


router = APIRouter(prefix='/tasks')
templates = Jinja2Templates(directory="templates")


@router.get('')
async def tasks_list_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    task_repo: TaskRepository = Depends(get_task_repo),
    session: AsyncSession = Depends(get_db)
):
    if not current_user:
        return RedirectResponse("/auth/login")

    tasks = await task_repo.get_all_user_tasks(session, current_user.id)

    return templates.TemplateResponse("task/tasks_list.html", {
        "request": request,
        "user": {
            "name": current_user.name,
            "lastname": current_user.lastname,
            "email": current_user.email,
            "role": current_user.role
        },
        "tasks": tasks

    })


@router.get('/create', response_class=HTMLResponse)
async def create_task_page(request: Request, error: str = None,
                           current_user: User = Depends(get_current_user),
                           user_repo: UserRepository = Depends(get_user_repo),
                           session: AsyncSession = Depends(get_db)):
    if not current_user:
        return RedirectResponse(
            "/auth/login", status_code=status.HTTP_303_SEE_OTHER
        )
    if current_user.role not in ['admin', 'manager']:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    users = await user_repo.get_all(session)

    return templates.TemplateResponse("task/create_task.html", {
        "request": request,
        "error": error,
        "users": users,
        "user": {
            "name": current_user.name,
            "lastname": current_user.lastname,
            "email": current_user.email,
            "role": current_user.role
        }
    })


@router.post('/create')
async def create_router(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repo),
    performer: int = Form(...),
    description: str = Form(...),
    deadline: datetime.datetime = Form(...),
    task_repo: TaskRepository = Depends(get_task_repo),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role not in ['admin', 'manager']:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    try:
        await task_repo.create_task(session, {
            "creator": current_user,
            "performer": performer,
            "description": description,
            "deadline": deadline
        })
    except ValueError as e:
        users = await user_repo.get_all_with_user(session)
        return templates.TemplateResponse(
            "task/create_task.html",
            {
                "request": request,
                "error": str(e),
                "users": users,
                "user": {
                    "name": current_user.name,
                    "lastname": current_user.lastname,
                    "email": current_user.email,
                    "role": current_user.role
                }
            },
            status_code=400
        )
    return RedirectResponse(
        "/tasks",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get('/{task_id}')
async def task_detail_page(
    task_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
    task_repo: TaskRepository = Depends(get_task_repo),
    current_user: User = Depends(get_current_user)
):

    task = await task_repo.get_user_tasks(session, task_id, current_user.id)

    if not task:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return templates.TemplateResponse("task/task_detail.html", {
        "request": request,
        "user": {
            "name": current_user.name,
            "lastname": current_user.lastname,
            "email": current_user.email,
            "role": current_user.role
        },
        "task": task
    })


@router.get('/{task_id}/change_status')
async def change_status(
    task_id: int,
    task_status: str,
    session: AsyncSession = Depends(get_db),
    task_repo: TaskRepository = Depends(get_task_repo),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(
            "/auth/login", status_code=status.HTTP_303_SEE_OTHER
        )
    if current_user.role not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Forbidden")

    await task_repo.update_status(
        session, task_id, task_status
    )
    return RedirectResponse(
        f'/tasks/{task_id}',
        status_code=status.HTTP_303_SEE_OTHER
    )