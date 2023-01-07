#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.background.celeryp.queues import CeleryCoreQueues
from haupt.background.celeryp.tasks import CoreSchedulerCeleryTasks

SCHEDULER_CORE_ROUTES = {
    # Scheduler health
    CoreSchedulerCeleryTasks.SCHEDULER_HEALTH: {
        "queue": CeleryCoreQueues.SCHEDULER_HEALTH
    },
    # compiler
    CoreSchedulerCeleryTasks.RUNS_PREPARE: {
        "queue": CeleryCoreQueues.SCHEDULER_COMPILER
    },
    CoreSchedulerCeleryTasks.RUNS_START: {"queue": CeleryCoreQueues.SCHEDULER_COMPILER},
    CoreSchedulerCeleryTasks.RUNS_BUILT: {"queue": CeleryCoreQueues.SCHEDULER_COMPILER},
    # Scheduler runs
    CoreSchedulerCeleryTasks.RUNS_STOP: {"queue": CeleryCoreQueues.SCHEDULER_RUNS},
    CoreSchedulerCeleryTasks.RUNS_DELETE: {"queue": CeleryCoreQueues.SCHEDULER_RUNS},
    # Scheduler artifacts
    CoreSchedulerCeleryTasks.RUNS_SET_ARTIFACTS: {
        "queue": CeleryCoreQueues.SCHEDULER_ARTIFACTS,
        "priority": 0,
    },
}


def get_routes():
    routes = {}
    routes.update(SCHEDULER_CORE_ROUTES)
    return routes
