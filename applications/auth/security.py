import os


from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from typing import Optional
from sqladmin.authentication import AuthenticationBackend
from dotenv import load_dotenv


from database.repositories import UserRepository
from database.database import get_db, AsyncSession, async_session_maker
from database.models import User
from dependencies import get_user_repo

load_dotenv()


SECRET_KEY = os.environ.get('SECRET_KEY')
ALGORITHM = os.environ.get('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES'))


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    need_auth: bool = True,
    admin: bool = False
):
    async def depends(
        request: Request,
        user_repo: UserRepository = Depends(get_user_repo),
        session: AsyncSession = Depends(get_db)
    ) -> Optional[User]:

        token = request.cookies.get("access_token")

        if not token:
            if need_auth:
                raise HTTPException(status_code=401, detail="Unauthorized")
            return None

        try:
            payload = jwt.decode(
                token.split(" ")[1],
                SECRET_KEY,
                algorithms=[ALGORITHM]
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=401, detail="Invalid credentials"
                )
        except (JWTError, IndexError, KeyError):
            if need_auth:
                raise HTTPException(status_code=401, detail="Unauthorized")
            return None

        user = await user_repo.get(session, int(user_id))
        if not user:
            if need_auth:
                raise HTTPException(status_code=401, detail="Unauthorized")
            return None

        if admin and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )

        return user

    return depends


class FastAPIAuthBackend(AuthenticationBackend):
    def __init__(self):
        super().__init__(secret_key=SECRET_KEY)

    async def login(self, request: Request) -> bool:
        return True

    async def authenticate(self, request: Request) -> bool:
        user_repo = UserRepository()
        async with async_session_maker() as session:
            current_user = get_current_user(need_auth=False, admin=False)
            current_user = await current_user(
                request,
                user_repo,
                session
            )
        if current_user:
            return True
        return False

    async def logout(self, request: Request) -> bool:
        return True
