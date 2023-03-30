#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from typing import Optional, Tuple

from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework.authentication import get_authorization_header

from django.http import HttpRequest

from haupt.common.headers import get_internal_header
from polyaxon.services.auth import AuthenticationTypes
from polyaxon.services.values import PolyaxonServices


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
