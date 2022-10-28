#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import pytest

from mock import mock

from haupt.background.scheduler.tasks.runs import runs_stop
from haupt.db.factories.runs import RunFactory
from polyaxon.lifecycle import V1Statuses
from tests.test_background.case import BaseTest


@pytest.mark.background_mark
class TestRunsStop(BaseTest):
    @mock.patch("haupt.orchestration.scheduler.manager.runs_stop")
    @mock.patch("haupt.orchestration.scheduler.manager.runs_prepare")
    def test_stop_managed_run(self, runs_prepare, managed_stop):
        with mock.patch("django.db.transaction.on_commit", lambda t: t()):
            managed_stop.return_value = True
            experiment = RunFactory(
                project=self.project,
                user=self.user,
                is_managed=True,
                raw_content="test",
            )
            assert runs_prepare.call_count == 1
            experiment.refresh_from_db()
            assert experiment.status == V1Statuses.CREATED
            runs_stop(run_id=experiment.id, update_status=True)
            assert managed_stop.call_count == 1

    def test_stop_non_managed_run(self):
        experiment = RunFactory(project=self.project, user=self.user, is_managed=False)
        runs_stop(run_id=experiment.id, update_status=True)
        experiment.refresh_from_db()
        assert experiment.status == V1Statuses.STOPPED

    @mock.patch("haupt.background.scheduler.tasks.runs_stop.retry")
    @mock.patch("haupt.orchestration.scheduler.manager.runs_stop")
    @mock.patch("haupt.orchestration.scheduler.resolver.resolve")
    def test_stop_managed_wrong_stop_retries(
        self, mock_resolve, managed_stop, mock_stop_run
    ):
        managed_stop.return_value = False
        experiment = RunFactory(
            project=self.project, user=self.user, is_managed=True, raw_content="test"
        )
        runs_stop(run_id=experiment.id)
        assert mock_stop_run.call_count == 1
        assert managed_stop.call_count == 1
        experiment.refresh_from_db()
        assert experiment.status == V1Statuses.CREATED
