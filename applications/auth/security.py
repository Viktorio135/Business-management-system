from datetime import datetime, timedelta
from fastapi import Depends, Request
from jose import JWTError, jwt


from database.repositories import UserRepository
from database.database import get_db, AsyncSession
from dependencies import get_user_repo


SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(request: Request,
                           user_repo: UserRepository = Depends(get_user_repo),
                           session: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(
            token.split(" ")[1], SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except (JWTError, IndexError):
        return None

    return await user_repo.get(session, user_id)
