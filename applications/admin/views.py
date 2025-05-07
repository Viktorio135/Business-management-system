from sqladmin import ModelView
from database.models import User, Task


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
    can_delete = False


class PostAdmin(ModelView, model=Task):
    name = "Задание"
    name_plural = "Задания"
    icon = "fa-solid fa-user"

    # column_list = [User.id, User.email, User.role]
    # column_searchable_list = [User.email]
    # column_sortable_list = [User.created_at]

    can_export = True
    can_create = True
    can_edit = True
    can_delete = False
