from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException


from .schemas import Token, RegUserModel, UserOut
from database.repositories import UserRepository
from database.database import get_db, AsyncSession

router = APIRouter(prefix='/auth')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_user_repo():
    return UserRepository()


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
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
    return {"access_token": "fake-jwt-token", "token_type": "bearer"}


@router.get("/profile")
async def read_profile(token: str = Depends(oauth2_scheme)):
    if token != "fake-jwt-token":
        raise HTTPException(status_code=401, detail="Неверный токен")
    return {"username": "test", "status": "logged in"}


@router.post('/reg', response_model=UserOut)
async def reg_user(
    reg_form: RegUserModel,
    user_repo: UserRepository = Depends(get_user_repo),
    session: AsyncSession = Depends(get_db)
):
    try:
        new_user = await user_repo.create_user(session, {
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

    return new_user
