import logging

from urllib.parse import urlparse

from rest_framework import status

from django.http import HttpResponse

from polyaxon._sandbox.auth import derive_sandbox_token_from_env
from polyaxon.api import SANDBOX_V1_LOCATION
from polyaxon.exceptions import PolyaxonConverterError


logger = logging.getLogger("haupt.streams.sandbox")


def sandbox_check(uri: str) -> str:
    parsed_uri = urlparse(uri)
    if not parsed_uri.path.startswith(SANDBOX_V1_LOCATION):
        raise ValueError("A valid sandbox path param is required")

    uri_path = parsed_uri.path[len(SANDBOX_V1_LOCATION) :].split("/")
    if len(uri_path) < 6 or uri_path[3] != "runs":
        raise ValueError("A valid sandbox path param is required")

    run_uuid = uri_path[4]
    if not uri_path[0] or not run_uuid or not uri_path[5]:
        raise ValueError("A valid sandbox path param is required")
    return run_uuid


def reverse_sandbox(run_uuid: str) -> HttpResponse:
    try:
        token = derive_sandbox_token_from_env(run_uuid)
    except PolyaxonConverterError as e:
        logger.error("Sandbox token derivation failed: %s", e)
        return HttpResponse(
            content="Sandbox internal token not configured",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return HttpResponse(
        status=status.HTTP_200_OK,
        headers={
            "SANDBOX_TOKEN": token,
        },
    )
