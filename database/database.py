from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)
from typing import AsyncGenerator


DATABASE_URL = 'sqlite+aiosqlite:///db.sqlite3'

Base = declarative_base()

engine = create_async_engine(
    DATABASE_URL,
    pool_size=30,
    max_overflow=20,
    pool_recycle=3600
)

async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
