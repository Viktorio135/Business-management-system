from database.repositories import (UserRepository, TaskRepository,
                                   TaskChatRepository, TeamRepository,
                                   MeetingRepository)


def get_user_repo():
    return UserRepository()


def get_task_repo():
    return TaskRepository()


def get_taskchat_repo():
    return TaskChatRepository()


def get_team_repo():
    return TeamRepository()


def get_meeting_repo():
    return MeetingRepository()
