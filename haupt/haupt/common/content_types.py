#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from enum import Enum


class ContentTypes(Enum):
    ORGANIZATION = "organization"
    TEAM = "team"
    USER = "user"
    PROJECT = "project"
    RUN = "run"
