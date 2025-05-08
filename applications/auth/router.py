from fastapi import APIRouter, Depends, status, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from datetime import timedelta


from .schemas import Token, RegUserModel, UserOut
from database.repositories import UserRepository
from database.database import get_db, AsyncSession
from .security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from dependencies import get_user_repo


router = APIRouter(prefix='/auth')
templates = Jinja2Templates(directory="templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.get('/login', response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error
    })


@router.post("/login", response_model=Token)
async def login(response: Response,
                form_data: OAuth2PasswordRequestForm = Depends(),
                user_repo: UserRepository = Depends(get_user_repo),
                session: AsyncSession = Depends(get_db)):
    user = await user_repo.is_auth(
        session, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        secure=False,
        samesite="Lax"
    )

    return RedirectResponse(
        "/users/profile", status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, error: str = None):
    return templates.TemplateResponse("register.html", {
        "request": request,
        "error": error
    })


@router.post('/register', response_model=UserOut)
async def reg_user(
    reg_form: RegUserModel,
    user_repo: UserRepository = Depends(get_user_repo),
    session: AsyncSession = Depends(get_db)
):
    try:
        await user_repo.create_user(session, {
            "name": reg_form.name,
            "lastname": reg_form.lastname,
            "email": reg_form.email,
            "password": reg_form.password1,
            "role": reg_form.role
        })
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    return RedirectResponse("/auth/login")


@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return RedirectResponse("/auth/login")
