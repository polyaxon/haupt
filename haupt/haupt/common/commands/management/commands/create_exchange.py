#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options) -> None:
        from haupt.common import workers
        from kombu import Exchange

        Exchange(
            "internal", type="topic", channel=workers.app.connection().channel()
        ).declare()
