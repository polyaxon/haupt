#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

USER_ROOT = 1
USER_SYSTEM_ID = -1
USER_SYSTEM_NAME = "Polyaxon"


def is_system_user(user_id: int = None) -> bool:
    if user_id:
        return user_id == USER_SYSTEM_ID

    return False
