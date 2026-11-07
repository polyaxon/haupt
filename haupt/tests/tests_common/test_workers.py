from mock import patch

from django.test import TestCase
from kombu.exceptions import OperationalError

from haupt.common import workers


# `app` and `OperationalError` only exist in `workers` when the scheduler is enabled.
@patch.object(workers, "OperationalError", OperationalError, create=True)
@patch.object(workers, "app", create=True)
class TestWorkersSend(TestCase):
    def test_send_publishes_task_on_commit(self, app):
        with self.captureOnCommitCallbacks(execute=True):
            workers.send("task", delay=True, kwargs={"run_id": 1})

        app.send_task.assert_called_once_with(
            "task", kwargs={"run_id": 1}, ignore_result=True
        )

    def test_send_drops_task_when_broker_unavailable(self, app):
        app.send_task.side_effect = OperationalError("Error 111 connecting to redis")

        with self.assertLogs("haupt.workers", level="WARNING") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                workers.send("task", delay=True, kwargs={"run_id": 1})

        app.send_task.assert_called_once()
        assert "task=task" in logs.output[0]
