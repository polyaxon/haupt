#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.schemas.platform_config import PlatformConfig


def set_encryption(context, config: PlatformConfig):
    context["ENCRYPTION_KEY"] = config.encryption_key
    context["ENCRYPTION_SECRET"] = config.encryption_secret
    context["ENCRYPTION_BACKEND"] = config.encryption_backend
