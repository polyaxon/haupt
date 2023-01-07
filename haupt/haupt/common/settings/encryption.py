#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.config_manager import ConfigManager


def set_encryption(context, config: ConfigManager):
    context["ENCRYPTION_KEY"] = config.get_string(
        "POLYAXON_ENCRYPTION_KEY", is_optional=True
    )
    context["ENCRYPTION_SECRET"] = config.get_string(
        "POLYAXON_ENCRYPTION_SECRET", is_optional=True
    )
    context["ENCRYPTION_BACKEND"] = config.get_string(
        "POLYAXON_ENCRYPTION_BACKEND", is_optional=True
    )
