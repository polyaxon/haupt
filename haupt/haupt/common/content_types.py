#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from clipped.utils.enums import PEnum


class ContentTypes(str, PEnum):
    ORGANIZATION = "organization"
    TEAM = "team"
    USER = "user"
    PROJECT = "project"
    RUN = "run"
