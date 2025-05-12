from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException


from applications.admin_panel.admin import setup_admin

from applications.user.router import router as user_router
from applications.auth.router import router as auth_router
from applications.task.router import router as task_router
from applications.team.router import router as team_router
from applications.meeting.router import router as meeting_router

from database.database import engine, Base


@asynccontextmanager
async def lifespan(app):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    setup_admin(app, engine)

    yield


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=404
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    return templates.TemplateResponse(
        "errors/400.html",
        {"request": request},
        status_code=400
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
):
    if exc.status_code == 403:
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request},
            status_code=403
        )
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=exc.status_code
    )


app.include_router(user_router)
app.include_router(auth_router)
app.include_router(task_router)
app.include_router(team_router)
app.include_router(meeting_router)
