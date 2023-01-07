#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from rest_framework import status
from rest_framework.exceptions import APIException


class EndpointError(APIException):
    status_code = status.HTTP_501_NOT_IMPLEMENTED
