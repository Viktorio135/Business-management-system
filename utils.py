from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import Response
from typing import Optional
from database.models import User  # замени на свой путь


def render_template(
    request: Request,
    templates: Jinja2Templates,
    template_name: str,
    context: dict,
    user: Optional[User] = None,
    status_code: int = 200
) -> Response:
    if user:
        context["user"] = {
            "name": user.name,
            "lastname": user.lastname,
            "email": user.email,
            "role": user.role
        }
    context["request"] = request
    return templates.TemplateResponse(
        template_name, context, status_code=status_code
    )
