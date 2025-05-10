from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from typing import Optional


from database.repositories import UserRepository
from database.database import get_db, AsyncSession
from database.models import User
from dependencies import get_user_repo


SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 360


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
                raise HTTPException(
                    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                    headers={"Location": "/auth/login"}
                )
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
                raise HTTPException(
                    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                    headers={"Location": "/auth/login"}
                )
            return None

        user = await user_repo.get(session, int(user_id))
        if not user:
            if need_auth:
                raise HTTPException(
                    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                    headers={"Location": "/auth/login"}
                )
            return None

        if admin and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )

        return user

    return depends
