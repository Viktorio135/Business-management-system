from database.repositories import (UserRepository, TaskRepository,
                                   TaskChatRepository, TeamRepository)


def get_user_repo():
    return UserRepository()


def get_task_repo():
    return TaskRepository()


def get_taskchat_repo():
    return TaskChatRepository()


def get_team_repo():
    return TeamRepository()
