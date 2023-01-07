#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import logging

from typing import Dict, List

from haupt.background.celeryp.tasks import CoreSchedulerCeleryTasks
from haupt.common import workers
from haupt.orchestration.scheduler import manager
from haupt.polyconf.settings import Intervals

_logger = logging.getLogger("polyaxon.scheduler")


@workers.app.task(name=CoreSchedulerCeleryTasks.RUNS_PREPARE, ignore_result=True)
def runs_prepare(run_id):
    if manager.runs_prepare(run_id=run_id, run=None):
        workers.send(CoreSchedulerCeleryTasks.RUNS_START, kwargs={"run_id": run_id})


@workers.app.task(name=CoreSchedulerCeleryTasks.RUNS_START, ignore_result=True)
def runs_start(run_id):
    manager.runs_start(run_id=run_id, run=None)


@workers.app.task(name=CoreSchedulerCeleryTasks.RUNS_BUILT, ignore_result=True)
def runs_built(run_id):
    # Move to CE
    return run_id


@workers.app.task(name=CoreSchedulerCeleryTasks.RUNS_SET_ARTIFACTS, ignore_result=True)
def runs_set_artifacts(run_id, artifacts: List[Dict]):
    manager.runs_set_artifacts(run_id=run_id, run=None, artifacts=artifacts)


@workers.app.task(
    name=CoreSchedulerCeleryTasks.RUNS_STOP,
    bind=True,
    max_retries=3,
    ignore_result=True,
)
def runs_stop(self, run_id, update_status=False, message=None):
    stopped = manager.runs_stop(
        run_id=run_id, run=None, update_status=update_status, message=message
    )
    if not stopped and self.request.retries < 2:
        _logger.info("Trying again to delete job `%s` in run.", run_id)
        self.retry(countdown=Intervals.RUNS_SCHEDULER)
        return


@workers.app.task(name=CoreSchedulerCeleryTasks.RUNS_DELETE, ignore_result=True)
def runs_delete(run_id):
    manager.runs_delete(run_id=run_id, run=None)
