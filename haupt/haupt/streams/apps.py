#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

# isort: skip_file

from django.apps import AppConfig


class StreamsConfig(AppConfig):
    name = "haupt.streams"
    verbose_name = "Streams"

    def ready(self):
        from haupt.common import conf

        conf.validate_and_setup()

        import haupt.common.options.conf_subscriptions  # noqa
