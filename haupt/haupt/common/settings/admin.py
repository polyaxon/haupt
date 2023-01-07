#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.config_manager import ConfigManager


def set_admin(context, config: ConfigManager):
    admin_name = config.get_string("POLYAXON_ADMIN_NAME", is_optional=True)
    admin_mail = config.get_string("POLYAXON_ADMIN_MAIL", is_optional=True)

    if admin_mail and admin_mail:
        admins = ((admin_name, admin_mail),)
        context["ADMINS"] = admins
        context["MANAGERS"] = admins
