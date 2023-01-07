#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.apps import AppConfig


class CommonApisConfig(AppConfig):
    name = "haupt.common.apis"
    verbose_name = "commonApis"
    label = "commonApis"
