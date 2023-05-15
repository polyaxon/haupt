import logging
import traceback

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import ValidationError as PydanticValidationError
from rest_framework.exceptions import ValidationError

from django.utils.timezone import now

from haupt.orchestration.scheduler.workflows.hooks import execute_hooks
from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.common import conf, workers
from haupt.common.exceptions import AccessNotAuthorized, AccessNotFound
from haupt.common.options.registry.k8s import K8S_IN_CLUSTER, K8S_NAMESPACE
from haupt.db.abstracts.runs import BaseRun
from haupt.db.defs import Models
from haupt.db.managers.artifacts import atomic_set_artifacts
from haupt.db.managers.statuses import new_run_status, new_run_stop_status
from haupt.orchestration.scheduler.resolver import PlatformResolver
from kubernetes.client.rest import ApiException
from polyaxon.compiler import resolver
from polyaxon.exceptions import (
    PolyaxonCompilerError,
    PolyaxonConverterError,
    PolyaxonK8sError,
    PolyaxonSchemaError,
)
from polyaxon.lifecycle import LifeCycle, V1StatusCondition, V1Statuses
from polyaxon.polyflow import V1CompiledOperation, V1Operation
from traceml.artifacts import V1RunArtifact

_logger = logging.getLogger("polyaxon.scheduler")


class RunsManager:
    DEFAULT_PREFETCH = ["project"]
    RESOLVER = PlatformResolver

    @classmethod
    def _resolve(
        cls,
        run: BaseRun,
        compiled_at: Optional[datetime] = None,
        eager: bool = False,
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
                is_independent=bool(run.pipeline_id),
                eager=eager,
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
    def _resolve_hooks(cls, run: BaseRun) -> List[V1Operation]:
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
        return

    @staticmethod
    def get_run(
        run_id: int,
        run: Optional[BaseRun],
        use_all: bool = False,
        only: Optional[List[str]] = None,
        defer: Optional[List[str]] = None,
        prefetch: Optional[List[str]] = None,
    ) -> Optional[BaseRun]:
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
        run: Optional[BaseRun],
        eager: bool = False,
        extra_message: Optional[str] = None,
    ) -> bool:
        run = cls.get_run(run_id=run_id, run=run, prefetch=cls.DEFAULT_PREFETCH)
        if not run:
            return False

        if not LifeCycle.is_compilable(run.status):
            _logger.info(
                "Run `%s` cannot transition from `%s` to `%s`.",
                run_id,
                run.status,
                V1Statuses.COMPILED,
            )
            return False

        try:
            compiled_at = now()
            _, compiled_operation = cls._resolve(
                run=run, compiled_at=compiled_at, eager=eager
            )
        except PolyaxonCompilerError as e:
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.FAILED,
                status="True",
                reason="SchedulerPrepare",
                message=f"Failed to compile.\n{e}",
            )
            new_run_status(run=run, condition=condition)
            return False
        except Exception as e:
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.FAILED,
                status="True",
                reason="SchedulerPrepare",
                message=f"Compiler received an internal error.\n{e}",
            )
            new_run_status(run=run, condition=condition)
            return False

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

        if run.pending:
            return False

        if eager:
            runs_start(run_id=run.id, run=run)
            return False

        return True

    @classmethod
    def runs_start(cls, run_id: int, run: Optional[BaseRun]):
        run = cls.get_run(run_id=run_id, run=run)
        if not run:
            return

        if not run.is_managed:
            return

        if not LifeCycle.is_compiled(run.status):
            _logger.info(
                "Run `%s` cannot transition from `%s` to `%s`.",
                run_id,
                run.status,
                V1Statuses.QUEUED,
            )
            return

        condition = V1StatusCondition.get_condition(
            type=V1Statuses.QUEUED,
            status="True",
            reason="SchedulerStart",
            message="Run is queued",
        )
        new_run_status(run=run, condition=condition)

        def _log_error(exc: Exception, message: Optional[str] = None):
            message = message or "Could not start the operation.\n"
            message += "error: {}\n{}".format(repr(exc), traceback.format_exc())
            cond = V1StatusCondition.get_condition(
                type=V1Statuses.FAILED,
                status="True",
                reason="SchedulerStart",
                message=message,
            )
            new_run_status(run=run, condition=cond)

        # TODO: Executor
        try:
            in_cluster = conf.get(K8S_IN_CLUSTER)
            if in_cluster and (run.is_service or run.is_job):
                executor.start(
                    content=run.content,
                    owner_name=run.project.owner.name,
                    project_name=run.project.name,
                    run_name=run.name,
                    run_uuid=run.uuid.hex,
                    run_kind=run.kind,
                    namespace=conf.get(K8S_NAMESPACE),
                    in_cluster=in_cluster,
                    default_auth=False,
                )
            return
        except (PolyaxonK8sError, ApiException) as e:
            _log_error(
                exc=e, message="Kubernetes manager could not start the operation.\n"
            )
        except PolyaxonConverterError as e:
            _log_error(exc=e, message="Failed converting the run manifest.\n")
        except Exception as e:
            _log_error(exc=e, message="Failed with unknown exception.\n")

    @classmethod
    def runs_set_artifacts(
        cls, run_id: int, run: Optional[BaseRun], artifacts: List[Dict]
    ):
        run = cls.get_run(run_id=run_id, run=run)
        if not run:
            return

        artifacts = [V1RunArtifact.from_dict(a) for a in artifacts]
        atomic_set_artifacts(run=run, artifacts=artifacts)

    @classmethod
    def runs_stop(
        cls,
        run_id: int,
        run: Optional[BaseRun],
        update_status=False,
        message=None,
        clean=False,
    ) -> bool:
        run = cls.get_run(run_id=run_id, run=run)
        if not run:
            return True

        should_stop = (
            LifeCycle.is_k8s_stoppable(run.status) or run.status == V1Statuses.STOPPING
        )

        # TODO: Executor
        def _clean():
            try:
                executor.clean(
                    run_uuid=run.uuid.hex,
                    run_kind=run.kind,
                    namespace=conf.get(K8S_NAMESPACE),
                    in_cluster=in_cluster,
                )
            except (PolyaxonK8sError, ApiException) as e:
                _logger.warning(
                    "Something went wrong, the run `%s` could not be stopped, error %s",
                    run.uuid,
                    e,
                )
                return False

        if run.is_managed and should_stop:
            in_cluster = conf.get(K8S_IN_CLUSTER)
            if in_cluster and (run.is_service or run.is_job):
                if clean:
                    _clean()
                try:
                    executor.stop(
                        run_uuid=run.uuid.hex,
                        run_kind=run.kind,
                        namespace=conf.get(K8S_NAMESPACE),
                        in_cluster=in_cluster,
                    )
                except (PolyaxonK8sError, ApiException) as e:
                    _logger.warning(
                        "Something went wrong, the run `%s` could not be stopped, error %s",
                        run.uuid,
                        e,
                    )
                    return False

        if not update_status:
            return True

        new_run_stop_status(run=run, message=message)
        return True

    @classmethod
    def runs_hooks(cls, run_id: int, run: Optional[BaseRun]):
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
            hook_runs = execute_hooks(run, hook_ops)
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
    def runs_built(cls, run_id):
        # Move to CE
        return run_id
