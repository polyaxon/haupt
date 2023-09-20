from typing import Any, Optional, Tuple

from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework.authentication import get_authorization_header

from django.http import HttpRequest

from haupt.common import conf
from haupt.common.authentication.base import BaseUser, PolyaxonAuthentication
from haupt.common.headers import get_internal_header
from haupt.common.options.registry.core import SECRET_INTERNAL_TOKEN
from polyaxon._services.auth import AuthenticationTypes
from polyaxon._services.values import PolyaxonServices


class InternalUser(BaseUser):
    def __init__(self, service: str):
        self.username = "internal_user"
        self.is_internal = True
        super().__init__(service)

    @property
    def access_token(self) -> str:
        return conf.get(SECRET_INTERNAL_TOKEN)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, InternalUser) and other.username == self.username


def is_internal_user(user: Any) -> bool:
    return hasattr(user, "is_internal")


def is_authenticated_internal_user(user: Any) -> bool:
    if is_internal_user(user):
        return user.is_internal

    return False


class InternalAuthentication(PolyaxonAuthentication):
    """
    Simple authentication based on internal secret token.

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "InternalToken ".  For example:

        Authorization: InternalToken 401f7ac837da42b97f613d789819ff93537bee6a

    As well as one of the supported internal service. For example:

        X_POLYAXON_INTERNAL: experiments
    """

    keyword = AuthenticationTypes.INTERNAL_TOKEN

    def authenticate(
        self, request: HttpRequest
    ) -> Optional[Tuple["InternalUser", None]]:
        data = get_internal_auth(request=request, keyword=self.keyword)

        if data is None:
            return None

        internal_service, token = data
        return self.authenticate_credentials(internal_service, token)

    def authenticate_credentials(
        self, service: str, key: str  # pylint:disable=arguments-differ
    ) -> Optional[Tuple["InternalUser", None]]:
        internal_user = InternalUser(service=service)
        if internal_user.access_token != key:
            raise exceptions.AuthenticationFailed("Invalid token.")

        return internal_user, None


def get_internal_auth(
    request: HttpRequest, keyword: str = AuthenticationTypes.INTERNAL_TOKEN
) -> Optional[Tuple[str, str]]:
    auth = get_authorization_header(request).split()
    internal_service = get_internal_header(request)
    try:
        internal_service = internal_service.decode()
    except UnicodeError:
        msg = (
            "Invalid internal_service header. "
            "internal_service string should not contain invalid characters."
        )
        raise exceptions.AuthenticationFailed(msg)

    if internal_service not in PolyaxonServices.to_set():
        return None

    if not auth or auth[0].lower() != keyword.lower().encode(HTTP_HEADER_ENCODING):
        return None

    if len(auth) == 1:
        msg = "Invalid token header. No credentials provided."
        raise exceptions.AuthenticationFailed(msg)

    elif len(auth) > 2:
        msg = "Invalid token header. Token string should not contain spaces."
        raise exceptions.AuthenticationFailed(msg)

    try:
        token = auth[1].decode()
    except UnicodeError:
        msg = (
            "Invalid token header. Token string should not contain invalid characters."
        )
        raise exceptions.AuthenticationFailed(msg)

    return internal_service, token
