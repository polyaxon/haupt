#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from typing import Dict

from django.core.exceptions import BadRequest
from django.http import HttpRequest

from haupt.common import conf
from haupt.common.internal_auth import get_internal_auth
from haupt.common.options.registry.core import SECRET_INTERNAL_TOKEN


def validate_methods(request: HttpRequest, methods: Dict = None):
    if methods and request.method not in methods:
        raise BadRequest("Request method not allowed by this endpoint.")


def validate_internal_auth(request: HttpRequest):
    data = get_internal_auth(request=request)
    if data is None:
        raise BadRequest("Request requires an authenticated internal service.")

    if data[1] != conf.get(SECRET_INTERNAL_TOKEN):
        raise BadRequest("Request requires an authenticated internal service.")
