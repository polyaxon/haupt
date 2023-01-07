#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from polyaxon.fs.fs import get_default_fs
from polyaxon.fs.types import FSSystem


class AppFS:
    FS = None

    @classmethod
    async def set_fs(cls) -> FSSystem:
        fs = await get_default_fs()
        cls.FS = fs
        return cls.FS

    @classmethod
    async def close_fs(cls):
        if cls.FS and hasattr(cls.FS, "close_session"):
            cls.FS.close_session(cls.FS.loop, cls.FS.session)

    @classmethod
    async def get_fs(cls) -> FSSystem:
        if not cls.FS:
            return await cls.set_fs()
        return cls.FS
