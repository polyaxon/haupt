#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

# isort: skip_file

from django.apps import AppConfig


class APIsConfig(AppConfig):
    name = "haupt.apis"
    verbose_name = "APIs"

    def ready(self):
        from haupt.common import conf
        from haupt.common import auditor
        from haupt.orchestration import executor, operations
        from haupt.common import query

        conf.validate_and_setup()
        query.validate_and_setup()
        operations.validate_and_setup()
        executor.validate_and_setup()
        auditor.validate_and_setup()

        import haupt.db.signals.runs  # noqa

        import haupt.common.options.conf_subscriptions  # noqa
        from haupt.common.events import auditor_subscriptions  # noqa
        from haupt.db.administration import register  # noqa
