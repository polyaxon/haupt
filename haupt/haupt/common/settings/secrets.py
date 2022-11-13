#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.config_manager import ConfigManager


def set_secrets(context, config: ConfigManager):
    context["SECRET_KEY"] = config.get_string(
        "POLYAXON_SECRET_KEY",
        is_secret=True,
        is_optional=True,
        default="default-secret",
    )
    context["SECRET_INTERNAL_TOKEN"] = config.get_string(
        "POLYAXON_SECRET_INTERNAL_TOKEN", is_secret=True, is_optional=True
    )
