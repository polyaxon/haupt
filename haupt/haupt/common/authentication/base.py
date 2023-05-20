from typing import Any

from rest_framework.authentication import BasicAuthentication

from django.contrib.auth import get_user_model
from django.http import HttpRequest

from polyaxon.services.auth import AuthenticationError, AuthenticationTypes
from polyaxon.services.values import PolyaxonServices


class PolyaxonAuthentication(BasicAuthentication):
    keyword = None

    def __init__(self) -> None:
        if self.keyword not in AuthenticationTypes.VALUES:
            raise AuthenticationError(
                "Authentication bad configuration, "
                "the keyword `{}` is not supported.".format(self.keyword)
            )

    def authenticate_header(self, request: HttpRequest) -> str:
        return self.keyword


class BaseUser:
    NAME = ""

    def __init__(self, service: str):
        if service not in PolyaxonServices.to_set():
            raise ValueError("Received an unrecognized {} service.".format(self.NAME))
        self.pk = -1
        self.id = -1
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
        self.is_staff = False
        self.is_superuser = False
        self.service = service
        if not self.username:
            raise ValueError("username required")


def is_user(user: Any) -> bool:
    return isinstance(user, get_user_model())
