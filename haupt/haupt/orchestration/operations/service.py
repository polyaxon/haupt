from collections import namedtuple
from typing import Dict, List, Optional, Set, Tuple, Union

from clipped.utils.lists import to_list

from haupt.common.service_interface import Service
from haupt.db.abstracts.runs import BaseRun
from haupt.db.defs import Models
from haupt.db.managers.statuses import new_run_status
from polyaxon._constants.metadata import (
    META_COPY_ARTIFACTS,
    META_DESTINATION_IMAGE,
    META_HAS_DAGS,
    META_HAS_HOOKS,
    META_HAS_JOBS,
    META_HAS_MATRICES,
    META_HAS_SERVICES,
    META_ITERATION,
    META_RECOMPILE,
    META_UPLOAD_ARTIFACTS,
)
from polyaxon._polyaxonfile import OperationSpecification
from polyaxon._schemas.types import V1ArtifactsType
from polyaxon.schemas import (
    ManagedBy,
    V1CloningKind,
    V1CompiledOperation,
    V1MatrixKind,
    V1Operation,
    V1RunEdgeKind,
    V1RunKind,
    V1RunPending,
    V1ScheduleKind,
    V1StatusCondition,
    V1Statuses,
)


class OperationInitSpec(
    namedtuple(
        "OperationInitSpec",
        "compiled_operation instance related_instance",
    )
):
    def update(self, compiled_operation=None, instance=None, related_instance=None):
        compiled_operation = compiled_operation or self.compiled_operation
        instance = instance or self.instance
        related_instance = related_instance or self.related_instance
        return OperationInitSpec(compiled_operation, instance, related_instance)


class OperationsService(Service):
    SUPPORTS_OP_BUILD = True
    DEFAULT_KINDS = V1RunKind.to_set() | V1MatrixKind.to_set() | V1ScheduleKind.to_set()

    __all__ = (
        "init_run",
        "init_and_save_run",
        "resolve_build",
        "save_build_relation",
        "resume_run",
        "restart_run",
        "copy_run",
    )

    @staticmethod
    def set_spec(spec: V1Operation, **kwargs) -> Tuple[V1Operation, Dict]:
        kwargs["raw_content"] = spec.to_json()
        return spec, kwargs

    @staticmethod
    def get_kind(compiled_operation: V1CompiledOperation) -> Tuple[str, Optional[str]]:
        if compiled_operation.is_tf_job_run:
            return V1RunKind.JOB, V1RunKind.TFJOB
        elif compiled_operation.is_pytorch_job_run:
            return V1RunKind.JOB, V1RunKind.PYTORCHJOB
        elif compiled_operation.is_paddle_job_run:
            return V1RunKind.JOB, V1RunKind.PADDLEJOB
        elif compiled_operation.is_mx_job_run:
            return V1RunKind.JOB, V1RunKind.MXJOB
        elif compiled_operation.is_xgb_job_run:
            return V1RunKind.JOB, V1RunKind.XGBJOB
        elif compiled_operation.is_mpi_job_run:
            return V1RunKind.JOB, V1RunKind.MPIJOB
        elif compiled_operation.is_ray_job_run:
            return V1RunKind.JOB, V1RunKind.RAYJOB
        elif compiled_operation.is_dask_job_run:
            return V1RunKind.JOB, V1RunKind.DASKJOB
        elif compiled_operation.is_tuner_run:
            return V1RunKind.JOB, V1RunKind.TUNER
        elif compiled_operation.is_notifier_run:
            return V1RunKind.JOB, V1RunKind.NOTIFIER
        # Default case
        kind = compiled_operation.run.kind
        return kind, kind

    @classmethod
    def supports_kind(
        cls, kind: str, runtime: str, supported_kinds: Set[str], is_managed: bool
    ) -> bool:
        supported_kinds = supported_kinds or cls.DEFAULT_KINDS
        error_message = (
            "You cannot create this operation. This can happen if "
            "the current project has runtime restrictions, "
            "your account has reached the allowed quota, "
            "or your plan does not support operations of kind: {}"
        )
        if kind not in supported_kinds and is_managed:
            raise ValueError(error_message.format(kind))
        if runtime and runtime not in supported_kinds and is_managed:
            raise ValueError(error_message.format(runtime))
        return True

    @classmethod
    def _finalize_meta_info(cls, meta_info: Dict, **kwargs):
        iteration = kwargs.pop(META_ITERATION, None)
        if iteration is not None:
            meta_info[META_ITERATION] = iteration
        return meta_info

    @classmethod
    def get_meta_info(
        cls,
        compiled_operation: V1CompiledOperation,
        kind: str,
        runtime: str,
        meta_info: Optional[Dict] = None,
        **kwargs,
    ) -> Tuple[str, str, Dict]:
        meta_info = meta_info or {}
        if compiled_operation.hooks:
            meta_info[META_HAS_HOOKS] = True
        if compiled_operation.schedule:
            if compiled_operation.matrix:
                meta_info[META_HAS_MATRICES] = True
            elif kind == V1RunKind.JOB:
                meta_info[META_HAS_JOBS] = True
            elif kind == V1RunKind.SERVICE:
                meta_info[META_HAS_SERVICES] = True
            elif kind == V1RunKind.DAG:
                meta_info[META_HAS_DAGS] = True
            kind = V1RunKind.SCHEDULE
            runtime = compiled_operation.schedule.kind
        elif compiled_operation.matrix:
            if kind == V1RunKind.JOB:
                meta_info[META_HAS_JOBS] = True
            elif kind == V1RunKind.SERVICE:
                meta_info[META_HAS_SERVICES] = True
            elif kind == V1RunKind.DAG:
                meta_info[META_HAS_DAGS] = True
            kind = V1RunKind.MATRIX
            runtime = compiled_operation.matrix.kind

        meta_info = cls._finalize_meta_info(meta_info=meta_info, **kwargs)
        return kind, runtime, meta_info

    @staticmethod
    def sanitize_kwargs(**kwargs):
        kwargs.pop(META_ITERATION, None)
        kwargs.pop("supported_owners", None)
        return kwargs

    def is_valid(self, compiled_operation: V1CompiledOperation):
        compiled_operation.validate_build()
        if compiled_operation.build and not self.SUPPORTS_OP_BUILD:
            raise ValueError(
                "You cannot create this operation. "
                "The build section is not supported in your plan."
            )

    def resolve_build(
        self,
        project_id: int,
        user_id: int,
        compiled_operation: V1CompiledOperation,
        inputs: Dict,
        meta_info: Optional[Dict] = None,
        pending: Optional[str] = None,
        **kwargs,
    ):
        instance = self.init_run(
            project_id=project_id,
            user_id=user_id,
            op_spec=V1Operation.from_build(compiled_operation.build, contexts=inputs),
            pending=pending,
            meta_info=meta_info,
            supported_owners=kwargs.get("supported_owners"),
        ).instance
        instance.runtime = V1RunKind.BUILDER
        return instance

    def _clone_build(self, original_run, run):
        build = (
            original_run.upstream_runs.filter(
                downstream_edges__kind=V1RunEdgeKind.BUILD
            )
            .order_by("created_at")
            .only("id")
            .last()
        )
        Models.RunEdge(
            upstream_id=build.id,
            downstream_id=run.id,
            kind=V1RunEdgeKind.BUILD,
        ).save()

    @staticmethod
    def save_build_relation(run_init_spec: OperationInitSpec):
        run_init_spec.related_instance.save()
        Models.RunEdge(
            upstream_id=run_init_spec.related_instance.id,
            downstream_id=run_init_spec.instance.id,
            kind=V1RunEdgeKind.BUILD,
        ).save()

    def init_run(
        self,
        project_id: int,
        user_id: int,
        op_spec: V1Operation = None,
        compiled_operation: V1CompiledOperation = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None,
        override: Optional[Union[str, Dict]] = None,
        use_override_patch_strategy: bool = False,
        params: Optional[Dict] = None,
        readme: Optional[str] = None,
        original_id: Optional[int] = None,
        cloning_kind: Optional[str] = None,
        managed_by: Optional[ManagedBy] = ManagedBy.AGENT,
        pending: Optional[str] = None,
        meta_info: Optional[Dict] = None,
        supported_kinds: Set[str] = None,
        **kwargs,
    ) -> OperationInitSpec:
        if op_spec:
            op_spec, kwargs = self.set_spec(op_spec, **kwargs)
        if op_spec:
            if not compiled_operation or override:
                compiled_operation = OperationSpecification.compile_operation(
                    op_spec,
                    override=override,
                    use_override_patch_strategy=use_override_patch_strategy,
                )
            params = op_spec.params

        params = params or {}
        inputs = {p: pv.value for p, pv in params.items() if pv.is_literal}
        params = {p: pv.to_dict() for p, pv in params.items()}
        kind = None
        meta_info = meta_info or {}
        build_instance = None
        runtime = None
        if compiled_operation:
            self.is_valid(compiled_operation)
            # If the is ab upload we need to check the build process immediately
            if pending == V1RunPending.UPLOAD and compiled_operation.build:
                upload_artifacts = meta_info.pop(META_UPLOAD_ARTIFACTS, None)
                build_instance = self.resolve_build(
                    project_id=project_id,
                    user_id=user_id,
                    compiled_operation=compiled_operation,
                    inputs=inputs,
                    meta_info={META_UPLOAD_ARTIFACTS: upload_artifacts}
                    if upload_artifacts
                    else None,
                    pending=V1RunPending.UPLOAD,
                    **kwargs,
                )
                # Change the pending logic to wait to build and remove build requirements
                compiled_operation.build = None
                pending = V1RunPending.BUILD
            # If the is a clone/resume we need to check the build process and remove it
            if cloning_kind and compiled_operation.build:
                compiled_operation.build = None

            if pending is None and compiled_operation.is_approved is False:
                pending = V1RunPending.APPROVAL
            name = name or compiled_operation.name
            description = description or compiled_operation.description
            tags = tags or compiled_operation.tags
            if tags:
                tags = to_list(tags, check_none=True, to_unique=True)
            kind, runtime = self.get_kind(compiled_operation)
            kind, runtime, meta_info = self.get_meta_info(
                compiled_operation, kind, runtime, meta_info, **kwargs
            )
            self.supports_kind(
                kind, runtime, supported_kinds, ManagedBy.is_managed(managed_by)
            )
            kwargs["content"] = compiled_operation.to_json()
        instance = Models.Run(
            project_id=project_id,
            user_id=user_id,
            name=name,
            description=description,
            tags=tags,
            readme=readme,
            params=params,
            inputs=inputs,
            kind=kind,
            runtime=runtime,
            meta_info=meta_info,
            original_id=original_id,
            cloning_kind=cloning_kind,
            managed_by=managed_by,
            pending=pending,
            status_conditions=[
                V1StatusCondition.get_condition(
                    type=V1Statuses.CREATED,
                    status="True",
                    reason=kwargs.pop("reason", "OperationServiceInit"),
                    message=kwargs.pop("message", "Run is created"),
                ).to_dict()
            ],
            **self.sanitize_kwargs(**kwargs),
        )
        return OperationInitSpec(compiled_operation, instance, build_instance)

    def init_and_save_run(
        self,
        project_id: int,
        user_id: int,
        op_spec: V1Operation = None,
        compiled_operation: V1CompiledOperation = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None,
        override: Optional[Union[str, Dict]] = None,
        params: Optional[Dict] = None,
        readme: Optional[str] = None,
        managed_by: Optional[ManagedBy] = ManagedBy.AGENT,
        pending: Optional[str] = None,
        meta_info: Optional[Dict] = None,
        pipeline_id: Optional[int] = None,
        controller_id: Optional[int] = None,
        supported_kinds: Set[str] = None,
        supported_owners: Set[str] = None,
    ):
        run_init_spec = self.init_run(
            project_id=project_id,
            user_id=user_id,
            name=name,
            description=description,
            op_spec=op_spec,
            compiled_operation=compiled_operation,
            override=override,
            params=params,
            readme=readme,
            pipeline_id=pipeline_id,
            controller_id=controller_id,
            tags=tags,
            managed_by=managed_by,
            pending=pending,
            meta_info=meta_info,
            supported_kinds=supported_kinds,
            supported_owners=supported_owners,
        )
        run_init_spec.instance.save()
        if run_init_spec.related_instance:
            self.save_build_relation(run_init_spec)
        return run_init_spec.instance

    def resume_run(
        self,
        run: BaseRun,
        user_id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        readme: Optional[str] = None,
        tags: Optional[List[str]] = None,
        supported_kinds: Set[str] = None,
        message=None,
        **kwargs,
    ):
        meta_info = kwargs.pop("meta_info", {}) or {}
        status_meta_info = kwargs.pop("status_meta_info", None)
        recompile = meta_info.pop(META_RECOMPILE, False)
        if recompile:
            op_spec = V1Operation.read(content)
            content = None
        else:
            op_spec = V1Operation.read(run.raw_content)  # TODO: Use constructor
        instance = self.init_run(
            project_id=run.project_id,
            user_id=user_id or run.user_id,
            name=name or run.name,
            description=description or run.description,
            readme=readme or run.readme,
            op_spec=op_spec,
            tags=tags or run.tags,
            override=content,
            supported_kinds=supported_kinds,
            cloning_kind=V1CloningKind.RESTART,  # To clean the build if any
            use_override_patch_strategy=True,
            **kwargs,
        ).instance

        run.user_id = instance.user_id
        run.name = instance.name
        run.description = instance.description
        run.readme = instance.readme
        run.content = instance.content
        run.raw_content = instance.raw_content
        run.tags = instance.tags
        run.params = instance.params
        run.save()
        status_condition = V1StatusCondition.get_condition(
            type=V1Statuses.RESUMING,
            status=True,
            reason="ResumeManager",
            message=message,
        )
        if status_meta_info:
            status_condition.meta_info = status_meta_info
        new_run_status(
            run,
            condition=status_condition,
            force=True,
        )
        return run

    def _clone_run(
        self,
        run: BaseRun,
        cloning_kind: str,
        user_id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        readme: Optional[str] = None,
        tags: List[int] = None,
        supported_kinds: Set[str] = None,
        supported_owners: Set[str] = None,
        **kwargs,
    ) -> BaseRun:
        meta_info = kwargs.pop("meta_info", {}) or {}
        recompile = meta_info.pop(META_RECOMPILE, False)
        if recompile:
            op_spec = V1Operation.read(content)
            content = None
        else:
            op_spec = V1Operation.read(run.raw_content)  # TODO: Use constructor
        original_meta_info = run.meta_info or {}
        original_uuid = run.uuid.hex
        upload_artifacts = original_meta_info.get(META_UPLOAD_ARTIFACTS)
        build_destination = original_meta_info.get(META_DESTINATION_IMAGE)
        if build_destination:
            meta_info[META_DESTINATION_IMAGE] = build_destination
        if upload_artifacts:
            meta_info[META_UPLOAD_ARTIFACTS] = upload_artifacts
        if cloning_kind == V1CloningKind.COPY and META_COPY_ARTIFACTS not in meta_info:
            # Handle default copy mode
            meta_info[META_COPY_ARTIFACTS] = V1ArtifactsType(
                dirs=[original_uuid]
            ).to_dict()
        if META_COPY_ARTIFACTS not in meta_info and upload_artifacts:
            # Handle default copy mode
            meta_info[META_COPY_ARTIFACTS] = V1ArtifactsType(
                dirs=["{}/{}".format(original_uuid, upload_artifacts)]
            ).to_dict()

        instance = self.init_run(
            project_id=run.project_id,
            user_id=user_id or run.user_id,
            name=name or run.name,
            description=description or run.description,
            readme=readme or run.readme,
            op_spec=op_spec,
            original_id=run.id,
            cloning_kind=cloning_kind,
            tags=tags or run.tags,
            override=content,
            supported_kinds=supported_kinds,
            supported_owners=supported_owners,
            meta_info=meta_info,
            use_override_patch_strategy=True,
            **kwargs,
        ).instance
        instance.save()
        if build_destination:
            self._clone_build(original_run=run, run=instance)
        return instance

    def restart_run(
        self,
        run: BaseRun,
        user_id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        readme: Optional[str] = None,
        tags: List[int] = None,
        supported_kinds: Set[str] = None,
        supported_owners: Set[str] = None,
        **kwargs,
    ) -> BaseRun:
        return self._clone_run(
            run=run,
            cloning_kind=V1CloningKind.RESTART,
            user_id=user_id,
            name=name,
            description=description,
            content=content,
            readme=readme,
            tags=tags,
            supported_kinds=supported_kinds,
            supported_owners=supported_owners,
            **kwargs,
        )

    def copy_run(
        self,
        run: BaseRun,
        user_id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        readme: Optional[str] = None,
        tags: List[int] = None,
        supported_kinds: Set[str] = None,
        supported_owners: Set[str] = None,
        **kwargs,
    ) -> BaseRun:
        return self._clone_run(
            run=run,
            cloning_kind=V1CloningKind.COPY,
            user_id=user_id,
            name=name,
            description=description,
            content=content,
            readme=readme,
            tags=tags,
            supported_kinds=supported_kinds,
            supported_owners=supported_owners,
            **kwargs,
        )
