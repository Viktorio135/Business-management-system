from database.repositories import UserRepository, TaskRepository


def get_user_repo():
    return UserRepository()


def get_task_repo():
    return TaskRepository()
