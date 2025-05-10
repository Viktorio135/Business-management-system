from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


from database.models import User
from applications.auth.security import get_current_user
from utils import render_template


router = APIRouter(prefix='/users')
templates = Jinja2Templates(directory="templates")


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: User = Depends(get_current_user())
):
    return render_template(
        request,
        templates,
        "user/profile.html",
        {},
        current_user
    )
