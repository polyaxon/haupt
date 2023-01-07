#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import pytest

from mock import mock

from haupt.background.scheduler.tasks.runs import runs_start
from haupt.db.factories.runs import RunFactory
from haupt.db.managers.statuses import new_run_status
from polyaxon.lifecycle import V1StatusCondition, V1Statuses
from tests.test_background.case import BaseTest


@pytest.mark.background_mark
class TestRunsStart(BaseTest):
    @mock.patch("polyaxon.agents.manager.start")
    def test_start_run_not_queued(self, manager_start):
        experiment = RunFactory(project=self.project, user=self.user)
        runs_start(run_id=experiment.id)
        assert manager_start.call_count == 0
        new_run_status(
            run=experiment,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.RUNNING, status=True
            ),
        )
        runs_start(run_id=experiment.id)
        assert manager_start.call_count == 0

    @mock.patch("haupt.orchestration.scheduler.manager.runs_start")
    def test_start_run(self, manager_start):
        experiment = RunFactory(project=self.project, user=self.user)
        new_run_status(
            run=experiment,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.COMPILED, status=True
            ),
        )
        runs_start(run_id=experiment.id)
        assert manager_start.call_count == 1
