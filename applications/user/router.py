from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates


from database.models import User
from applications.auth.security import get_current_user


router = APIRouter(prefix='/users')
templates = Jinja2Templates(directory="templates")


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/auth/login")

    return templates.TemplateResponse("user/profile.html", {
        "request": request,
        "user": {
            "name": current_user.name,
            "lastname": current_user.lastname,
            "email": current_user.email,
            "role": current_user.role
        }
    })
