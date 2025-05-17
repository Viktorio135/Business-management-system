import os
from fastapi import APIRouter, Depends, Request, Response, Form, status
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from datetime import timedelta
from dotenv import load_dotenv


from applications.auth.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
)
from database.repositories import UserRepository
from database.database import get_db, AsyncSession
from dependencies import get_user_repo


load_dotenv()
SUPERADMIN_USERNAME = os.environ.get("SUPERADMIN_USERNAME")
SUPERADMIN_PASSWORD = os.environ.get("SUPERADMIN_PASSWORD")


router = APIRouter()


@router.post("/login")
async def admin_login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    user_repo: UserRepository = Depends(get_user_repo),
    session: AsyncSession = Depends(get_db)
):
    if username == SUPERADMIN_USERNAME and password == SUPERADMIN_PASSWORD:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": "superadmin"},
            expires_delta=access_token_expires
        )

        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return response

    user = await user_repo.is_auth(session, username, password)

    if not user or user.role != "admin":
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return RedirectResponse(
        url="/auth/login",
        status_code=status.HTTP_303_SEE_OTHER,
        headers=response.headers
    )
