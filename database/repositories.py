from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete
from sqlalchemy import select


from .models import User


class BaseRepository:
    def __init__(self, model):
        self.model = model

    async def get(self, session: AsyncSession, id: int):
        result = await session.execute(
            select(self.model).where(
                self.model.id == id
            )
        )
        return result.scalars().first()

    async def get_all(self, session: AsyncSession):
        result = await session.execute(
            select(self.model)
        )
        return result.scalars().all()

    async def add(self, session: AsyncSession, obj_in: dict):
        obj = self.model(**obj_in)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def update(self, session: AsyncSession,
                     id: int, obj_in: Dict[str, Any]):
        await session.execute(
            sqlalchemy_update(self.model)
            .where(self.model.id == id)
            .values(**obj_in)
        )
        await session.commit()
        return await self.get(session, id)

    async def delete(self, session: AsyncSession, id: int):
        await session.execute(
            sqlalchemy_delete(self.model).where(self.model.id == id)
        )
        await session.commit()

    async def filter_by(self, session: AsyncSession, **kwargs):
        result = await session.execute(
            select(self.model).filter_by(**kwargs)
        )
        return result.scalars().all()


class UserRepository(BaseRepository):
    def __init__(self, model):
        super().__init__(model=User)

    async def is_auth(self, session: AsyncSession, email: str, password: str):
        result = await session.execute(
            select(self.model).where(self.model.email == email)
        )
        user = result.scalars().first()
        if user and user.check_password(password):
            return user
        return False
