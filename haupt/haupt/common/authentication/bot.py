from typing import Any

from haupt.common.authentication.base import BaseUser


class BotUser(BaseUser):
    NAME = "bot"

    def __init__(self, service: str, username: str):
        self.username = username
        self.is_bot = True
        self.is_sa = False
        super().__init__(service)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, BotUser) and other.username == self.username


def is_bot_user(user: Any) -> bool:
    return getattr(user, "is_bot", False)


def is_sa_user(user: Any) -> bool:
    return getattr(user, "is_sa", False)


def is_bot_or_sa_user(user: Any) -> bool:
    return is_bot_user(user) or is_sa_user(user)


def is_authenticated_bot_user(user: Any) -> bool:
    if is_bot_user(user):
        return user.is_bot

    return False


def is_authenticated_service_account(user: Any) -> bool:
    if is_sa_user(user):
        return user.is_sa

    return False
