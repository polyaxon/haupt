#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.polyconf.settings import PLATFORM_CONFIG

if PLATFORM_CONFIG.is_streams_service:
    from haupt.streams.patterns import *  # noqa
else:
    from haupt.apis.patterns import *  # noqa
