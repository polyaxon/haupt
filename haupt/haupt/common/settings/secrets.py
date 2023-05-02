#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.schemas.platform_config import PlatformConfig


def set_secrets(context, config: PlatformConfig):
    context["SECRET_KEY"] = config.secret_key
    context["SECRET_INTERNAL_TOKEN"] = config.secret_internal_token
