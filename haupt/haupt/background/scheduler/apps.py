#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    name = "haupt.background.scheduler"
    verbose_name = "Scheduler"

    def ready(self):
        import haupt.db.signals.runs  # noqa
        from haupt.common import auditor, conf
        from haupt.orchestration import executor, operations

        conf.validate_and_setup()
        operations.validate_and_setup()
        executor.validate_and_setup()
        auditor.validate_and_setup()

        import haupt.common.options.conf_subscriptions  # noqa
        from haupt.common.events import auditor_subscriptions  # noqa
