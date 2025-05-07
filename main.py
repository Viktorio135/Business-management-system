from fastapi import FastAPI
from contextlib import asynccontextmanager
from applications.admin_panel.admin import setup_admin

from applications.user.router import router as user_router
from applications.auth.router import router as auth_router

from database.database import engine, Base


@asynccontextmanager
async def lifespan(app):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    setup_admin(app, engine)

    yield


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(auth_router)
