from .database import Base
from sqlalchemy import (Column, String, Integer, ForeignKey, Text, DateTime,
                        )
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ChoiceType
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash


class User(Base):
    __tablename__ = 'users'

    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('admin', 'Админ'),
        ('manager', 'Мэнеджер'),
    ]

    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    lastname = Column(String(30))
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(ChoiceType(ROLE_CHOICES), default='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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

    creator_user = relationship(
        "User", foreign_keys=[creator], backref='created_tasks'
    )
    performer_user = relationship(
        "User", foreign_keys=[performer], backref='assigned_tasks'
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


class Meeting(Base):
    __tablename__ = 'meeting'

    id = Column(Integer, primary_key=True)
    description = Column(Text)
    date = Column(DateTime)
    user_metting = relationship('User', backref='meeting')
