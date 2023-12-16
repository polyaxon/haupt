from clipped.utils.enums import get_enum_value

from django.http import HttpRequest

from polyaxon._services.headers import PolyaxonServiceHeaders

try:
    from rest_framework import HTTP_HEADER_ENCODING
except ImportError:
    raise ImportError("This module depends on django rest.")


POLYAXON_HEADERS_USER_ID = "X_POLYAXON_USER_ID"
POLYAXON_HEADERS_PUBLIC_ONLY = "X_POLYAXON_PUBLIC_ONLY"


def get_header(request: HttpRequest, header_key: str, as_bytestring: bool = False):
    """Return request's 'X_POLYAXON_...:' header, as a str or bytestring.

    Hide some test client ickyness where the header can be unicode.
    """
    header = request.META.get("HTTP_{}".format(get_enum_value(header_key)), "")
    if isinstance(header, str) and as_bytestring:
        # Work around django test client oddness
        header = header.encode(HTTP_HEADER_ENCODING)
    return header


def get_service_header(request: HttpRequest):
    """Return request's 'X_POLYAXON_SERVICE:' header, as a bytestring."""
    return get_header(
        request=request, header_key=PolyaxonServiceHeaders.SERVICE, as_bytestring=True
    )


def get_internal_header(request: HttpRequest) -> str:
    """
    Return request's 'X_POLYAXON_INTERNAL:' header, as a bytestring.
    """
    return get_header(
        request=request, header_key=PolyaxonServiceHeaders.INTERNAL, as_bytestring=True
    )


def get_original_uri_header(request: HttpRequest) -> str:
    """
    Return request's 'X_ORIGIN_URI:' header, as a str.
    """
    return get_header(request=request, header_key="X_ORIGIN_URI", as_bytestring=False)


def get_original_method_header(request: HttpRequest) -> str:
    """
    Return request's 'X_ORIGIN_METHOD:' header, as a str.
    """
    return get_header(
        request=request, header_key="X_ORIGIN_METHOD", as_bytestring=False
    )


def get_user_agent_header(request: HttpRequest) -> str:
    """
    Return request's 'USER_AGENT:' header, as a str.
    """
    return get_header(request=request, header_key="USER_AGENT", as_bytestring=False)


def get_referrer_header(request: HttpRequest) -> str:
    """
    Return request's 'REFERER:' header, as a str.
    """
    return get_header(request=request, header_key="REFERER", as_bytestring=False)


def get_authorization_header(request: HttpRequest) -> str:
    """
    Return request's 'AUTHORIZATION:' header, as a str.
    """
    return get_header(request=request, header_key="AUTHORIZATION", as_bytestring=False)


def get_remote_client_ip(request: HttpRequest) -> str:
    x_forwarded_for = get_header(
        request=request, header_key="X_FORWARDED_FOR", as_bytestring=False
    )
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
