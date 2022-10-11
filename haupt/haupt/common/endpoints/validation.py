#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from typing import Dict

from django.core.exceptions import BadRequest
from django.http import HttpRequest


def validate_methods(request: HttpRequest, methods: Dict = None):
    if methods and request.method not in methods:
        raise BadRequest("Request method not allowed by this endpoint.")
