#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from typing import Any

import redis


class BaseRedisDb:
    REDIS_POOL = None

    @classmethod
    def _get_redis(cls) -> Any:
        return redis.Redis(
            connection_pool=cls.REDIS_POOL, retry_on_timeout=True, socket_keepalive=True
        )

    @classmethod
    def connection(cls) -> Any:
        return cls._get_redis()
