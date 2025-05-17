from enum import Enum
from .database import Base
from sqlalchemy import (Column, String, Integer, ForeignKey, Text, DateTime,
                        )
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ChoiceType
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash


class UserRoleEnum(str, Enum):
    user = "user"
    admin = "admin"


ROLE_CHOICES = [(role.value, role.name) for role in UserRoleEnum]


class User(Base):
    __tablename__ = 'users'

    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('admin', 'Админ')
    ]

    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    lastname = Column(String(30))
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(
        ChoiceType(ROLE_CHOICES, impl=String(8)),
        default=UserRoleEnum.user.value
    )

    meeting_participants = relationship(
        'MeetingParticipant',
        back_populates='user'
    )

    meetings = relationship(
        "Meeting",
        secondary="meeting_participants",
        viewonly=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role_name(self):
        return dict(self.ROLE_CHOICES).get(self.role.code, 'Неизвестно')


class Task(Base):
    __tablename__ = 'tasks'

    STATUS_CHOICES = [
        ('open', 'Открыто'),
        ('in_work', 'В работе'),
        ('completed', 'Выполнено'),
    ]

    id = Column(Integer, primary_key=True)
    creator = Column(Integer, ForeignKey('users.id'))
    performer = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, server_default=func.now())
    description = Column(Text)
    deadline = Column(DateTime)
    status = Column(ChoiceType(STATUS_CHOICES), default='open')
    assessment = Column(Integer, nullable=True)

    @hybrid_property
    def performer_fullname(self):
        if self.performer_user:
            return f"{self.performer_user.name} {self.performer_user.lastname}"
        return "Не назначен"

    creator_user = relationship(
        "User", foreign_keys=[creator], backref='created_tasks'
    )
    performer_user = relationship(
        "User", foreign_keys=[performer], backref='assigned_tasks'
    )
    created_tasks = relationship(
        "TaskChat",
        back_populates="task",
        cascade="all, delete-orphan"
    )


class TaskChat(Base):
    __tablename__ = 'task_chat'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    text = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship(
        "User", foreign_keys=[user_id], backref='created_chats'
    )
    task = relationship(
        "Task",
        foreign_keys=[task_id],
        back_populates="created_tasks"
    )


class UserTeam(Base):
    __tablename__ = 'user_teams'

    ROLE_CHOICES = [
        ('staff', 'Сотрудник'),
        ('manager', 'Мэнеджер'),
    ]

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    team_id = Column(Integer, ForeignKey('teams.id'))
    role = Column(ChoiceType(ROLE_CHOICES), default='staff')

    user = relationship('User', backref='team_links')


class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    user_teams = relationship('UserTeam', backref='team')


class MeetingParticipant(Base):
    __tablename__ = 'meeting_participants'

    meeting_id = Column(Integer, ForeignKey('meeting.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    user = relationship('User', back_populates='meeting_participants')
    meeting = relationship('Meeting', back_populates='participants')


class Meeting(Base):
    __tablename__ = 'meeting'

    id = Column(Integer, primary_key=True)
    description = Column(Text)
    date = Column(DateTime)
    creator_id = Column(Integer, ForeignKey('users.id'))

    participants = relationship(
        "MeetingParticipant",
        back_populates="meeting"
    )

    creator = relationship("User", foreign_keys=[creator_id])
