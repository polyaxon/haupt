from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from django.conf import settings as dj_settings
from django.db.models import Count, Q
from django.utils.timezone import now

from haupt.background.celeryp.tasks import CronsCeleryTasks, SchedulerCeleryTasks
from haupt.common import workers
from haupt.db.defs import Models
from haupt.db.managers.live_state import confirm_delete_runs
from haupt.db.managers.queues import get_num_to_start
from haupt.db.managers.statuses import bulk_new_run_status
from haupt.db.queries.runs import STATUS_UPDATE_COLUMNS_ONLY
from polyaxon import _operations, settings
from polyaxon._auxiliaries import V1DefaultScheduling
from polyaxon._schemas.agent import AgentConfig
from polyaxon._utils.fqn_utils import get_run_instance
from polyaxon.schemas import (
    LifeCycle,
    LiveState,
    ManagedBy,
    V1RunKind,
    V1StatusCondition,
    V1Statuses,
)

MAX_DELETE_ITEMS = 200


def check_schedules(
    managed_by: Optional[ManagedBy] = ManagedBy.AGENT,
    agent_filters: Optional[Dict] = None,
) -> bool:
    agent_filters = agent_filters or {}
    end = now() + timedelta(seconds=3)
    schedule_runs = (
        Models.Run.objects.filter(
            **agent_filters,
            status=V1Statuses.CREATED,
            schedule_at__lte=end,
            pending__isnull=True,
            managed_by=managed_by,
        )
        .order_by("schedule_at")
        .only(*STATUS_UPDATE_COLUMNS_ONLY)
    )
    if schedule_runs:
        condition = V1StatusCondition.get_condition(
            type=V1Statuses.ON_SCHEDULE,
            status="True",
            reason="AgentSchedules",
            message="Run is on schedule",
        )
        bulk_new_run_status(runs=schedule_runs, condition=condition)
        schedule_run_ids = [s.id for s in schedule_runs]
        for run_id in schedule_run_ids:
            workers.send(
                SchedulerCeleryTasks.RUNS_PREPARE,
                kwargs={"run_id": run_id},
            )
    return Models.Run.objects.filter(
        **agent_filters,
        status=V1Statuses.CREATED,
        schedule_at__range=(end, end + timedelta(seconds=8)),
        pending__isnull=True,
        managed_by=managed_by,
    ).exists()


def get_stopping_runs(
    owner_name: str,
    max_budget: int,
    managed_by: Optional[ManagedBy] = ManagedBy.AGENT,
    agent_filters: Optional[Dict] = None,
    is_new_agent: Optional[bool] = False,
) -> Tuple[List[Tuple[str, str, str]], bool]:
    agent_filters = agent_filters or {}
    filters = Q(status=V1Statuses.STOPPING)
    if dj_settings.HAS_ORG_MANAGEMENT:
        values_list = ["project__name", "uuid", "kind", "namespace"]
    else:
        values_list = ["project__name", "uuid", "kind"]
    stopping_runs = (
        Models.Run.restorable.filter(
            **agent_filters,
            kind__in=[
                V1RunKind.JOB,
                V1RunKind.SERVICE,
                V1RunKind.TUNER,
                V1RunKind.NOTIFIER,
            ],
            pending__isnull=True,
            managed_by=managed_by,
        )
        .filter(filters)
        .prefetch_related("project")
        .values_list(*values_list)[:max_budget]
    )
    full = len(stopping_runs) >= max_budget
    if is_new_agent:
        data = [
            (
                get_run_instance(owner_name, run[0], run[1].hex),
                run[2],
                run[3] if dj_settings.HAS_ORG_MANAGEMENT else None,
            )
            for run in stopping_runs
        ]
    else:
        data = [
            (get_run_instance(owner_name, run[0], run[1].hex), run[2])
            for run in stopping_runs
        ]
    return data, full


def get_deleting_runs(
    owner_name: str,
    agent_id: str,
    agent_config: AgentConfig,
    max_budget: int,
    managed_by: Optional[ManagedBy] = ManagedBy.AGENT,
    agent_filters: Optional[Dict] = None,
    is_new_agent: Optional[bool] = None,
) -> Tuple[List[str], List[Tuple[str, str, str, str, str]], bool]:
    agent_filters = agent_filters or {}
    values = []

    # Clean and delete
    deleting_runs = (
        Models.Run.all.filter(
            **agent_filters,
            kind__in=[
                V1RunKind.JOB,
                V1RunKind.SERVICE,
                V1RunKind.TUNER,
                V1RunKind.NOTIFIER,
            ],
            live_state=LiveState.DELETION_PROGRESSING,
            status__in=LifeCycle.DONE_VALUES,
            pending__isnull=True,
            deleted_at__isnull=True,
            updated_at__lte=now().replace(second=0, microsecond=0)
            - timedelta(seconds=dj_settings.MIN_ARTIFACTS_DELETION_TIMEDELTA),
        )
        .prefetch_related("project")
        .values_list("uuid", "id", "pipeline_id")[:MAX_DELETE_ITEMS]
    )
    if deleting_runs:
        run_ids = [v[1] for v in deleting_runs]
        confirm_delete_runs(
            runs=Models.Run.all.filter(id__in=run_ids),
            run_ids=run_ids,
        )
        pipeline_ids = {v[2] for v in deleting_runs if v[2]}
        for pipeline_id in pipeline_ids:
            workers.send(
                SchedulerCeleryTasks.RUNS_CHECK_ORPHAN_PIPELINE,
                kwargs={"run_id": pipeline_id},
            )
    paths = [run[0].hex for run in deleting_runs]
    if paths:
        op = _operations.get_batch_cleaner_operation(
            connection=agent_config.artifacts_store,
            paths=paths,
            environment=V1DefaultScheduling.get_service_environment(
                agent_config.cleaner, agent_config.default_scheduling
            ),
            cleaner=agent_config.cleaner,
        )
        if is_new_agent:
            values.append(
                (
                    get_run_instance(owner_name, "agent", agent_id),
                    V1RunKind.JOB,
                    "cleaner",
                    op.to_json(include_version=True),
                    None,
                )
            )
        else:
            values.append(
                (
                    get_run_instance(owner_name, "agent", agent_id),
                    V1RunKind.JOB,
                    "cleaner",
                    op.to_json(include_version=True),
                )
            )

    # Clean and stop
    if dj_settings.HAS_ORG_MANAGEMENT:
        values_list = ["project__name", "uuid", "kind", "name", "id", "namespace"]
    else:
        values_list = ["project__name", "uuid", "kind", "name", "id"]
    deleting_runs = (
        Models.Run.all.filter(
            **agent_filters,
            kind__in={
                V1RunKind.JOB,
                V1RunKind.SERVICE,
                V1RunKind.TUNER,
                V1RunKind.NOTIFIER,
            },
            live_state=LiveState.DELETION_PROGRESSING,
        )
        .exclude(status__in=LifeCycle.DONE_VALUES)
        .prefetch_related("project")
        .values_list(*values_list)[:max_budget]
    )
    if deleting_runs:
        Models.Run.all.filter(id__in=[v[4] for v in deleting_runs]).update(
            status=V1Statuses.STOPPED
        )
    for run in deleting_runs:
        run_uuid = run[1].hex
        if is_new_agent:
            values.append(
                (
                    get_run_instance(owner_name, run[0], run_uuid),
                    run[2],
                    run[3],
                    None,
                    run[5] if dj_settings.HAS_ORG_MANAGEMENT else None,
                )
            )
        else:
            values.append(
                (
                    get_run_instance(owner_name, run[0], run_uuid),
                    run[2],
                    run[3],
                    None,
                )
            )

    return paths, values, len(values) >= max_budget


def get_checks_runs(
    owner_name: str,
    managed_by: Optional[ManagedBy] = ManagedBy.AGENT,
    agent_filters: Optional[Dict] = None,
    is_new_agent: Optional[bool] = None,
) -> List[Tuple[str, str, str]]:
    agent_filters = agent_filters or {}
    start = now()
    end = start - timedelta(hours=1)
    if dj_settings.HAS_ORG_MANAGEMENT:
        values_list = ["project__name", "uuid", "kind", "id", "namespace"]
    else:
        values_list = ["project__name", "uuid", "kind", "id"]
    checks_runs = (
        Models.Run.objects.filter(
            **agent_filters,
            kind__in=[
                V1RunKind.JOB,
                V1RunKind.SERVICE,
                V1RunKind.TUNER,
                V1RunKind.NOTIFIER,
            ],
            checked_at__lte=end,
            managed_by=managed_by,
            status__in=LifeCycle.ON_K8S_VALUES,
        )
        .prefetch_related("project")
        .values_list(*values_list)
    )
    if is_new_agent:
        values = [
            (
                get_run_instance(owner_name, run[0], run[1].hex),
                run[2],
                run[4] if dj_settings.HAS_ORG_MANAGEMENT else None,
            )
            for run in checks_runs
        ]
    else:
        values = [
            (get_run_instance(owner_name, run[0], run[1].hex), run[2])
            for run in checks_runs
        ]
    if checks_runs:
        Models.Run.objects.filter(id__in=[r[3] for r in checks_runs]).update(
            checked_at=start
        )
    return values


def get_runs_by_pipeline(
    controller_id: int,
    pipeline_id: int,
    concurrency: int,
    consumed: int,
    max_budget: Optional[int],
    managed_by: Optional[ManagedBy] = ManagedBy.AGENT,
) -> List[Models.Run]:
    num_to_run = get_num_to_start(
        concurrency=concurrency, consumed=consumed, max_budget=max_budget
    )
    if num_to_run < 1:
        return []

    return Models.Run.objects.filter(
        controller_id=controller_id,
        pipeline_id=pipeline_id,
        status=V1Statuses.COMPILED,
        pending__isnull=True,
        managed_by=managed_by,
    )[:num_to_run]


def check_pipelines(
    controller_id: int, max_budget: int
) -> Tuple[List[Models.Run], bool]:
    # TODO: TESTS
    # We queue runs managed by children pipelines
    to_update = []
    for pipeline in get_annotated_pipelines(controller_id=controller_id):
        runs = get_runs_by_pipeline(
            controller_id=controller_id,
            pipeline_id=pipeline[0],
            concurrency=pipeline[1],
            consumed=pipeline[2],
            max_budget=max_budget,
        )
        to_update += runs
        if max_budget:
            max_budget -= len(runs)
        if max_budget < 1:
            return to_update, True

    return to_update, False


def get_runs_by_controller(
    controller_id: int,
    concurrency: int,
    consumed: int,
    max_budget: Optional[int],
    managed_by: Optional[ManagedBy] = ManagedBy.AGENT,
) -> List[Models.Run]:
    num_to_run = get_num_to_start(
        concurrency=concurrency, consumed=consumed, max_budget=max_budget
    )
    if num_to_run < 1:
        return []

    return Models.Run.objects.filter(
        controller_id=controller_id,
        pipeline_id=controller_id,
        status=V1Statuses.COMPILED,
        pending__isnull=True,
        managed_by=managed_by,
    )[:num_to_run]


def get_annotated_pipelines(
    controller_id: int, managed_by: Optional[ManagedBy] = ManagedBy.AGENT
) -> List[Tuple[int, int, int]]:
    pipelines = (
        Models.Run.objects.filter(
            kind__in=[V1RunKind.DAG, V1RunKind.MATRIX],
            status=V1Statuses.RUNNING,
            controller_id=controller_id,
            pipeline_runs__status=V1Statuses.COMPILED,
            pending__isnull=True,
            managed_by=managed_by,
        )
        .distinct()
        .values_list("id", flat=True)
    )
    pipelines = Models.Run.objects.filter(id__in=pipelines)
    pipelines = pipelines.annotate(
        consumed=Count(
            "pipeline_runs",
            filter=Q(
                pipeline_runs__status__in=LifeCycle.ON_K8S_VALUES | {V1Statuses.QUEUED}
            ),
            distinct=True,
        ),
    )
    return pipelines.values_list("id", "meta_info__concurrency", "consumed")


def get_annotated_controllers(
    managed_by: Optional[ManagedBy] = ManagedBy.AGENT,
    agent_filters: Optional[Dict] = None,
) -> List[Tuple[int, int, int]]:
    agent_filters = agent_filters or {}
    controllers = (
        Models.Run.objects.filter(
            **agent_filters,
            kind__in=[V1RunKind.DAG, V1RunKind.MATRIX],
            status=V1Statuses.RUNNING,
            pending__isnull=True,
            managed_by=managed_by,
            controller_id__isnull=True,
            controller_runs__status=V1Statuses.COMPILED,
        )
        .distinct()
        .values_list("id", flat=True)
    )
    controllers = Models.Run.objects.filter(id__in=controllers)
    controllers = controllers.annotate(
        consumed=Count(
            "pipeline_runs",
            filter=Q(
                pipeline_runs__status__in=LifeCycle.ON_K8S_VALUES | {V1Statuses.QUEUED}
            ),
            distinct=True,
        ),
    )
    return controllers.values_list("id", "meta_info__concurrency", "consumed")


def check_controllers(max_budget: int, agent_filters: Optional[Dict] = None) -> bool:
    if max_budget <= 0:
        return True

    full = False
    # TODO: TESTS
    to_update = []
    for controller in get_annotated_controllers(agent_filters=agent_filters):
        # We start by queueing directly managed runs by controller
        controller_budget = (
            controller[1]
            if (controller[1] is not None and controller[1] > 0)
            else max_budget
        )
        runs = get_runs_by_controller(
            controller_id=controller[0],
            concurrency=controller_budget,
            consumed=controller[2],
            max_budget=max_budget,
        )
        if controller_budget:
            controller_budget -= len(runs)
        to_update += runs

        # Check if controller still can queue
        if controller_budget < 1:
            full = True
            continue

        pipeline_runs, pipeline_full = check_pipelines(
            controller_id=controller[0], max_budget=controller_budget
        )
        to_update += pipeline_runs
        if pipeline_full:
            full = True

    # Split runs to pipeline and operations
    pipelines_to_update = [i for i in to_update if i.has_pipeline]
    runs_to_update = [i for i in to_update if not i.has_pipeline]
    # Start nested pipelines
    for pipeline in pipelines_to_update:
        workers.send(
            SchedulerCeleryTasks.RUNS_START_IMMEDIATELY,
            kwargs={"run_id": pipeline.id},
        )
    # Set queue
    condition = V1StatusCondition.get_condition(
        type=V1Statuses.QUEUED,
        status="True",
        reason="AgentController",
        message="Run is queued",
    )
    bulk_new_run_status(runs_to_update, condition)
    return full


def get_queued_runs(
    managed_by: Optional[ManagedBy] = ManagedBy.AGENT,
    is_new_agent: Optional[bool] = None,
) -> Tuple[List[Tuple[str, str, str, str]], bool]:
    consumed = Models.Run.objects.filter(
        status__in=LifeCycle.ON_K8S_VALUES,
        pending__isnull=True,
        managed_by=managed_by,
    ).count()

    max_budget = dj_settings.MAX_CONCURRENCY - consumed

    if max_budget <= 0:
        return [], True

    num_to_run = get_num_to_start(
        concurrency=dj_settings.MAX_CONCURRENCY,
        consumed=consumed,
        max_budget=max_budget,
    )
    if num_to_run < 1:
        return [], True

    full = False
    if num_to_run > max_budget:
        full = True
        num_to_run = max_budget

    queryset = Models.Run.objects.filter(
        kind__in=[
            V1RunKind.JOB,
            V1RunKind.SERVICE,
            V1RunKind.TUNER,
            V1RunKind.NOTIFIER,
        ],
        status=V1Statuses.QUEUED,
        pending__isnull=True,
        managed_by=managed_by,
    ).prefetch_related("project")[:num_to_run]

    # Set scheduled
    condition = V1StatusCondition.get_condition(
        type=V1Statuses.SCHEDULED,
        status="True",
        reason="AgentController",
        message="Operation is scheduled",
    )
    bulk_new_run_status(runs=[i for i in queryset], condition=condition)

    if is_new_agent:
        data = [
            (
                get_run_instance("default", run.project.name, run.uuid.hex),
                run.kind,
                run.name,
                run.content,
                getattr(run, "namespace", None),
            )
            for run in queryset
        ]
    else:
        data = [
            (
                get_run_instance("default", run.project.name, run.uuid.hex),
                run.kind,
                run.name,
                run.content,
            )
            for run in queryset
        ]

    return data, full


def get_agent_state() -> Dict:
    agent_config = settings.AGENT_CONFIG

    full = False
    # We check the schedules
    if check_schedules():
        full = True

    # We collect all jobs/services to stop
    stopping_runs, stopping_full = get_stopping_runs(
        owner_name="default",
        max_budget=dj_settings.MAX_CONCURRENCY,
        is_new_agent=True,
    )
    if stopping_full:
        full = True
    # We collect all jobs/services to delete
    if agent_config:
        _, deleting_runs, deleting_full = get_deleting_runs(
            owner_name="default",
            agent_id="agent",
            agent_config=agent_config,
            max_budget=dj_settings.MAX_CONCURRENCY,
            is_new_agent=True,
        )
        if deleting_full:
            full = True
    else:
        deleting_runs = []

    checks_runs = get_checks_runs(owner_name="default", is_new_agent=True)
    # We check the pipelines/controllers
    if check_controllers(max_budget=dj_settings.MAX_CONCURRENCY):
        full = True
    # We collect all jobs/services to start
    queued_runs, queued_full = get_queued_runs(is_new_agent=True)
    if queued_full:
        full = True
    return {
        V1Statuses.STOPPING: stopping_runs,
        V1Statuses.QUEUED: queued_runs,
        "checks": checks_runs,
        "deleting": deleting_runs,
        "full": full,
    }


def trigger_cron(state: bool = False) -> Dict:
    workers.send(CronsCeleryTasks.HEARTBEAT_OUT_OF_SYNC_SCHEDULES)
    workers.send(CronsCeleryTasks.HEARTBEAT_STOPPING_RUNS)
    workers.send(CronsCeleryTasks.HEARTBEAT_PROJECT_LAST_UPDATED)
    workers.send(CronsCeleryTasks.STATS_CALCULATION_PROJECTS)
    workers.send(CronsCeleryTasks.DELETE_ARCHIVED_PROJECTS)
    workers.send(CronsCeleryTasks.DELETE_IN_PROGRESS_PROJECTS)
    workers.send(CronsCeleryTasks.DELETE_ARCHIVED_RUNS)
    workers.send(CronsCeleryTasks.DELETE_IN_PROGRESS_RUNS)
    if not state:
        return {}

    # Return paths to be deleted not ops since the sandbox can manage the artifacts store
    deleting_paths, _, _ = get_deleting_runs(
        owner_name="default",
        agent_id="agent",
        agent_config=settings.AGENT_CONFIG,
        max_budget=dj_settings.MAX_CONCURRENCY,
    )
    return {
        "deleting": deleting_paths,
    }
