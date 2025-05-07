from fastapi import FastAPI
from contextlib import asynccontextmanager
from applications.admin.admin import setup_admin

from database.database import engine, Base


@asynccontextmanager
async def lifespan(app):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    setup_admin(app, engine)

    yield


app = FastAPI()
