import datetime

from fastapi import APIRouter, Form, Query, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates


from database.database import AsyncSession, get_db
from database.repositories import (TaskRepository, UserRepository,
                                   TaskChatRepository)
from database.models import User
from dependencies import get_task_repo, get_user_repo, get_taskchat_repo
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
    if current_user.role not in ['admin']:
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
async def create_task(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repo),
    performer: int = Form(...),
    description: str = Form(...),
    deadline: datetime.datetime = Form(...),
    task_repo: TaskRepository = Depends(get_task_repo),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role not in ['admin']:
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
    if not current_user:
        return RedirectResponse(
            "/auth/login", status_code=status.HTTP_303_SEE_OTHER
        )

    task = await task_repo.get_user_tasks(session, task_id, current_user.id)

    if current_user.id not in (task.creator, task.performer):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if not task:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND)

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

    await task_repo.update_status(
        session, task_id, task_status
    )
    return RedirectResponse(
        f'/tasks/{task_id}',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get('/{task_id}/change_assessment')
async def change_assessment(
    task_id: int, assessment: int = Query(ge=1, le=5),
    session: AsyncSession = Depends(get_db),
    task_repo: TaskRepository = Depends(get_task_repo),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(
            "/auth/login", status_code=status.HTTP_303_SEE_OTHER
        )
    await task_repo.update_assessment(
        session, task_id, assessment
    )
    return RedirectResponse(
        f'/tasks/{task_id}',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post('/{task_id}/delete')
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_db),
    task_repo: TaskRepository = Depends(get_task_repo),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(
            "/auth/login", status_code=status.HTTP_303_SEE_OTHER
        )
    task = await task_repo.get(session, task_id)
    if task and (task.creator == current_user.id):
        await task_repo.delete(session, task_id)

    return RedirectResponse(
        '/tasks',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get('/{task_id}/edit')
async def edit_task_page(
    request: Request,
    task_id:  int,
    session: AsyncSession = Depends(get_db),
    task_repo: TaskRepository = Depends(get_task_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(
            "/auth/login", status_code=status.HTTP_303_SEE_OTHER
        )
    task = await task_repo.get(session, task_id)
    if task and (task.creator == current_user.id):
        users = await user_repo.get_all(session)
        return templates.TemplateResponse("task/edit_task.html", {
            "request": request,
            "user": {
                "name": current_user.name,
                "lastname": current_user.lastname,
                "email": current_user.email,
                "role": current_user.role
            },
            "task": task,
            "status_choices": [
                ('open', 'Открыто'),
                ('in_work', 'В работе'),
                ('completed', 'Завершено')
            ],
            "users": users
        })
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@router.post('/{task_id}/edit')
async def edit_task(
    request: Request,
    task_id: int,
    description: str = Form(...),
    status: str = Form(...),
    performer: int = Form(...),
    deadline: datetime.datetime = Form(...),
    assessment: int = Form(...),
    session: AsyncSession = Depends(get_db),
    task_repo: TaskRepository = Depends(get_task_repo),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(
            "/auth/login", status_code=status.HTTP_303_SEE_OTHER
        )
    task = await task_repo.get(session, task_id)
    if task and (task.creator == current_user.id):
        try:
            await task_repo.update(
                session, task_id, {
                    "description": description,
                    "status": status,
                    "performer": performer,
                    "deadline": deadline,
                    "assessment": assessment
                }
            )
            return RedirectResponse(
                f'/tasks/{task_id}',
                status_code=303
            )
        except Exception as e:
            return HTTPException(
                status_code=400,
                detail=str(e)
            )


@router.post('/{task_id}/add_comment')
async def add_comment(
    task_id: int,
    message: str = Form(...),
    session: AsyncSession = Depends(get_db),
    taskchat_repo: TaskChatRepository = Depends(get_taskchat_repo),
    task_repo: TaskRepository = Depends(get_task_repo),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(
            "/auth/login", status_code=status.HTTP_303_SEE_OTHER
        )
    task = await task_repo.get(session, task_id)
    if task and (task.creator == current_user.id or
                 task.performer == current_user.id):
        try:
            await taskchat_repo.add(session, {
                "user_id": current_user.id,
                "task_id": task_id,
                "text": message
            })
            return RedirectResponse(
                    f'/tasks/{task_id}',
                    status_code=status.HTTP_303_SEE_OTHER
                )
        except Exception as e:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN
    )
