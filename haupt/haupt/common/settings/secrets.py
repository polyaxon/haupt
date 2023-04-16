#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.config_manager import ConfigManager
from polyaxon.env_vars.keys import EV_KEYS_SECRET_KEY


def set_secrets(context, config: ConfigManager):
    context["SECRET_KEY"] = config.get(
        EV_KEYS_SECRET_KEY,
        "str",
        is_secret=True,
        is_optional=True,
        default="default-secret",
    )
    context["SECRET_INTERNAL_TOKEN"] = config.get(
        "POLYAXON_SECRET_INTERNAL_TOKEN", "str", is_secret=True, is_optional=True
    )
