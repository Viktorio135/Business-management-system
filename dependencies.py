from database.repositories import UserRepository


def get_user_repo():
    return UserRepository()
