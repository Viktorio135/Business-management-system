import datetime
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (and_, func, update as sqlalchemy_update,
                        delete as sqlalchemy_delete)
from sqlalchemy import select
from sqlalchemy.orm import selectinload


from .models import (TaskChat, User, Task, Team, UserTeam,
                     Meeting, MeetingParticipant)


class BaseRepository:
    def __init__(self, model):
        self.model = model

    async def get(self, session: AsyncSession, id: int):
        result = await session.get(self.model, id)
        return result

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
        return user

    async def update_password(
        self, session: AsyncSession, user_id: int, new_password: str
    ):
        user = await self.get(session, user_id)
        if user:
            user.set_password(new_password)
            session.add(user)
            await session.commit()
            return user
        raise ValueError(
            "Такого пользователя не существует"
        )


class TaskRepository(BaseRepository):
    def __init__(self):
        super().__init__(model=Task)

    async def create_task(self, session: AsyncSession, task_data: dict):
        performer = await session.get(session, task_data["performer"])
        if not performer:
            raise ValueError("Такого исполнителя не существует")
        task = self.model(
            creator=task_data["creator"].id,
            performer=performer.id,
            description=task_data["description"],
            deadline=task_data["deadline"]
        )
        await session.commit()
        return task

    async def get_all_user_tasks(self, session: AsyncSession, user_id: int):
        avg_assessment_subq = (
            select(
                func.avg(Task.assessment)
                .filter(Task.assessment.is_not(None))
                .label("average_assessment")
            )
            .where((Task.creator == user_id) | (Task.performer == user_id))
        ).scalar_subquery()

        stmt = (
            select(
                Task,
                avg_assessment_subq
            )
            .options(
                selectinload(Task.performer_user),
                selectinload(Task.creator_user)
            )
            .where((Task.creator == user_id) | (Task.performer == user_id))
        )

        result = await session.execute(stmt)
        rows = result.all()

        if not rows:
            return {"tasks": [], "avg": None}

        tasks = [row[0] for row in rows]
        average_assessment = rows[0][1]

        return {
            "tasks": tasks,
            "avg": (
                float(average_assessment)
                if average_assessment is not None
                else None
            )
        }

    async def get_task_with_date(
        self, session: AsyncSession,
        user_id: int, month_start: datetime.datetime,
        month_end: datetime.datetime
    ):
        result = await session.execute(select(Task).where(
                and_(
                    Task.performer == user_id,
                    Task.deadline >= month_start,
                    Task.deadline <= month_end,
                    Task.status != "completed"
                )
            ).order_by(Task.deadline)
        )
        return result.scalars().all()

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


class TeamRepository(BaseRepository):
    def __init__(self):
        super().__init__(Team)

    async def add(self, session: AsyncSession,
                  name: str, members: Optional[list[int]] = None):
        team = Team(name=name)
        session.add(team)
        await session.flush()
        if members:
            for member in members:
                userteam = UserTeam(
                    user_id=member,
                    team_id=team.id,
                    role='staff'
                )
                session.add(userteam)
        await session.commit()
        return team

    async def delete(self, session: AsyncSession, team_id: int):
        await session.execute(
            sqlalchemy_delete(Team).where(Team.id == team_id)
        )
        await session.execute(
            sqlalchemy_delete(UserTeam).where(
                UserTeam.team_id == team_id
            )
        )
        await session.commit()

    async def get(self, session: AsyncSession, team_id: int):
        result = await session.execute(
            select(Team)
            .options(
                selectinload(Team.users)
            )
            .where(Team.id == team_id)
        )
        return result.scalars().first()

    async def add_member(self, session: AsyncSession,
                         team_id: int, user_id: int, role: str):
        userteam = UserTeam(
            user_id=user_id,
            team_id=team_id,
            role=role
        )
        session.add(userteam)
        await session.commit()
        return userteam

    async def delete_member(self, session: AsyncSession,
                            team_id: int, user_id: int):
        await session.execute(
            sqlalchemy_delete(UserTeam).where(
                (UserTeam.team_id == team_id) & (UserTeam.user_id == user_id)
            )
        )
        await session.commit()

    async def get_user_team(self, session: AsyncSession, user_id: int):
        result = await session.execute(
            select(Team)
            .options(
                selectinload(Team.user_teams).joinedload(UserTeam.user)
            )
            .where(UserTeam.user_id == user_id)
        )

        return result.scalars().first()


class MeetingRepository(BaseRepository):
    def __init__(self):
        super().__init__(Meeting)

    async def get(self, session: AsyncSession, meeting_id: int):
        result = await session.execute(
            select(Meeting)
            .options(
                selectinload(
                    Meeting.participants
                ).selectinload(MeetingParticipant.user)
            )
            .where(Meeting.id == meeting_id)
        )
        return result.scalars().first()

    async def get_all(self, session):
        result = await session.execute(
            select(Meeting)
            .where(Meeting.date > datetime.datetime.now())
        )
        return result.scalars().all()

    async def add(self, session: AsyncSession,
                  date: datetime.datetime,
                  description: str,
                  creator_id: int, members: Optional[list[int]] = None):
        meeting = Meeting(
            description=description,
            date=date, creator_id=creator_id
        )
        session.add(meeting)
        await session.flush()
        if members:
            for member in members:
                usermeeting = MeetingParticipant(
                    user_id=member,
                    meeting_id=meeting.id,
                )
                session.add(usermeeting)
        await session.commit()
        return meeting

    async def delete(self, session: AsyncSession, meeting_id: int):
        await session.execute(
            sqlalchemy_delete(Meeting).where(Meeting.id == meeting_id)
        )
        await session.execute(
            sqlalchemy_delete(MeetingParticipant).where(
                MeetingParticipant.meeting_id == meeting_id
            )
        )
        await session.commit()

    async def add_member(self, session: AsyncSession,
                         meeting_id: int, user_id: int):
        usermeeting = MeetingParticipant(
            user_id=user_id,
            meeting_id=meeting_id
        )
        session.add(usermeeting)
        await session.commit()
        return usermeeting

    async def delete_member(self, session: AsyncSession,
                            meeting_id: int, user_id: int):
        await session.execute(
            sqlalchemy_delete(MeetingParticipant).where(
                (MeetingParticipant.meeting_id == meeting_id) &
                (MeetingParticipant.user_id == user_id)
            )
        )
        await session.commit()

    async def get_meeting_with_date(
        self,
        session: AsyncSession,
        month_start: datetime,
        month_end: datetime,
        user_id: int  # <- передаём ID пользователя
    ):
        meetings_query = await session.execute(
            select(Meeting)
            .join(MeetingParticipant)
            .where(
                Meeting.date >= month_start,
                Meeting.date <= month_end,
                MeetingParticipant.user_id == user_id
            ).order_by(Meeting.date)
        )
        return meetings_query.scalars().all()
