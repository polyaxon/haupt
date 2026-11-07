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

        with patch.object(workers, "_run_eager") as run_eager:
            with self.assertLogs("haupt.workers", level="WARNING") as logs:
                with self.captureOnCommitCallbacks(execute=True):
                    workers.send("task", delay=True, kwargs={"run_id": 1})

        app.send_task.assert_called_once()
        run_eager.assert_not_called()
        assert "dropping task: task=task" in logs.output[0]

    def test_send_runs_task_eagerly_when_broker_unavailable(self, app):
        app.send_task.side_effect = OperationalError("Error 111 connecting to redis")

        with patch.object(workers, "_run_eager") as run_eager:
            with self.captureOnCommitCallbacks(execute=True):
                workers.send(
                    "task",
                    delay=True,
                    kwargs={"run_id": 1},
                    eager_kwargs={"run": "run"},
                    eager_fallback=True,
                )

        app.send_task.assert_called_once_with(
            "task", kwargs={"run_id": 1}, ignore_result=True
        )
        run_eager.assert_called_once_with("task", {"run_id": 1}, {"run": "run"})

    def test_send_logs_eager_fallback_failure(self, app):
        app.send_task.side_effect = OperationalError("Error 111 connecting to redis")

        with patch.object(workers, "_run_eager", side_effect=ValueError("boom")):
            with self.assertLogs("haupt.workers", level="ERROR") as logs:
                with self.captureOnCommitCallbacks(execute=True):
                    workers.send(
                        "task", delay=True, kwargs={"run_id": 1}, eager_fallback=True
                    )

        assert "Eager fallback failed: task=task" in logs.output[0]
