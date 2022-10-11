#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

# isort: skip_file

from django.apps import AppConfig

from haupt.streams.connections.fs import AppFS


class StreamsConfig(AppConfig):
    name = "haupt.streams"
    verbose_name = "Streams"

    # async def ready(self): TODO
    #     await AppFS.set_fs()
