from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException
from pydantic import EmailStr


from database.models import User
from database.database import AsyncSession, get_db
from database.repositories import UserRepository
from applications.auth.security import get_current_user, get_user_repo
from utils import render_template


router = APIRouter(prefix='/users')
templates = Jinja2Templates(directory="templates")


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: User = Depends(get_current_user())
):
    return render_template(
        request,
        templates,
        "user/profile.html",
        {},
        current_user
    )


@router.post('/edit')
async def profile_edit(
    current_user: User = Depends(get_current_user()),
    name: str = Form(..., max_length=20),
    lastname: str = Form(..., max_length=30),
    email: EmailStr = Form(...),
    new_password: Optional[str] = Form(default=None),
    user_repo: UserRepository = Depends(get_user_repo),
    session: AsyncSession = Depends(get_db)
):
    try:
        await user_repo.update(
            session,
            current_user.id,
            {
                "name": name,
                "lastname": lastname,
                "email": email
            }
        )
        if new_password:
            if (8 <= len(new_password) <= 128):
                await user_repo.update_password(
                    session,
                    current_user.id,
                    new_password
                )
            else:
                return HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Неверный пароль'
                )
        return RedirectResponse(
            '/users/profile',
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post('/delete')
async def profile_delete(
    current_user: User = Depends(get_current_user()),
    password: str = Form(...),
    user_repo: UserRepository = Depends(get_user_repo),
    session: AsyncSession = Depends(get_db)
):
    try:
        if not user_repo.is_auth(session, current_user.email, password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Неверный пароль'
            )

        await user_repo.delete(
            session,
            current_user.id
        )

        response = RedirectResponse(
            '/auth/login',
            status_code=status.HTTP_303_SEE_OTHER
        )
        response.delete_cookie("access_token")
        return response

    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
