from sqladmin import ModelView
from database.models import User, Task, Team


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"

    # column_list = [User.id, User.email, User.role]
    # column_searchable_list = [User.email]
    # column_sortable_list = [User.created_at]

    can_export = True
    can_create = True
    can_edit = True
    can_delete = True


class TaskAdmin(ModelView, model=Task):
    name = "Задача"
    name_plural = "Задачи"
    icon = "fa-solid fa-user"

    # column_list = [User.id, User.email, User.role]
    # column_searchable_list = [User.email]
    # column_sortable_list = [User.created_at]

    can_export = True
    can_create = True
    can_edit = True
    can_delete = True


class TeamAdmin(ModelView, model=Team):
    name = "Команды"
    name_plural = "Команды"
    icon = "fa-solid fa-user"

    # column_list = [User.id, User.email, User.role]
    # column_searchable_list = [User.email]
    # column_sortable_list = [User.created_at]

    can_export = True
    can_create = True
    can_edit = True
    can_delete = True
