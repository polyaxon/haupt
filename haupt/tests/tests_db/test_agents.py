import datetime

from unittest.mock import patch

from django.conf import settings as dj_settings
from django.test import TestCase, override_settings
from django.utils.timezone import now

from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.managers.agents import (
    get_agent_state,
    get_annotated_controllers,
    get_annotated_pipelines,
    get_runs_by_controller,
    get_runs_by_pipeline,
)
from haupt.db.models.runs import Run
from polyaxon import _operations, settings
from polyaxon._connections import V1BucketConnection, V1Connection, V1ConnectionKind
from polyaxon._schemas.agent import AgentConfig
from polyaxon._utils.fqn_utils import get_run_instance
from polyaxon.schemas import LiveState, ManagedBy, V1Environment, V1RunKind, V1Statuses


class TestAgentState(TestCase):
    @override_settings(MIN_ARTIFACTS_DELETION_TIMEDELTA=-60)
    def test_get_agent_state(self):
        project = ProjectFactory()
        agent_config = AgentConfig(
            namespace="foo",
            artifacts_store=V1Connection(
                name="moo",
                kind=V1ConnectionKind.GCS,
                schema_=V1BucketConnection(bucket="gs//:foo"),
            ),
        )
        settings.AGENT_CONFIG = agent_config

        # No runs
        with patch("haupt.common.workers.send") as workers_send:
            state = get_agent_state()
        assert workers_send.call_count == 0
        assert state[V1Statuses.STOPPING] == []
        assert state[V1Statuses.QUEUED] == []
        assert state["deleting"] == []
        assert state["checks"] == []
        assert state["full"] is False

        # Runs without satisfying status
        run1 = RunFactory(
            project=project,
            kind=V1RunKind.JOB,
        )
        run1.managed_by = ManagedBy.AGENT
        run2 = RunFactory(
            project=project,
            kind=V1RunKind.JOB,
        )
        run2.managed_by = ManagedBy.AGENT
        run3 = RunFactory(
            project=project,
            kind=V1RunKind.SERVICE,
        )
        run3.managed_by = ManagedBy.AGENT
        run4 = RunFactory(
            project=project,
            kind=V1RunKind.TUNER,
        )
        run4.managed_by = ManagedBy.AGENT
        # Patch all runs to be managed
        Run.all.update(managed_by=ManagedBy.AGENT)

        with patch("haupt.common.workers.send") as workers_send:
            state = get_agent_state()
        assert workers_send.call_count == 0
        assert state[V1Statuses.STOPPING] == []
        assert state[V1Statuses.QUEUED] == []
        assert state["deleting"] == []
        assert state["checks"] == []
        assert state["full"] is False

        run1.status = V1Statuses.QUEUED
        run1.save()
        run2.status = V1Statuses.QUEUED
        run2.save()
        run3.status = V1Statuses.QUEUED
        run3.save()
        # Set concurrency to 1
        dj_settings.MAX_CONCURRENCY = 1
        with patch("haupt.common.workers.send") as workers_send:
            state = get_agent_state()
        assert workers_send.call_count == 0

        assert set(state[V1Statuses.QUEUED]) == {
            (
                get_run_instance("default", project.name, run1.uuid.hex),
                run1.runtime,
                run1.name,
                run1.content,
                None,
            )
        }
        assert state[V1Statuses.STOPPING] == []
        assert state["deleting"] == []
        assert state["checks"] == []
        assert state["full"] is False

        run1.refresh_from_db()
        run2.refresh_from_db()
        run3.refresh_from_db()
        assert run1.status == V1Statuses.SCHEDULED
        assert run2.status == V1Statuses.QUEUED
        assert run3.status == V1Statuses.QUEUED

        # Max concurrency at 100
        run1.status = V1Statuses.QUEUED
        run1.save()
        dj_settings.MAX_CONCURRENCY = 100
        with patch("haupt.common.workers.send") as workers_send:
            state = get_agent_state()
        assert workers_send.call_count == 0
        assert set(state[V1Statuses.QUEUED]) == {
            (
                get_run_instance("default", project.name, run1.uuid.hex),
                run1.runtime,
                run1.name,
                run1.content,
                None,
            ),
            (
                get_run_instance("default", project.name, run2.uuid.hex),
                run2.runtime,
                run2.name,
                run2.content,
                None,
            ),
            (
                get_run_instance("default", project.name, run3.uuid.hex),
                run3.runtime,
                run3.name,
                run3.content,
                None,
            ),
        }
        assert state[V1Statuses.STOPPING] == []
        assert state["deleting"] == []
        assert state["checks"] == []
        assert state["full"] is False

        run1.refresh_from_db()
        run2.refresh_from_db()
        run3.refresh_from_db()
        assert run1.status == V1Statuses.SCHEDULED
        assert run2.status == V1Statuses.SCHEDULED
        assert run3.status == V1Statuses.SCHEDULED
        run1.status = V1Statuses.QUEUED
        run1.save()
        run2.status = V1Statuses.QUEUED
        run2.save()

        run3.status = V1Statuses.STOPPING
        run3.save()
        run4.status = V1Statuses.STOPPING
        run4.save()
        with patch("haupt.common.workers.send") as workers_send:
            state = get_agent_state()
        assert workers_send.call_count == 0

        assert set(state[V1Statuses.QUEUED]) == {
            (
                get_run_instance("default", project.name, run1.uuid.hex),
                run1.runtime,
                run1.name,
                run1.content,
                None,
            ),
            (
                get_run_instance("default", project.name, run2.uuid.hex),
                run2.runtime,
                run2.name,
                run2.content,
                None,
            ),
        }
        assert set(state[V1Statuses.STOPPING]) == {
            (
                get_run_instance("default", project.name, run3.uuid.hex),
                run3.runtime,
                None,
            ),
            (
                get_run_instance("default", project.name, run4.uuid.hex),
                run4.runtime,
                None,
            ),
        }
        assert state["deleting"] == []
        assert state["checks"] == []
        assert state["full"] is False
        run1.refresh_from_db()
        run2.refresh_from_db()
        assert run1.status == V1Statuses.SCHEDULED
        assert run2.status == V1Statuses.SCHEDULED

        run1.status = V1Statuses.STOPPING
        run1.save()
        run2.status = V1Statuses.STOPPING
        run2.save()
        with patch("haupt.common.workers.send") as workers_send:
            state = get_agent_state()
        assert workers_send.call_count == 0

        assert state[V1Statuses.QUEUED] == []
        assert set(state[V1Statuses.STOPPING]) == {
            (
                get_run_instance("default", project.name, run1.uuid.hex),
                run1.runtime,
                None,
            ),
            (
                get_run_instance("default", project.name, run2.uuid.hex),
                run2.runtime,
                None,
            ),
            (
                get_run_instance("default", project.name, run3.uuid.hex),
                run3.runtime,
                None,
            ),
            (
                get_run_instance("default", project.name, run4.uuid.hex),
                run4.runtime,
                None,
            ),
        }
        assert state["deleting"] == []
        assert state["checks"] == []
        assert state["full"] is False

        # Trigger checks
        checked_at = now() - datetime.timedelta(hours=3)
        run1.checked_at = checked_at
        run1.status = V1Statuses.RUNNING
        run1.save()
        run2.checked_at = checked_at
        run2.status = V1Statuses.COMPILED
        run2.save()

        with patch("haupt.common.workers.send") as workers_send:
            state = get_agent_state()
        assert workers_send.call_count == 0
        assert state[V1Statuses.QUEUED] == []
        assert set(state[V1Statuses.STOPPING]) == {
            (
                get_run_instance("default", project.name, run3.uuid.hex),
                run3.runtime,
                None,
            ),
            (
                get_run_instance("default", project.name, run4.uuid.hex),
                run4.runtime,
                None,
            ),
        }
        assert state["deleting"] == []
        assert state["checks"] == [
            (
                get_run_instance("default", project.name, run1.uuid.hex),
                run1.runtime,
                None,
            ),
        ]
        run1.refresh_from_db()
        run2.refresh_from_db()
        assert run1.checked_at > checked_at
        assert run2.checked_at == checked_at

        # Deleting
        run5 = RunFactory(
            project=project,
            kind=V1RunKind.SERVICE,
        )
        run5.managed_by = ManagedBy.AGENT
        run6 = RunFactory(
            project=project,
            kind=V1RunKind.JOB,
        )
        run6.managed_by = ManagedBy.AGENT
        # Patch all runs to be managed
        Run.all.update(managed_by=ManagedBy.AGENT)

        run1.live_state = LiveState.DELETION_PROGRESSING
        run1.status = V1Statuses.RUNNING
        run1.save()
        run2.live_state = LiveState.DELETION_PROGRESSING
        run2.status = V1Statuses.COMPILED
        run2.save()

        run5.live_state = LiveState.DELETION_PROGRESSING
        run5.status = V1Statuses.STOPPED
        run5.save()
        run6.live_state = LiveState.DELETION_PROGRESSING
        run6.status = V1Statuses.FAILED
        run6.save()

        with patch("haupt.common.workers.send") as workers_send:
            state = get_agent_state()
        assert workers_send.call_count == 0
        assert state[V1Statuses.QUEUED] == []
        assert set(state[V1Statuses.STOPPING]) == {
            (
                get_run_instance("default", project.name, run3.uuid.hex),
                run3.runtime,
                None,
            ),
            (
                get_run_instance("default", project.name, run4.uuid.hex),
                run4.runtime,
                None,
            ),
        }
        assert set(state["deleting"]) == {
            (
                get_run_instance("default", "agent", "agent"),
                V1RunKind.JOB,
                "cleaner",
                _operations.get_batch_cleaner_operation(
                    environment=V1Environment(),
                    connection=agent_config.artifacts_store,
                    paths=[run5.uuid.hex, run6.uuid.hex],
                ).to_json(include_version=True),
                None,
            ),
            (
                get_run_instance("default", project.name, run1.uuid.hex),
                run1.runtime,
                run1.name,
                None,
                None,
            ),
            (
                get_run_instance("default", project.name, run2.uuid.hex),
                run2.runtime,
                run2.name,
                None,
                None,
            ),
        }
        assert state["checks"] == []
        assert state["full"] is False

    def test_get_annotated_controllers(self):
        project = ProjectFactory()
        pipeline1 = RunFactory(
            project=project,
            kind=V1RunKind.DAG,
        )
        pipeline1.managed_by = ManagedBy.AGENT
        pipeline1.pending = None
        pipeline2 = RunFactory(
            project=project,
            kind=V1RunKind.MATRIX,
            meta_info={"concurrency": 19},
        )
        pipeline2.managed_by = ManagedBy.AGENT
        pipeline2.pending = None
        pipeline3 = RunFactory(
            project=project,
            kind=V1RunKind.DAG,
            meta_info={"concurrency": 2},
        )
        pipeline3.managed_by = ManagedBy.AGENT
        pipeline3.pending = None
        run1 = RunFactory(
            project=project,
            kind=V1RunKind.JOB,
            pipeline=pipeline1,
            controller=pipeline1,
        )
        run1.managed_by = ManagedBy.AGENT
        run2 = RunFactory(
            project=project,
            kind=V1RunKind.JOB,
            pipeline=pipeline1,
            controller=pipeline1,
        )
        run2.managed_by = ManagedBy.AGENT
        run3 = RunFactory(
            project=project,
            kind=V1RunKind.TUNER,
            pipeline=pipeline2,
            controller=pipeline2,
        )
        run3.managed_by = ManagedBy.AGENT
        run4 = RunFactory(
            project=project,
            kind=V1RunKind.SERVICE,
            pipeline=pipeline2,
            controller=pipeline2,
        )
        run4.managed_by = ManagedBy.AGENT
        run5 = RunFactory(
            project=project,
            kind=V1RunKind.SERVICE,
            pipeline=pipeline3,
            controller=pipeline3,
        )
        run5.managed_by = ManagedBy.AGENT
        # Patch all runs to be managed
        Run.all.update(managed_by=ManagedBy.AGENT)

        # No queue with queued runs
        queues = get_annotated_controllers()
        assert list(queues) == []

        # Queue runs
        run1.status = V1Statuses.COMPILED
        run1.save()
        run2.status = V1Statuses.COMPILED
        run2.save()
        run5.status = V1Statuses.COMPILED
        run5.save()

        # Controllers not running
        queues = get_annotated_controllers()
        assert list(queues) == []

        pipeline1.status = V1Statuses.RUNNING
        pipeline1.save()
        pipeline2.status = V1Statuses.RUNNING
        pipeline2.save()
        pipeline3.status = V1Statuses.RUNNING
        pipeline3.save()

        # But no runs on k8s
        queues = get_annotated_controllers()
        assert list(queues) == [
            (pipeline1.id, None, 0),
            (pipeline3.id, 2, 0),
        ]

        # Queue more runs
        run3.status = V1Statuses.COMPILED
        run3.save()
        run4.status = V1Statuses.COMPILED
        run4.save()

        # But no runs on k8s
        queues = get_annotated_controllers()
        assert list(queues) == [
            (pipeline1.id, None, 0),
            (pipeline2.id, 19, 0),
            (pipeline3.id, 2, 0),
        ]

        # Runs on k8s
        run1.status = V1Statuses.RUNNING
        run1.save()
        # Queue are consumed
        queues = get_annotated_controllers()
        assert list(queues) == [
            (pipeline1.id, None, 1),
            (pipeline2.id, 19, 0),
            (pipeline3.id, 2, 0),
        ]

        run2.status = V1Statuses.WARNING
        run2.save()
        run5.status = V1Statuses.STARTING
        run5.save()
        # Queue are consumed
        queues = get_annotated_controllers()
        assert list(queues) == [
            (pipeline2.id, 19, 0),
        ]

    def test_get_annotated_pipelines(self):
        project = ProjectFactory()

        controller = RunFactory(project=project, kind=V1RunKind.DAG)

        pipeline1 = RunFactory(
            project=project,
            kind=V1RunKind.DAG,
            controller=controller,
            pipeline=controller,
        )
        pipeline1.managed_by = ManagedBy.AGENT
        pipeline1.pending = None
        pipeline2 = RunFactory(
            project=project,
            kind=V1RunKind.MATRIX,
            controller=controller,
            pipeline=controller,
            meta_info={"concurrency": 19},
        )
        pipeline2.managed_by = ManagedBy.AGENT
        pipeline2.pending = None
        pipeline3 = RunFactory(
            project=project,
            kind=V1RunKind.DAG,
            controller=controller,
            pipeline=controller,
            meta_info={"concurrency": 2},
        )
        pipeline3.managed_by = ManagedBy.AGENT
        pipeline3.pending = None

        run1 = RunFactory(
            project=project,
            kind=V1RunKind.JOB,
            pipeline=pipeline1,
            controller=pipeline1,
        )
        run1.managed_by = ManagedBy.AGENT
        run2 = RunFactory(
            project=project,
            kind=V1RunKind.JOB,
            pipeline=pipeline1,
            controller=pipeline1,
        )
        run2.managed_by = ManagedBy.AGENT
        run3 = RunFactory(
            project=project,
            kind=V1RunKind.TUNER,
            pipeline=pipeline2,
            controller=pipeline2,
        )
        run3.managed_by = ManagedBy.AGENT
        run4 = RunFactory(
            project=project,
            kind=V1RunKind.SERVICE,
            pipeline=pipeline2,
            controller=pipeline2,
        )
        run4.managed_by = ManagedBy.AGENT
        run5 = RunFactory(
            project=project,
            kind=V1RunKind.SERVICE,
            pipeline=pipeline3,
            controller=pipeline3,
        )
        run5.managed_by = ManagedBy.AGENT
        # Patch all runs to be managed
        Run.all.update(managed_by=ManagedBy.AGENT)

        # No queue with queued runs
        queues = get_annotated_pipelines(controller.id)
        assert list(queues) == []

        # Queue runs
        run1.status = V1Statuses.COMPILED
        run1.save()
        run2.status = V1Statuses.COMPILED
        run2.save()
        run5.status = V1Statuses.COMPILED
        run5.save()

        # Pipelines are not running
        queues = get_annotated_pipelines(controller.id)
        assert list(queues) == []

        pipeline1.status = V1Statuses.RUNNING
        pipeline1.save()
        pipeline2.status = V1Statuses.RUNNING
        pipeline2.save()
        pipeline3.status = V1Statuses.RUNNING
        pipeline3.save()

        # But no runs on k8s
        queues = get_annotated_pipelines(controller.id)
        assert list(queues) == [
            (pipeline1.id, None, 0),
            (pipeline3.id, 2, 0),
        ]

        # Queue more runs
        run3.status = V1Statuses.COMPILED
        run3.save()
        run4.status = V1Statuses.COMPILED
        run4.save()

        # But no runs on k8s
        queues = get_annotated_pipelines(controller.id)
        assert list(queues) == [
            (pipeline1.id, None, 0),
            (pipeline2.id, 19, 0),
            (pipeline3.id, 2, 0),
        ]

        # Runs on k8s
        run1.status = V1Statuses.RUNNING
        run1.save()
        # Queue are consumed
        queues = get_annotated_pipelines(controller.id)
        assert list(queues) == [
            (pipeline1.id, None, 1),
            (pipeline2.id, 19, 0),
            (pipeline3.id, 2, 0),
        ]

        run2.status = V1Statuses.WARNING
        run2.save()
        run5.status = V1Statuses.STARTING
        run5.save()
        # Queue are consumed
        queues = get_annotated_pipelines(controller.id)
        assert list(queues) == [
            (pipeline2.id, 19, 0),
        ]

    def test_get_runs_by_controller(self):
        project = ProjectFactory()
        controller = RunFactory(project=project, kind=V1RunKind.DAG)
        # Patch all runs to be managed
        Run.all.update(managed_by=ManagedBy.AGENT)

        assert get_runs_by_controller(controller.id, None, 0, None) == []
        assert list(get_runs_by_controller(controller.id, 10, 0, None)) == []

        run1 = RunFactory(
            project=project,
            kind=V1RunKind.JOB,
            controller=controller,
            pipeline=controller,
        )
        run1.managed_by = ManagedBy.AGENT
        # Patch all runs to be managed
        Run.all.update(managed_by=ManagedBy.AGENT)
        assert get_runs_by_controller(controller.id, None, 0, None) == []
        assert list(get_runs_by_controller(controller.id, 10, 0, None)) == []

        run1.status = V1Statuses.COMPILED
        run1.save()
        assert get_runs_by_controller(controller.id, None, 0, None) == []
        assert list(get_runs_by_controller(controller.id, 10, 0, None)) == [run1]

    def test_get_runs_by_pipeline(self):
        project = ProjectFactory()
        controller = RunFactory(project=project, kind=V1RunKind.DAG)
        pipeline1 = RunFactory(
            project=project,
            kind=V1RunKind.DAG,
            controller=controller,
            pipeline=controller,
        )
        pipeline2 = RunFactory(
            project=project,
            kind=V1RunKind.MATRIX,
            controller=controller,
            pipeline=controller,
            meta_info={"concurrency": 19},
        )
        pipeline3 = RunFactory(
            project=project,
            kind=V1RunKind.DAG,
            controller=controller,
            pipeline=controller,
            meta_info={"concurrency": 2},
        )
        # Patch all runs to be managed
        Run.all.update(managed_by=ManagedBy.AGENT)

        assert get_runs_by_pipeline(controller.id, pipeline1.id, None, 0, None) == []
        assert (
            list(get_runs_by_pipeline(controller.id, pipeline1.id, 10, 0, None)) == []
        )

        assert get_runs_by_pipeline(controller.id, pipeline2.id, None, 0, None) == []
        assert (
            list(get_runs_by_pipeline(controller.id, pipeline2.id, 10, 0, None)) == []
        )

        assert get_runs_by_pipeline(controller.id, pipeline3.id, None, 0, None) == []
        assert (
            list(get_runs_by_pipeline(controller.id, pipeline3.id, 10, 0, None)) == []
        )

        run1 = RunFactory(
            project=project,
            kind=V1RunKind.JOB,
            pipeline=pipeline1,
            controller=controller,
        )
        run1.managed_by = ManagedBy.AGENT
        run2 = RunFactory(
            project=project,
            kind=V1RunKind.JOB,
            pipeline=pipeline1,
            controller=controller,
        )
        run2.managed_by = ManagedBy.AGENT
        run3 = RunFactory(
            project=project,
            kind=V1RunKind.TUNER,
            pipeline=pipeline2,
            controller=controller,
        )
        run3.managed_by = ManagedBy.AGENT
        run4 = RunFactory(
            project=project,
            kind=V1RunKind.SERVICE,
            pipeline=pipeline2,
            controller=controller,
        )
        run4.managed_by = ManagedBy.AGENT
        run5 = RunFactory(
            project=project,
            kind=V1RunKind.SERVICE,
            pipeline=pipeline3,
            controller=controller,
        )
        run5.managed_by = ManagedBy.AGENT
        # Patch all runs to be managed
        Run.all.update(managed_by=ManagedBy.AGENT)

        assert get_runs_by_pipeline(controller.id, pipeline1.id, None, 0, None) == []
        assert (
            list(get_runs_by_pipeline(controller.id, pipeline1.id, 10, 0, None)) == []
        )

        assert get_runs_by_pipeline(controller.id, pipeline2.id, None, 0, None) == []
        assert (
            list(get_runs_by_pipeline(controller.id, pipeline2.id, 10, 0, None)) == []
        )

        assert get_runs_by_pipeline(controller.id, pipeline3.id, None, 0, None) == []
        assert (
            list(get_runs_by_pipeline(controller.id, pipeline3.id, 10, 0, None)) == []
        )

        run1.status = V1Statuses.COMPILED
        run1.save()
        run2.status = V1Statuses.COMPILED
        run2.save()
        run3.status = V1Statuses.COMPILED
        run3.save()
        run4.status = V1Statuses.COMPILED
        run4.save()
        run5.status = V1Statuses.COMPILED
        run5.save()

        assert get_runs_by_pipeline(controller.id, pipeline1.id, None, 0, None) == []
        assert set(
            [
                i.id
                for i in get_runs_by_pipeline(controller.id, pipeline1.id, 10, 0, None)
            ]
        ) == {run1.id, run2.id}

        assert get_runs_by_pipeline(controller.id, pipeline2.id, None, 0, None) == []
        assert set(
            [
                i.id
                for i in get_runs_by_pipeline(controller.id, pipeline2.id, 10, 0, None)
            ]
        ) == {run3.id, run4.id}

        assert get_runs_by_pipeline(controller.id, pipeline3.id, None, 0, None) == []
        assert set(
            [
                i.id
                for i in get_runs_by_pipeline(controller.id, pipeline3.id, 10, 0, None)
            ]
        ) == {run5.id}
