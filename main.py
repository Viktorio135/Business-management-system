import os
import logging

from fastapi import FastAPI, HTTPException, Request, status
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv


from applications.admin_panel.admin import setup_admin

from applications.user.router import router as user_router
from applications.auth.router import router as auth_router
from applications.task.router import router as task_router
from applications.team.router import router as team_router
from applications.meeting.router import router as meeting_router
from applications.calendar.router import router as calendar_router
from applications.admin_panel.router import router as admin_router

from database.database import engine, Base


load_dotenv()
logger = logging.getLogger(__name__)


MODE = os.environ.get("MODE")


@asynccontextmanager
async def lifespan(app):
    if MODE == "DEV":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_handler(request: Request, exc: HTTPException):
    return RedirectResponse(
        "/auth/login", status_code=status.HTTP_303_SEE_OTHER
    )


@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "404 Not Found: %s %s",
        request.method,
        request.url.path,
        extra={
            "tags": ["http_404"],
            "client": request.client.host if request.client else None,
            "headers": dict(request.headers)
        }
    )
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=status.HTTP_404_NOT_FOUND
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    return templates.TemplateResponse(
        "errors/400.html",
        {"request": request, "error": exc.errors()},
        status_code=status.HTTP_400_BAD_REQUEST
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
):
    if exc.status_code == status.HTTP_403_FORBIDDEN:
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request},
            status_code=status.HTTP_403_FORBIDDEN
        )
    return templates.TemplateResponse(
        "errors/other.html",
        {"request": request, "error": exc},
        status_code=exc.status_code
    )


app.include_router(user_router)
app.include_router(auth_router)
app.include_router(task_router)
app.include_router(team_router)
app.include_router(meeting_router)
app.include_router(calendar_router)
app.include_router(admin_router)

setup_admin(app, engine)
