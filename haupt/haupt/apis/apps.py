#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

# isort: skip_file

from django.apps import AppConfig


class APIsConfig(AppConfig):
    name = "apis"
    verbose_name = "APIs"

    def ready(self):
        from common import conf
        from common import auditor
        from db import executor, operations
        from common import query

        conf.validate_and_setup()
        query.validate_and_setup()
        operations.validate_and_setup()
        executor.validate_and_setup()
        auditor.validate_and_setup()

        import db.signals.runs  # noqa

        import common.options.conf_subscriptions  # noqa
        from common.events import auditor_subscriptions  # noqa
        from db.administration import register  # noqa
