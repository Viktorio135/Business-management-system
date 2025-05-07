from .database import Base
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime
from sqlalchemy_utils import ChoiceType
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash


class User(Base):
    __tablename__ = 'Пользователи'

    ROLE_CHOICES = [
        ('user', 'Пользоватль'),
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
    __tablename__ = 'Задача'

    STATUS_CHOICES = [
        ('open', 'Открыто'),
        ('in_work', 'В работе'),
        ('completed', 'Выполнено'),
    ]

    creator = Column(Integer, ForeignKey(User.id))
    performer = Column(Integer, ForeignKey(User.id))
    created_at = Column(DateTime, server_default=func.now())
    description = Column(Text)
    deadline = Column(DateTime)
    status = Column(ChoiceType(STATUS_CHOICES), default='open')
