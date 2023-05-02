#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.schemas.platform_config import PlatformConfig


def set_admin(context, config: PlatformConfig):
    if config.admin_mail and config.admin_mail:
        admins = ((config.admin_name, config.admin_mail),)
        context["ADMINS"] = admins
        context["MANAGERS"] = admins
