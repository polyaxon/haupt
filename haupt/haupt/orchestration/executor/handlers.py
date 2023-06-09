from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.common import conf
from haupt.common.options.registry.core import SCHEDULER_ENABLED
from haupt.db.defs import Models
from haupt.db.managers.cache import get_cache_clones
from haupt.db.managers.live_state import delete_in_progress_run
from haupt.db.managers.statuses import bulk_new_run_status
from haupt.orchestration.scheduler.manager import RunsManager
from polyaxon.constants.metadata import META_HAS_DOWNSTREAM_EVENTS_TRIGGER
from polyaxon.lifecycle import LifeCycle, ManagedBy, V1StatusCondition, V1Statuses
from polyaxon.polyflow import V1RunEdgeKind, V1RunKind


class APIHandler:
    MANAGER = RunsManager

    @classmethod
    def handle_run_created(cls, workers_backend, event: "Event") -> None:  # noqa: F821
        """Handles creation, resume, and restart"""
        # Run is not managed by Polyaxon
        if (
            event.instance and event.instance.managed_by == ManagedBy.USER
        ) or event.data["managed_by"] == ManagedBy.USER:
            return
        eager = False
        if event.instance and (
            event.instance.managed_by == ManagedBy.CLI
            or event.data["managed_by"] == ManagedBy.CLI
        ):
            eager = True
        # Run is managed by a pipeline
        if (
            event.data.get("pipeline_id") is not None
            and event.instance.status != V1Statuses.RESUMING
        ):
            return
        # Run is pending
        if event.instance.pending is not None:
            return

        workers_backend.send(
            SchedulerCeleryTasks.RUNS_PREPARE,
            delay=conf.get(SCHEDULER_ENABLED) and not eager,
            kwargs={"run_id": event.instance_id},
            eager_kwargs={"run": event.instance},
        )

    @classmethod
    def handle_run_approved_triggered(
        cls, workers_backend, event: "Event"
    ) -> None:  # noqa: F821
        run = cls.MANAGER.get_run(run_id=event.instance_id, run=event.instance)
        if not run:
            return

        task = (
            SchedulerCeleryTasks.RUNS_PREPARE
            if run.status == V1Statuses.CREATED
            else SchedulerCeleryTasks.RUNS_START
        )

        workers_backend.send(
            task,
            kwargs={"run_id": event.instance_id},
            eager_kwargs={"run": event.instance},
        )

    @classmethod
    def handle_run_stopped_triggered(
        cls, workers_backend, event: "Event"
    ) -> None:  # noqa: F821
        cls.MANAGER.runs_stop(run_id=event.instance_id, run=event.instance)

    @classmethod
    def handle_run_done(
        cls, workers_backend, event: "Event" = None
    ) -> None:  # noqa: F821
        """Handles all run done statuses"""
        workers_backend.send(
            SchedulerCeleryTasks.RUNS_NOTIFY_DONE,
            kwargs={"run_id": event.instance_id},
            eager_kwargs={"run": event.instance},
            countdown=2,
        )

    @classmethod
    def handle_run_new_status(
        cls, workers_backend, event: "Event"
    ) -> None:  # noqa: F821
        run = cls.MANAGER.get_run(run_id=event.instance_id, run=event.instance)
        if not run:
            return

        if LifeCycle.is_done(run.status):  # Managed by notify done
            return

        if run.meta_info.get(META_HAS_DOWNSTREAM_EVENTS_TRIGGER):
            workers_backend.send(
                SchedulerCeleryTasks.RUNS_NOTIFY_STATUS,
                kwargs={"run_id": event.instance_id},
                eager_kwargs={"run": event.instance},
            )

    @classmethod
    def handle_new_artifacts(
        cls, workers_backend, event: "Event"
    ) -> None:  # noqa: F821
        artifacts = event.data.get("artifacts")
        if not artifacts:
            return

        workers_backend.send(
            SchedulerCeleryTasks.RUNS_SET_ARTIFACTS,
            kwargs={"run_id": event.instance_id, "artifacts": artifacts},
            eager_kwargs={"run": event.instance},
        )

    @classmethod
    def handle_run_deleted(cls, workers_backend, event: "Event") -> None:  # noqa: F821
        run = cls.MANAGER.get_run(run_id=event.instance_id, run=event.instance)
        if not run:
            return

        cache_clones = [i for i in get_cache_clones(run.id)]
        if cache_clones:
            Models.Run.all.filter(id__in=cache_clones).update(
                original=None, cloning_kind=None, pending=None
            )
            for cache_clone_id in cache_clones:
                workers_backend.send(
                    SchedulerCeleryTasks.RUNS_PREPARE,
                    kwargs={"run_id": cache_clone_id},
                )

        if run.runtime == V1RunKind.BUILDER:
            awaiting_build = run.downstream_runs.filter(
                upstream_edges__kind=V1RunEdgeKind.BUILD
            )
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.UPSTREAM_FAILED,
                status="True",
                reason="BuildProcessDeleted",
                message=f"Build process {run.uuid.hex} was deleted, "
                f"last build status: {run.status}.",
            )
            bulk_new_run_status(awaiting_build, condition)
        if not run.has_pipeline:
            return

        delete_in_progress_run(run=run)
