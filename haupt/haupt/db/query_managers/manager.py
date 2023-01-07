#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.conf import settings
from django.db.models import Q

from polyaxon.pql.manager import PQLManager


class BaseQueryManager(PQLManager):
    QUERY_BACKEND = Q
    TIMEZONE = settings.TIME_ZONE
