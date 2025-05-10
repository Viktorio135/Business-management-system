from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncEngine
from .views import UserAdmin, TaskAdmin, TeamAdmin


def setup_admin(app, engine: AsyncEngine):
    admin = Admin(
        app,
        engine,
        title="Admin Panel",
        base_url="/admin",
        logo_url="https://example.com/logo.png"
    )

    admin.add_view(UserAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(TeamAdmin)

    return admin
