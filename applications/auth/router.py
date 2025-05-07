from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from pydantic import BaseModel


from database.repositories import UserRepository

router = APIRouter(prefix='/auth')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class Token(BaseModel):
    access_token: str
    token_type: str


def get_user_repo():
    return UserRepository()


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                user_repo: UserRepository = Depends(get_user_repo)):
    user = await user_repo.is_auth(form_data.username, form_data.password)
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
