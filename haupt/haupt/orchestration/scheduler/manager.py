import logging

from datetime import datetime
from functools import reduce
from operator import __or__ as OR
from typing import Dict, List, Optional

from clipped.compact.pydantic import ValidationError as PydanticValidationError
from clipped.utils.lists import to_list
from rest_framework.exceptions import ValidationError

from django.db.models import Q, QuerySet
from django.utils.timezone import now

from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.common import workers
from haupt.common.exceptions import AccessNotAuthorized, AccessNotFound
from haupt.db.defs import Models
from haupt.db.managers import flows
from haupt.db.managers.artifacts import atomic_set_artifacts
from haupt.db.managers.live_state import (
    delete_in_progress_project,
    delete_in_progress_run,
)
from haupt.db.managers.runs import (
    base_approve_run,
    get_failed_stopped_and_all_runs,
    get_stopping_pipelines_with_no_runs,
    is_pipeline_done,
)
from haupt.db.managers.stats import (
    collect_project_run_count_stats,
    collect_project_run_duration_stats,
    collect_project_run_status_stats,
    collect_project_unique_user_stats,
    collect_project_version_stats,
)
from haupt.db.managers.statuses import (
    bulk_new_run_status,
    new_run_skip_status,
    new_run_status,
    new_run_stop_status,
)
from haupt.db.queries.runs import (
    STATUS_UPDATE_COLUMNS_DEFER,
    STATUS_UPDATE_COLUMNS_ONLY,
)
from haupt.orchestration import operations
from haupt.orchestration.scheduler.resolver import SchedulingResolver
from polyaxon._compiler import resolver
from polyaxon._constants.metadata import (
    META_BRACKET_ITERATION,
    META_DESTINATION_IMAGE,
    META_HAS_EARLY_STOPPING,
    META_HAS_HOOKS,
    META_IS_HOOK,
    META_ITERATION,
)
from polyaxon._operations import get_bo_tuner, get_hyperband_tuner, get_hyperopt_tuner
from polyaxon.exceptions import (
    PolyaxonCompilerError,
    PolyaxonException,
    PolyaxonSchemaError,
)
from polyaxon.schemas import (
    LifeCycle,
    ManagedBy,
    V1CloningKind,
    V1CompiledOperation,
    V1FailureEarlyStopping,
    V1MatrixKind,
    V1MetricEarlyStopping,
    V1Operation,
    V1Optimization,
    V1RunEdgeKind,
    V1RunKind,
    V1RunPending,
    V1StatusCondition,
    V1Statuses,
    V1TriggerPolicy,
    dags,
)
from traceml.artifacts import V1ArtifactKind, V1RunArtifact

_logger = logging.getLogger("polyaxon.scheduler")


class SchedulingManager:
    DEFAULT_PREFETCH = ["project"]
    RESOLVER = SchedulingResolver

    @classmethod
    def _resolve(
        cls,
        run: Models.Run,
        compiled_at: Optional[datetime] = None,
    ):
        try:
            compiled_operation = V1CompiledOperation.read(
                run.content
            )  # TODO: Use construct
            project = run.project
            return resolver.resolve(
                run=run,
                compiled_operation=compiled_operation,
                owner_name=project.owner.name,
                project_name=project.name,
                project_uuid=project.uuid.hex,
                run_uuid=run.uuid.hex,
                run_name=run.name,
                run_path=run.subpath,
                resolver_cls=cls.RESOLVER,
                params=None,
                compiled_at=compiled_at,
                created_at=run.created_at,
                cloning_kind=run.cloning_kind,
                original_uuid=run.original.uuid.hex if run.original_id else None,
                is_independent=not bool(run.pipeline_id),
            )
        except (
            AccessNotAuthorized,
            AccessNotFound,
        ) as e:
            raise PolyaxonCompilerError("Access Error: %s" % e) from e
        except (
            AccessNotAuthorized,
            AccessNotFound,
            PydanticValidationError,
            PolyaxonSchemaError,
            ValidationError,
        ) as e:
            raise PolyaxonCompilerError("Compilation Error: %s" % e) from e

    @classmethod
    def _resolve_hooks(cls, run: Models.Run) -> List[V1Operation]:
        try:
            compiled_operation = V1CompiledOperation.read(
                run.content
            )  # TODO: Use construct
            project = run.project
            return resolver.resolve_hooks(
                run=run,
                compiled_operation=compiled_operation,
                owner_name=project.owner.name,
                project_name=project.name,
                project_uuid=project.uuid.hex,
                run_uuid=run.uuid.hex,
                run_name=run.name,
                run_path=run.subpath,
                resolver_cls=cls.RESOLVER,
                params=None,
                compiled_at=None,
                created_at=run.created_at,
                cloning_kind=run.cloning_kind,
                original_uuid=run.original.uuid.hex if run.original_id else None,
            )
        except (
            AccessNotAuthorized,
            AccessNotFound,
        ) as e:
            raise PolyaxonCompilerError("Access Error: %s" % e) from e
        except (
            AccessNotAuthorized,
            AccessNotFound,
            PydanticValidationError,
            PolyaxonSchemaError,
            ValidationError,
        ) as e:
            raise PolyaxonCompilerError("Compilation Error: %s" % e) from e

    @staticmethod
    def _capture_exception(e: Exception):
        _logger.exception(e)

    @staticmethod
    def _capture_message(message: str):
        return

    @staticmethod
    def _set_iteration_meta_info(
        run: Models.Run, suggestions: List[Dict], iteration: int, bracket_iteration: int
    ) -> V1CompiledOperation:
        compiled_operation = V1CompiledOperation.read(
            run.content
        )  # TODO: Use construct

        condition = not suggestions or iteration is None
        if condition or (
            compiled_operation.has_hyperband_matrix and bracket_iteration is None
        ):
            _logger.info(
                "Run `%s` cannot iterate and create matrix runs, received wrong iteration lineage",
                run.id,
            )
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.FAILED,
                status="True",
                reason="SchedulerIterateFailure",
                message="Run received wrong iteration lineage, "
                "an iteration number and a list of suggestions is required, "
                "received empty suggestions.",
            )
            new_run_status(run=run, condition=condition)
            return compiled_operation
        run.meta_info[META_ITERATION] = iteration
        if compiled_operation.has_hyperband_matrix:
            run.meta_info[META_BRACKET_ITERATION] = bracket_iteration
        run.save(update_fields=["meta_info"])
        return compiled_operation

    @classmethod
    def _execute_hooks(
        cls, run: Models.Run, hook_ops: List[V1Operation]
    ) -> List[Models.Run]:
        if not hook_ops:
            return []

        hub_refs_to_components = cls.RESOLVER._collect_hub_refs(
            ops=hook_ops, owner_name=run.project.owner.name
        )

        def get_edges():
            run_edges = []
            for hook_run in runs:
                run_edges.append(
                    Models.RunEdge(
                        upstream_id=run.id,
                        downstream_id=hook_run.id,
                        kind=V1RunEdgeKind.HOOK,
                    )
                )
            return run_edges

        runs = []
        for hook in hook_ops:
            component_state = None
            if (
                not hook.has_component_reference
                and hook.has_hub_reference
                and hook.hub_ref in hub_refs_to_components
            ):
                hook.set_definition(
                    hub_refs_to_components[hook.hub_ref]["component_content"]
                )
                component_state = hub_refs_to_components[hook.hub_ref][
                    "component_state"
                ]
            hook_run = operations.init_run(
                project_id=run.project_id,
                user_id=run.user_id,
                op_spec=hook,
                supported_owners={run.project.owner.name},
                component_state=component_state,
            ).instance
            hook_run.meta_info[META_IS_HOOK] = True
            runs.append(hook_run)

        # Create batch runs
        if runs:
            runs = Models.Run.objects.bulk_create(runs)

        # Create edges
        run_edges = get_edges()
        if run_edges:
            Models.RunEdge.objects.bulk_create(run_edges)

        return [run.id for run in runs]

    @staticmethod
    def _notify_build(run: Models.Run):
        if run.runtime != V1RunKind.BUILDER:
            return
        runs = run.downstream_runs.exclude(status__in=LifeCycle.DONE_VALUES).filter(
            pending=V1RunPending.BUILD,
        )
        if run.status != V1Statuses.SUCCEEDED:
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.UPSTREAM_FAILED,
                status="True",
                reason="SchedulerBuildNotify",
                message=f"Build process {run.uuid.hex} did not succeed, "
                f"last build status: {run.status}.",
            )
            bulk_new_run_status(runs, condition)
            return

        destination = (
            Models.ArtifactLineage.objects.filter(
                artifact__name="destination",
                artifact__kind=V1ArtifactKind.DOCKER_IMAGE,
                is_input=False,
                run_id=run.id,
            )
            .values_list("artifact__summary", flat=True)
            .last()
        )
        destination_image = None
        if destination:
            destination_image = destination.get("image")

        if not destination_image:
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.UPSTREAM_FAILED,
                status="True",
                reason="SchedulerBuildNotify",
                message=f"Build process {run.uuid.hex} succeed "
                f"but did not generate an image destination.",
            )
            bulk_new_run_status(runs, condition)
            return

        built_runs = []
        for built_run in runs:
            meta_info = built_run.meta_info or {}
            meta_info[META_DESTINATION_IMAGE] = destination_image
            built_run.meta_info = meta_info
            built_runs.append(built_run)
        Models.Run.objects.bulk_update(built_runs, ["meta_info"])
        for built_run in built_runs:
            workers.send(
                SchedulerCeleryTasks.RUNS_BUILT,
                kwargs={"run_id": built_run.id},
                eager_kwargs={"run": built_run},
            )

    @staticmethod
    def _notify_cache(run: Models.Run):
        condition = V1StatusCondition.get_condition(
            type=run.status,
            status="True",
            reason="SchedulerCacheNotify",
            message="Original run is done.",
        )
        for clone_run in Models.Run.objects.filter(
            original_id=run.id,
            cloning_kind=V1CloningKind.CACHE,
            pending=V1RunPending.CACHE,
        ).only("outputs", *STATUS_UPDATE_COLUMNS_ONLY):
            clone_run.outputs = run.outputs
            clone_run.pending = None
            new_run_status(
                run=clone_run,
                condition=condition,
                additional_fields=["outputs", "pending"],
            )

    @staticmethod
    def _notify_hooks(run: Models.Run):
        if run.meta_info.get(META_HAS_HOOKS):
            workers.send(
                SchedulerCeleryTasks.RUNS_HOOKS,
                kwargs={"run_id": run.id},
                eager_kwargs={"run": run},
            )

    @staticmethod
    def _check_failure_early_stopping(
        run: Models.Run, early_stopping: List[V1FailureEarlyStopping]
    ) -> bool:
        # We only need one with the lowest percent
        early_stopping = to_list(early_stopping, check_none=True)
        if not early_stopping:
            return False
        percent = min([es.percent for es in early_stopping if es.percent])
        failed_count = run.controller_runs.filter(
            status__in={V1Statuses.FAILED, V1Statuses.UPSTREAM_FAILED}
        ).count()
        if failed_count == 0:
            return False
        return failed_count / run.controller_runs.count() >= (percent / 100)

    @staticmethod
    def _check_absolute_metric_early_stopping(
        run: Models.Run, early_stopping: List[V1MetricEarlyStopping]
    ) -> bool:
        early_stopping = to_list(early_stopping, check_none=True)
        if not early_stopping:
            return False
        filters = []
        for early_stopping_metric in early_stopping:
            comparison = (
                "gte"
                if V1Optimization.maximize(early_stopping_metric.optimization)
                else "lte"
            )
            metric_filter = "outputs__{}__{}".format(
                early_stopping_metric.metric, comparison
            )
            filters.append({metric_filter: early_stopping_metric.value})
        if filters:
            return run.controller_runs.filter(
                reduce(OR, [Q(**f) for f in filters])
            ).exists()
        return False

    @staticmethod
    def _check_metric_early_stopping(
        run: Models.Run, early_stopping: List[V1MetricEarlyStopping]
    ) -> bool:
        early_stopping = to_list(early_stopping, check_none=True)
        if not early_stopping:
            return False
        return False

    @classmethod
    def _should_early_stop(cls, run: Models.Run) -> bool:
        if not run.meta_info.get(META_HAS_EARLY_STOPPING):
            return False

        if hasattr(run, "_compiled_operation"):
            compiled_operation = run._compiled_operation
        else:
            compiled_operation = V1CompiledOperation.read(
                run.content
            )  # TODO: Use construct
            # Cache the compiled_operation to avoid recalculation
            run._compiled_operation = compiled_operation

        if compiled_operation.matrix:
            early_stopping = compiled_operation.matrix.early_stopping
        elif compiled_operation.is_dag_run:
            early_stopping = compiled_operation.run.early_stopping

        early_stopping = to_list(early_stopping, check_none=True)
        metric_early_stopping = []
        absolute_metric_early_stopping = []
        failure_early_stopping = []
        for es in early_stopping:
            if es.kind == V1FailureEarlyStopping._IDENTIFIER:
                failure_early_stopping.append(es)
            elif es.kind == V1MetricEarlyStopping._IDENTIFIER:
                if es.policy:
                    metric_early_stopping.append(es)
                else:
                    absolute_metric_early_stopping.append(es)

        if cls._check_failure_early_stopping(
            run, early_stopping=failure_early_stopping
        ):
            return True
        if cls._check_absolute_metric_early_stopping(
            run, early_stopping=absolute_metric_early_stopping
        ):
            return True
        if cls._check_metric_early_stopping(run, early_stopping=metric_early_stopping):
            return True

        return False

    @staticmethod
    def _get_upstream_runs(
        run: Models.Run, pipeline_run_id: Optional[int] = None
    ) -> QuerySet:
        upstream = run.upstream_runs
        if pipeline_run_id:
            upstream = upstream.filter(pipeline_id=pipeline_run_id)
        return upstream

    @classmethod
    def _is_upstream_all_done(
        cls, run: Models.Run, pipeline_run_id: Optional[int] = None
    ) -> bool:
        return (
            not cls._get_upstream_runs(run=run, pipeline_run_id=pipeline_run_id)
            .exclude(status__in=LifeCycle.DONE_VALUES)
            .exists()
        )

    @classmethod
    def _is_upstream_one_done(
        cls, run: Models.Run, pipeline_run_id: Optional[int] = None
    ) -> bool:
        return (
            cls._get_upstream_runs(run=run, pipeline_run_id=pipeline_run_id)
            .filter(status__in=LifeCycle.DONE_VALUES)
            .exists()
        )

    @classmethod
    def _is_upstream_all_failed(
        cls, run: Models.Run, pipeline_run_id: Optional[int] = None
    ) -> bool:
        return (
            not cls._get_upstream_runs(run=run, pipeline_run_id=pipeline_run_id)
            .exclude(status=V1Statuses.FAILED)
            .exists()
        )

    @classmethod
    def _is_upstream_one_failed(
        cls, run: Models.Run, pipeline_run_id: Optional[int] = None
    ) -> bool:
        return (
            cls._get_upstream_runs(run=run, pipeline_run_id=pipeline_run_id)
            .filter(status=V1Statuses.FAILED)
            .exists()
        )

    @classmethod
    def _is_upstream_all_succeeded(
        cls, run: Models.Run, pipeline_run_id: Optional[int] = None
    ) -> bool:
        return (
            not cls._get_upstream_runs(run=run, pipeline_run_id=pipeline_run_id)
            .exclude(status=V1Statuses.SUCCEEDED)
            .exists()
        )

    @classmethod
    def _is_upstream_one_succeeded(
        cls, run: Models.Run, pipeline_run_id: Optional[int] = None
    ) -> bool:
        return (
            cls._get_upstream_runs(run=run, pipeline_run_id=pipeline_run_id)
            .filter(status=V1Statuses.SUCCEEDED)
            .exists()
        )

    @classmethod
    def _check_upstream_trigger(
        cls, run: Models.Run, op_spec: V1Operation
    ) -> [bool, bool]:
        """
        Checks the upstream and the trigger rule.

        Returns a tuple containing information about if the run:
         * should start
         * can start
        """
        one_done = cls._is_upstream_one_done(run=run)
        # Early opt-out if not upstream is done
        if not one_done:
            return False, False
        if op_spec.trigger == V1TriggerPolicy.ONE_DONE:
            return one_done, one_done
        if op_spec.trigger == V1TriggerPolicy.ONE_SUCCEEDED:
            return one_done, cls._is_upstream_one_succeeded(run=run)
        if op_spec.trigger == V1TriggerPolicy.ONE_FAILED:
            return one_done, cls._is_upstream_one_failed(run=run)

        all_done = cls._is_upstream_all_done(run=run)
        # Early opt-out if not upstream is done
        if not all_done:
            return False, False
        if op_spec.trigger == V1TriggerPolicy.ALL_DONE:
            return all_done, all_done
        # If not trigger policy is set we assume ALL_SUCCEEDED
        if op_spec.trigger is None or op_spec.trigger == V1TriggerPolicy.ALL_SUCCEEDED:
            return all_done, cls._is_upstream_all_succeeded(run=run)
        if op_spec.trigger == V1TriggerPolicy.ALL_FAILED:
            return all_done, cls._is_upstream_all_failed(run=run)

        return False, False

    @staticmethod
    def _trigger_event_downstream(queryset: QuerySet):
        for down_run in queryset:
            workers.send(
                SchedulerCeleryTasks.RUNS_PREPARE,
                kwargs={"run_id": down_run},
                eager_kwargs={"run": down_run},
            )

    @classmethod
    def _trigger_downstream(cls, queryset: QuerySet, is_skipped: bool = False):
        for down_run in queryset:
            op_spec = V1Operation.read(down_run.raw_content)  # TODO: Use construct
            if is_skipped and op_spec.skip_on_upstream_skip:
                condition = V1StatusCondition.get_condition(
                    type=V1Statuses.SKIPPED,
                    status="True",
                    reason="SchedulerNotifyDone",
                    message="Run is skipped because one of the upstream dependencies is skipped.",
                )
                new_run_status(run=down_run, condition=condition)
                continue

            should_start, can_start = cls._check_upstream_trigger(
                run=down_run, op_spec=op_spec
            )
            if should_start:
                if can_start:
                    workers.send(
                        SchedulerCeleryTasks.RUNS_PREPARE,
                        kwargs={"run_id": down_run.id},
                        eager_kwargs={"run": down_run},
                    )
                else:
                    condition = V1StatusCondition.get_condition(
                        type=V1Statuses.UPSTREAM_FAILED,
                        status="True",
                        reason="SchedulerNotifyDone",
                        message="Run could not be started, upstream error.",
                    )
                    new_run_status(run=down_run, condition=condition)

    @staticmethod
    def _should_iterate(run: Models.Run) -> bool:
        if not (
            run.is_matrix
            and (LifeCycle.is_compiled(run.status) or run.status == V1Statuses.RUNNING)
            and run.runtime in V1MatrixKind.iteration_values()
        ):
            return False

        iteration = run.meta_info.get(META_ITERATION)
        if iteration is None:
            return True

        if hasattr(run, "_compiled_operation"):
            compiled_operation = run._compiled_operation
        else:
            compiled_operation = V1CompiledOperation.read(
                run.content
            )  # TODO: Use construct
            # Cache the compiled_operation to avoid recalculation
            run._compiled_operation = compiled_operation
        if compiled_operation.has_hyperband_matrix:
            bracket_iteration = run.meta_info.get(META_BRACKET_ITERATION, 0)
            compiled_operation.matrix.set_tuning_params()
            return compiled_operation.matrix.should_reschedule(
                iteration, bracket_iteration=bracket_iteration
            )
        return compiled_operation.matrix.should_reschedule(iteration)

    @staticmethod
    def _get_max_budget(run: Models.Run) -> int:
        return -1

    @classmethod
    def _start_pipeline(cls, run: Models.Run):
        dag = flows.get_run_dag(run)
        max_budget = 100
        independent_ops = dags.get_independent_ops(dag)
        run_max_budget = cls._get_max_budget(run)
        if len(independent_ops) > 100 and run_max_budget > 0:
            max_budget = run_max_budget
        independent_ops = Models.Run.objects.filter(
            id__in=independent_ops,
            status=V1Statuses.CREATED,
            pending=None,
        ).values_list("id", flat=True)
        for i_run in independent_ops:
            options = {}
            if max_budget < 0:
                options = {"countdown": 2 + abs(max_budget) // 50}
            workers.send(
                SchedulerCeleryTasks.RUNS_PREPARE, kwargs={"run_id": i_run}, **options
            )
            max_budget -= 1

        condition = V1StatusCondition.get_condition(
            type=V1Statuses.RUNNING,
            status="True",
            reason="SchedulerPipeline",
            message="Operation is running",
        )
        new_run_status(run=run, condition=condition)
        return run

    @classmethod
    def _start_run_for_schedule(cls, pipeline: Models.Run, depends_on_past: bool):
        if LifeCycle.is_done(pipeline.status):
            return
        compiled_operation = V1CompiledOperation.read(
            pipeline.content
        )  # TODO: Use construct
        if compiled_operation.schedule.depends_on_past:
            dependence_cond = depends_on_past is True
        else:
            dependence_cond = depends_on_past is False
        if dependence_cond:
            cls.RESOLVER._create_operation_schedule(
                run=pipeline, compiled_operation=compiled_operation
            )

    @classmethod
    def _start_schedule_based_on_run(cls, run: Models.Run, depends_on_past: bool):
        return cls._start_run_for_schedule(
            pipeline=run.pipeline, depends_on_past=depends_on_past
        )

    @classmethod
    def _create_tuner_operation(cls, run):
        run_uuid = run.uuid.hex
        compiled_operation = V1CompiledOperation.read(
            run.content
        )  # TODO: Use construct
        iteration = run.meta_info.get(META_ITERATION)
        params = dict(
            matrix=compiled_operation.matrix,
            iteration=iteration,
        )
        op = None
        if run.runtime == V1MatrixKind.BAYES:
            op = get_bo_tuner(
                tuner=compiled_operation.matrix.tuner,
                join=cls.RESOLVER._get_pipeline_join(
                    pipeline=run_uuid, metric=compiled_operation.matrix.metric
                ),
                **params,
            )
        elif run.runtime == V1MatrixKind.HYPERBAND:
            try:
                bracket_iteration = run.meta_info.get(META_BRACKET_ITERATION)
                additional_filters = ""
                if iteration is not None:
                    additional_filters += "meta_values.iteration:{}".format(iteration)
                if bracket_iteration:
                    additional_filters += ", meta_values.bracket_iteration:{}".format(
                        bracket_iteration
                    )
                op = get_hyperband_tuner(
                    tuner=compiled_operation.matrix.tuner,
                    join=cls.RESOLVER._get_pipeline_join(
                        pipeline=run_uuid,
                        metric=compiled_operation.matrix.metric,
                        additional_filters=additional_filters,
                    ),
                    bracket_iteration=bracket_iteration,
                    **params,
                )
            except ValueError:
                pass
        elif run.runtime == V1MatrixKind.HYPEROPT:
            op = get_hyperopt_tuner(
                tuner=compiled_operation.matrix.tuner,
                join=cls.RESOLVER._get_pipeline_join(
                    pipeline=run_uuid, metric=compiled_operation.matrix.metric
                ),
                **params,
            )
        elif run.runtime == V1MatrixKind.ITERATIVE:
            # TODO
            return

        if op:
            try:
                tuner = operations.init_run(
                    project_id=run.project_id,
                    user_id=run.user_id,
                    pipeline_id=run.id,
                    op_spec=op,
                    controller_id=run.controller_id or run.id,
                    supported_owners={run.project.owner.name},
                ).instance
                tuner.save()
                return tuner
            except (PolyaxonException, ValueError, ValidationError) as e:
                condition = V1StatusCondition.get_condition(
                    type=V1Statuses.FAILED,
                    status="True",
                    reason="SchedulerTunerError",
                    message=f"Could not create a tuner, an exception was raised:\n{e}",
                )
                new_run_status(run=run, condition=condition)
                return
        cls._capture_message(
            "Iteration algorithm could not create a tuning operation: {}".format(run.id)
        )
        condition = V1StatusCondition.get_condition(
            type=V1Statuses.FAILED,
            status="True",
            reason="SchedulerTunerError",
            message="Iteration algorithm could not create a tuning operation.",
        )
        new_run_status(run=run, condition=condition)

    @staticmethod
    def get_run(
        run_id: int,
        run: Optional[Models.Run] = None,
        use_all: bool = False,
        only: Optional[List[str]] = None,
        defer: Optional[List[str]] = None,
        prefetch: Optional[List[str]] = None,
    ) -> Optional[Models.Run]:
        if run:
            return run
        query = Models.Run.all if use_all else Models.Run.objects
        if only:
            query = query.only(*only)
        if defer:
            query = query.only(*defer)
        if prefetch:
            query = query.select_related(*prefetch)

        try:
            return query.get(id=run_id)
        except Models.Run.DoesNotExist:
            _logger.info(
                "Something went wrong, the run `%s` does not exist anymore.", run_id
            )

    @classmethod
    def runs_prepare(
        cls,
        run_id: int,
        run: Optional[Models.Run] = None,
        start: bool = True,
        extra_message: Optional[str] = None,
    ):
        run = cls.get_run(
            run_id=run_id, run=run, prefetch=cls.DEFAULT_PREFETCH + ["controller"]
        )
        if not run:
            return

        if not LifeCycle.is_compilable(run.status):
            _logger.info(
                "Run `%s` cannot transition from `%s` to `%s`.",
                run_id,
                run.status,
                V1Statuses.COMPILED,
            )
            return

        try:
            compiled_at = now()
            _, compiled_operation = cls._resolve(run=run, compiled_at=compiled_at)
        except PolyaxonCompilerError as e:
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.FAILED,
                status="True",
                reason="SchedulerPrepare",
                message=f"Failed to compile.\n{e}",
            )
            new_run_status(run=run, condition=condition)
            return None
        except Exception as e:
            cls._capture_exception(e)
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.FAILED,
                status="True",
                reason="SchedulerPrepare",
                message="Compiler received an unexpected error.",
            )
            new_run_status(run=run, condition=condition)
            return None

        if run.cloning_kind == V1CloningKind.CACHE or run.pending == V1RunPending.BUILD:
            return run

        message = "Run is compiled"
        if extra_message:
            message = f"{message} ({extra_message})."
        condition = V1StatusCondition.get_condition(
            type=V1Statuses.COMPILED,
            status="True",
            reason="SchedulerPrepare",
            message=message,
            last_update_time=compiled_at,
        )
        new_run_status(run=run, condition=condition)

        if cls._should_iterate(run):
            workers.send(
                SchedulerCeleryTasks.RUNS_TUNE,
                kwargs={"run_id": run_id},
                eager_kwargs={"run": run},
            )
            return run
        if start and run.pending is None:
            workers.send(
                SchedulerCeleryTasks.RUNS_START,
                kwargs={"run_id": run_id},
                eager_kwargs={"run": run},
            )
        return run

    @classmethod
    def runs_start_immediately(cls, run_id: int, run: Optional[Models.Run] = None):
        run = cls.get_run(run_id=run_id, run=run)
        if not run:
            return

        if run.managed_by != ManagedBy.AGENT:
            return

        if LifeCycle.is_done(run.status):
            _logger.info(
                "Run `%s` cannot be started from `%s`.",
                run_id,
                run.status,
            )
            return

        if run.is_matrix or run.is_dag:
            return cls._start_pipeline(run)

        condition = V1StatusCondition.get_condition(
            type=V1Statuses.QUEUED,
            status="True",
            reason="SchedulerStart",
            message="Run is queued",
        )
        new_run_status(run=run, condition=condition)
        return run

    @classmethod
    def runs_start(cls, run_id: int, run: Optional[Models.Run] = None):
        run = cls.get_run(run_id=run_id, run=run, prefetch=["pipeline"])
        if not run:
            return

        if not run.is_managed:
            return

        if LifeCycle.is_done(run.status):
            _logger.info(
                "Run `%s` cannot be started from `%s`.",
                run_id,
                run.status,
            )
            return

        if run.schedule_at:
            cls._start_schedule_based_on_run(run, depends_on_past=False)

        if run.is_schedule:
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.RUNNING,
                status="True",
                reason="SchedulerStart",
                message="Schedule is running",
            )
            new_run_status(run=run, condition=condition)
            return None

        if not LifeCycle.is_compiled(run.status):
            _logger.info(
                "Run `%s` cannot transition from `%s` to `%s`.",
                run_id,
                run.status,
                V1Statuses.QUEUED,
            )
            return None

        # Queue the independent or schedule runs immediately
        start_immediately = bool(not run.pipeline_id or run.schedule_at)
        if not start_immediately and run.pipeline_id:
            start_immediately = LifeCycle.is_done(run.pipeline.status)

        if start_immediately:
            cls.runs_start_immediately(run_id=run_id, run=run)
        return run

    @classmethod
    def runs_set_artifacts(
        cls, run_id: int, run: Optional[Models.Run] = None, artifacts: List[Dict] = None
    ):
        if not artifacts:
            return

        run = cls.get_run(run_id=run_id, run=run)
        if not run:
            return

        artifacts = [V1RunArtifact.from_dict(a) for a in artifacts]
        atomic_set_artifacts(run=run, artifacts=artifacts)

    @classmethod
    def runs_stop(
        cls,
        run_id: int,
        run: Optional[Models.Run] = None,
        reason: str = "PipelineStopping",
        message: Optional[str] = None,
    ):
        run = cls.get_run(run_id=run_id, run=run)
        if not run:
            return

        if run.is_managed:
            if run.is_matrix or run.is_dag or run.is_schedule:
                dependent_runs = Models.Run.objects.filter(
                    Q(pipeline_id=run.id) | Q(controller_id=run.id)
                )
                if not dependent_runs.exclude(
                    status__in=LifeCycle.DONE_VALUES
                ).exists():
                    new_run_stop_status(run=run, message=None)
                    return
                # Set the active ops to stopping
                active_pipeline_runs = dependent_runs.filter(
                    status__in=LifeCycle.ON_K8S_VALUES
                )
                if active_pipeline_runs:
                    condition = V1StatusCondition.get_condition(
                        type=V1Statuses.STOPPING,
                        status="True",
                        reason=reason,
                        message="Pipeline controller requested to stop the run.",
                    )
                    bulk_new_run_status(active_pipeline_runs, condition)
                # Set any dependent pipeline with no pipeline
                pipeline_pipeline_runs = get_stopping_pipelines_with_no_runs(
                    dependent_runs
                )
                if pipeline_pipeline_runs:
                    condition = V1StatusCondition.get_condition(
                        type=V1Statuses.STOPPED,
                        status="True",
                        reason=reason,
                        message="Pipeline controller requested to stop the run.",
                    )
                    bulk_new_run_status(pipeline_pipeline_runs, condition)
                # Set the non active / non done ops to stopped
                pipeline_runs = dependent_runs.exclude(
                    status__in=LifeCycle.ON_K8S_VALUES
                    | LifeCycle.DONE_VALUES
                    | {
                        V1Statuses.STOPPING,
                    }
                )
                if pipeline_runs:
                    condition = V1StatusCondition.get_condition(
                        type=V1Statuses.STOPPED,
                        status="True",
                        reason=reason,
                        message="Pipeline controller requested to stop the run.",
                    )
                    bulk_new_run_status(pipeline_runs, condition)
                # If none of the ops is in the stopping mode we mark the operation as stopped
                if not dependent_runs.exclude(
                    status__in=LifeCycle.DONE_VALUES
                ).exists():
                    new_run_stop_status(run=run, message=None)
                    return
            return
        new_run_stop_status(run=run, message=message)

    @classmethod
    def runs_skip(
        cls,
        run_id: int,
        run: Optional[Models.Run] = None,
        reason: str = "PipelineSKipped",
        message: Optional[str] = None,
    ):
        run = cls.get_run(run_id=run_id, run=run)
        if not run:
            return

        if run.is_managed:
            if run.is_matrix or run.is_dag or run.is_schedule:
                dependent_runs = Models.Run.objects.filter(
                    Q(pipeline_id=run.id) | Q(controller_id=run.id)
                )
                if not dependent_runs.exclude(
                    status__in=LifeCycle.DONE_VALUES
                ).exists():
                    new_run_skip_status(run=run, message=None)
                    return
                # Set the active ops to stopping
                active_pipeline_runs = dependent_runs.filter(
                    status__in=LifeCycle.ON_K8S_VALUES
                )
                if active_pipeline_runs:
                    condition = V1StatusCondition.get_condition(
                        type=V1Statuses.STOPPING,
                        status="True",
                        reason=reason,
                        message="Pipeline controller requested to stop the run.",
                    )
                    bulk_new_run_status(active_pipeline_runs, condition)
                # Set any dependent pipeline with no pipeline
                pipeline_pipeline_runs = get_stopping_pipelines_with_no_runs(
                    dependent_runs
                )
                if pipeline_pipeline_runs:
                    condition = V1StatusCondition.get_condition(
                        type=V1Statuses.SKIPPED,
                        status="True",
                        reason=reason,
                        message="Pipeline controller requested to skip the run.",
                    )
                    bulk_new_run_status(pipeline_pipeline_runs, condition)
                # Set the non active / non done ops to stopped
                pipeline_runs = dependent_runs.exclude(
                    status__in=LifeCycle.ON_K8S_VALUES
                    | LifeCycle.DONE_VALUES
                    | {
                        V1Statuses.STOPPING,
                    }
                )
                if pipeline_runs:
                    condition = V1StatusCondition.get_condition(
                        type=V1Statuses.SKIPPED,
                        status="True",
                        reason=reason,
                        message="Pipeline controller requested to skip the run.",
                    )
                    bulk_new_run_status(pipeline_runs, condition)
                # If none of the ops is in the stopping mode we mark the operation as stopped
                if not dependent_runs.exclude(
                    status__in=LifeCycle.DONE_VALUES
                ).exists():
                    new_run_skip_status(run=run, message=None)
                    return
            return
        new_run_skip_status(run=run, message=message)

    @classmethod
    def runs_hooks(cls, run_id: int, run: Optional[Models.Run] = None):
        run = cls.get_run(run_id=run_id, run=run, prefetch=cls.DEFAULT_PREFETCH)
        if not run:
            return

        if not LifeCycle.is_done(run.status):
            _logger.info(
                "Run `%s` has a current status `%s`. "
                "Scheduler cannot execute hooks before the run is done.",
                run_id,
                run.status,
            )
            return None

        try:
            hook_ops = cls._resolve_hooks(run=run)
        except PolyaxonCompilerError as e:
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.FAILED,
                status="True",
                reason="SchedulerHooksResolve",
                message=f"Hooks resolution failed.\n{e}",
            )
            new_run_status(run=run, condition=condition)
            return None
        except Exception as e:
            cls._capture_exception(e)
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.FAILED,
                status="True",
                reason="SchedulerHooksResolve",
                message="Compiler received an unexpected error.",
            )
            new_run_status(run=run, condition=condition)
            return None

        try:
            hook_runs = cls._execute_hooks(run, hook_ops)
        except PolyaxonCompilerError as e:
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.FAILED,
                status="True",
                reason="SchedulerHooksExecute",
                message=f"Hooks execution failed.\n{e}",
            )
            new_run_status(run=run, condition=condition)
            return None
        except Exception as e:
            cls._capture_exception(e)
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.FAILED,
                status="True",
                reason="SchedulerHooksExecute",
                message="Compiler received an unexpected error.",
            )
            new_run_status(run=run, condition=condition)
            return None

        for hook_run_id in hook_runs:
            workers.send(
                SchedulerCeleryTasks.RUNS_PREPARE,
                kwargs={"run_id": hook_run_id},
            )

    @classmethod
    def runs_built(cls, run_id: int, run: Optional[Models.Run] = None):
        run = cls.get_run(run_id=run_id, run=run, prefetch=cls.DEFAULT_PREFETCH)
        if not run:
            return

        if run.status != V1Statuses.CREATED:
            return

        base_approve_run(run)

        if run.pending is not None:
            return

        cls.runs_prepare(
            run_id=run_id,
            run=run,
            extra_message="Image was built successfully",
            start=True,
        )

    @classmethod
    def runs_iterate(cls, run_id: int, run: Optional[Models.Run] = None):
        run = cls.get_run(run_id=run_id, run=run, prefetch=["pipeline"])
        if not run:
            return

        if not run.pipeline_id:
            return

        outputs = run.outputs or {}
        inputs = run.inputs or {}
        suggestions = outputs.get("suggestions", [])
        iteration = inputs.get(META_ITERATION)
        pipeline = run.pipeline

        if not run.outputs or not suggestions or iteration is None:
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.FAILED,
                status="True",
                reason="EmptyIteration",
                message="Run does not have a more iterations and suggestions, early stopped.",
            )
            new_run_status(run=pipeline, condition=condition)
            return

        compiled_operation = cls._set_iteration_meta_info(
            run=pipeline,
            suggestions=suggestions,
            iteration=iteration,
            bracket_iteration=inputs.get(META_BRACKET_ITERATION),
        )
        if compiled_operation:
            runs = cls.RESOLVER._create_iteration_matrix(
                run=pipeline,
                suggestions=suggestions,
                iteration=iteration,
                compiled_operation=compiled_operation,
            )
            if runs:
                # Create edges
                run_edges = [
                    Models.RunEdge(
                        upstream_id=run.id,
                        downstream_id=r,
                        kind=V1RunEdgeKind.JOIN,
                    )
                    for r in runs
                ]
                if run_edges:
                    Models.RunEdge.objects.bulk_create(run_edges)
        return run

    @classmethod
    def runs_tune(cls, run_id: int, run: Optional[Models.Run] = None):
        run = cls.get_run(run_id=run_id, run=run)
        if not run:
            return

        if LifeCycle.is_compiled(run.status):
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.RUNNING,
                status="True",
                reason="SchedulerIterate",
                message="Starting the optimization process.",
            )
            new_run_status(run=run, condition=condition)

        tuner = cls._create_tuner_operation(run)
        if tuner:
            workers.send(
                SchedulerCeleryTasks.RUNS_PREPARE,
                kwargs={"run_id": tuner.id},
                eager_kwargs={"run": tuner},
            )

    @classmethod
    def runs_notify_status(cls, run_id: int, run: Optional[Models.Run] = None):
        run = cls.get_run(
            run_id=run_id,
            run=run,
            only=[
                "id",
                "schedule_at",
                "pipeline_id",
                "controller_id",
                "status",
                "outputs",
                "meta_info",
            ],
        )
        if not run:
            return

        if run.pipeline_id is None:
            return

        # Queue more runs for the pipeline
        downstream_query = run.downstream_edges.filter(
            downstream__status=V1Statuses.CREATED,
            statuses__contains=[run.status],
            pending=None,
        ).values_list("downstream__id", flat=True)
        cls._trigger_event_downstream(downstream_query)

    @classmethod
    def runs_notify_done(cls, run_id: int, run: Optional[Models.Run] = None):
        run = cls.get_run(
            run_id=run_id,
            run=run,
            only=[
                "id",
                "schedule_at",
                "pipeline_id",
                "controller_id",
                "status",
                "outputs",
                "meta_info",
            ],
        )
        if not run:
            return

        cls._notify_cache(run)
        cls._notify_build(run)
        cls._notify_hooks(run)

        if run.pipeline_id is None:
            return

        if run.schedule_at:
            cls._start_schedule_based_on_run(run=run, depends_on_past=True)
            return

        if run.has_tuner_runtime:
            cls.runs_iterate(run_id=run.id, run=run)

        # Queue more runs for the pipeline
        downstream_query = Models.Run.objects.filter(
            upstream_runs=run_id,
            status=V1Statuses.CREATED,
            pending=None,
        ).prefetch_related("upstream_runs")
        cls._trigger_downstream(
            downstream_query, is_skipped=LifeCycle.skipped(run.status)
        )

        if run.downstream_runs.filter(status=V1Statuses.CREATED).count() == 0:
            workers.send(
                SchedulerCeleryTasks.RUNS_CHECK_PIPELINE,
                kwargs={"run_id": run.pipeline_id},
            )
        else:
            workers.send(
                SchedulerCeleryTasks.RUNS_CHECK_EARLY_STOPPING,
                kwargs={"run_id": run.pipeline_id},
            )

    @classmethod
    def runs_wakeup_schedule(cls, run_id: int, run: Optional[Models.Run] = None):
        run = cls.get_run(
            run_id=run_id,
            run=run,
            prefetch=cls.DEFAULT_PREFETCH,
        )
        if not run:
            return

        cls._start_run_for_schedule(pipeline=run, depends_on_past=True)

    @classmethod
    def runs_check_early_stopping(cls, run_id: int, run: Optional[Models.Run] = None):
        run = cls.get_run(run_id=run_id, run=run, defer=STATUS_UPDATE_COLUMNS_DEFER)
        if not run:
            return

        if cls._should_early_stop(run):
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.STOPPING,
                status="True",
                reason="SchedulerEarlyStopping",
                message="Pipeline was early stopped.",
            )
            new_run_status(run=run, condition=condition)
            pipeline_runs = run.pipeline_runs.exclude(status__in=LifeCycle.DONE_VALUES)
            bulk_new_run_status(pipeline_runs, condition)

    @classmethod
    def runs_check_pipeline(cls, run_id: int, run: Optional[Models.Run] = None):
        run = cls.get_run(run_id=run_id, run=run, defer=STATUS_UPDATE_COLUMNS_DEFER)
        if not run:
            return

        def _early_stop():
            message = "Pipeline met an early stopping condition."
            _condition = V1StatusCondition.get_condition(
                type=V1Statuses.STOPPING,
                status="True",
                reason=reason,
                message=message,
            )
            new_run_status(run=run, condition=_condition)
            cls.runs_stop(
                run_id=run_id, run=run, reason="PipelineEarlyStopping", message=message
            )

        reason = "SchedulerCheckPipeline"
        if is_pipeline_done(run):
            if LifeCycle.stopped(run.status):
                return
            elif cls._should_iterate(run):
                if cls._should_early_stop(run):
                    _early_stop()
                else:
                    workers.send(
                        SchedulerCeleryTasks.RUNS_TUNE,
                        kwargs={"run_id": run_id},
                        eager_kwargs={"run": run},
                    )
                return
            elif LifeCycle.is_stopping(run.status):
                condition = V1StatusCondition.get_condition(
                    type=V1Statuses.STOPPED,
                    status="True",
                    reason=reason,
                    message="Pipeline has stopped.",
                )
            else:
                runs_count = get_failed_stopped_and_all_runs(run.id)
                failed_count = runs_count.get("failed", 0)
                stopped_count = runs_count.get("stopped", 0)
                all_count = runs_count.get("all", 0)
                if failed_count > 0:
                    condition = V1StatusCondition.get_condition(
                        type=V1Statuses.FAILED,
                        status="True",
                        reason=reason,
                        message="Pipeline has failed, some operations did not finish successfully.\n"
                        "Number of failed operations: {}".format(runs_count["failed"]),
                    )
                elif stopped_count > 0 and stopped_count == all_count:
                    condition = V1StatusCondition.get_condition(
                        type=V1Statuses.STOPPED,
                        status="True",
                        reason=reason,
                        message="All operations in this pipeline were stopped.",
                    )
                else:
                    condition = V1StatusCondition.get_condition(
                        type=V1Statuses.SUCCEEDED,
                        status="True",
                        reason=reason,
                        message="Pipeline has succeeded.",
                    )
            new_run_status(run=run, condition=condition)
        elif cls._should_early_stop(run):
            _early_stop()

    @classmethod
    def runs_check_orphan_pipeline(cls, run_id: int, run: Optional[Models.Run] = None):
        run = cls.get_run(
            run_id=run_id, run=run, use_all=True, defer=STATUS_UPDATE_COLUMNS_DEFER
        )
        if not run:
            return

        if Models.Run.all.filter(pipeline_id=run_id).count() == 0:
            run.confirm_delete()

    @staticmethod
    def delete_archived_project(project_id: int):
        try:
            project = Models.Project.all.get(id=project_id)
        except Models.Project.DoesNotExist:
            return

        delete_in_progress_project(project)

    @staticmethod
    def delete_archived_run(run_id):
        try:
            run = Models.Run.all.get(id=run_id)
        except Models.Run.DoesNotExist:
            return

        delete_in_progress_run(run)

    @staticmethod
    def stats_calculation_project(project_id: int):
        project = Models.Project.all.select_related("latest_stats").get(id=project_id)
        current_hour = now().replace(minute=0, second=0, microsecond=0)

        run_count = collect_project_run_count_stats(project=project)
        status_count = collect_project_run_status_stats(project=project)
        run_tracking_time = collect_project_run_duration_stats(project=project)
        version_count = collect_project_version_stats(project=project)
        user_count = collect_project_unique_user_stats(project=project)

        is_new = False
        if (
            project.latest_stats is None
            or project.latest_stats.created_at < current_hour
        ):
            is_new = True
            latest_stats = Models.ProjectStats(project=project)
        else:
            latest_stats = project.latest_stats

        latest_stats.run = run_count
        latest_stats.status = status_count
        latest_stats.tracking_time = run_tracking_time
        latest_stats.version = version_count
        latest_stats.user = user_count
        latest_stats.save()

        if is_new:
            project.latest_stats = latest_stats
            project.save(update_fields=["latest_stats"])
        if user_count and user_count.get("ids"):
            user_count["ids"] = list(user_count["ids"])
            project.contributors.add(*user_count["ids"])
