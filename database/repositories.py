from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (func, update as sqlalchemy_update,
                        delete as sqlalchemy_delete)
from sqlalchemy import select
from sqlalchemy.orm import selectinload


from .models import TaskChat, User, Task


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
        return True

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
    def __init__(self):
        super().__init__(model=User)

    async def is_auth(self, session: AsyncSession, email: str, password: str):
        result = await session.execute(
            select(self.model).where(self.model.email == email)
        )
        user = result.scalars().first()
        if user and user.check_password(password):
            return user
        return False

    async def create_user(self, session: AsyncSession, user_data: dict):
        result = await session.execute(
            select(self.model).where(self.model.email == user_data["email"])
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise ValueError("Пользователь с таким email уже существует")

        user = self.model(
            name=user_data["name"],
            lastname=user_data["lastname"],
            email=user_data["email"],
            role=user_data.get("role", "user"),
        )
        user.set_password(user_data["password"])

        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


class TaskRepository(BaseRepository):
    def __init__(self):
        super().__init__(model=Task)

    async def create_task(self, session: AsyncSession, task_data: dict):
        performer = await session.execute(
            select(User).where(
                User.id == task_data["performer"]
            )
        )
        performer = performer.scalars().first()
        if not performer:
            raise ValueError("Такого исполнителя не существует")
        task = self.model(
            creator=task_data["creator"].id,
            performer=performer.id,
            description=task_data["description"],
            deadline=task_data["deadline"]
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)

        return task

    async def get_all_user_tasks(self, session: AsyncSession, user_id: int):
        avg_assessment = func.avg(
            Task.assessment
        ).filter(
            Task.assessment.is_not(None)
        ).over().label("average_assessment")

        stmt = (
            select(Task, avg_assessment)
            .options(
                selectinload(Task.performer_user),
                selectinload(Task.creator_user)
            )
            .where((Task.creator == user_id) | (Task.performer == user_id))
        )

        result = await session.execute(stmt)

        rows = result.all()

        tasks = [row[0] for row in rows]
        average_assessment = (
            round(rows[0][1], 2)if rows and rows[0][1] is not None else None
        )

        return {
            "tasks": tasks,
            "avg": average_assessment
        }

    async def get_user_tasks(self, session: AsyncSession,
                             task_id: int, user_id: int):
        result = await session.execute(
            select(Task)
            .options(
                selectinload(Task.performer_user),
                selectinload(Task.creator_user),
                selectinload(Task.created_tasks).joinedload(TaskChat.user)
            )
            .where(
                (Task.id == task_id) &
                ((Task.creator == user_id) | (Task.performer == user_id))
            )
        )
        return result.scalars().first()

    async def update_status(self, session: AsyncSession,
                            task_id: int, task_status: str):
        task = await self.get(session, task_id)
        if not task:
            raise ValueError("Такого задания не существует")
        task.status = task_status
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

    async def update_assessment(self, session: AsyncSession,
                                task_id: int, assessment: int):
        task = await self.get(session, task_id)
        if not task:
            raise ValueError("Такого задания не существует")
        task.assessment = assessment
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


class TaskChatRepository(BaseRepository):
    def __init__(self):
        super().__init__(model=TaskChat)
