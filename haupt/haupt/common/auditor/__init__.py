#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.conf import settings

from common.auditor.manager import event_manager
from common.auditor.service import AuditorService
from common.service_interface import LazyServiceWrapper


def get_auditor_backend_path():
    return settings.AUDITOR_BACKEND or "common.auditor.service.AuditorService"


def get_auditor_options():
    return {
        "auditor_events_task": settings.AUDITOR_EVENTS_TASK,
        "workers_service": settings.WORKERS_SERVICE,
        "executor_service": settings.EXECUTOR_SERVICE or "db.executor",
    }


backend = LazyServiceWrapper(
    backend_base=AuditorService,
    backend_path=get_auditor_backend_path(),
    options=get_auditor_options(),
)
backend.expose(locals())

subscribe = event_manager.subscribe
