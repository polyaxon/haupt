import uuid

from datetime import datetime, timedelta
from functools import reduce
from operator import or_
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from clipped.config.patch_strategy import PatchStrategy
from clipped.utils.bools import to_bool
from clipped.utils.lists import to_list

from django.conf import settings
from django.db.models import Count, Q
from django.utils.timezone import now

from croniter import croniter
from haupt.common.db.runs import bulk_create_runs
from haupt.common.exceptions import AccessNotAuthorized, AccessNotFound
from haupt.db.abstracts.project_versions import BaseProjectVersion
from haupt.db.abstracts.runs import BaseRun
from haupt.db.defs import Models
from haupt.db.managers.artifacts import set_artifacts
from haupt.db.managers.cache import get_run_state
from haupt.db.managers.statuses import new_run_status
from haupt.db.managers.versions import get_component_version_state
from haupt.db.query_managers.run import RunsOfflineFilter
from haupt.orchestration import operations
from hypertune.search_managers.grid_search.manager import GridSearchManager
from hypertune.search_managers.mapping.manager import MappingManager
from hypertune.search_managers.random_search.manager import RandomSearchManager
from polyaxon._auxiliaries import V1PolyaxonSidecarContainer
from polyaxon._compiler import resolver
from polyaxon._compiler.lineage import collect_lineage_artifacts_path
from polyaxon._constants.metadata import (
    META_CONCURRENCY,
    META_COPY_ARTIFACTS,
    META_DESTINATION_IMAGE,
    META_EDGE,
    META_HAS_DAGS,
    META_HAS_DOWNSTREAM_EVENTS_TRIGGER,
    META_HAS_EARLY_STOPPING,
    META_HAS_JOBS,
    META_HAS_MATRICES,
    META_HAS_SCHEDULES,
    META_HAS_SERVICES,
    META_IS_EXTERNAL,
    META_PORTS,
    META_REWRITE_PATH,
    META_UPLOAD_ARTIFACTS,
)
from polyaxon._contexts import keys as ctx_keys
from polyaxon._contexts import paths as ctx_paths
from polyaxon._contexts import refs as ctx_refs
from polyaxon._contexts import sections as ctx_sections
from polyaxon._env_vars.getters import get_versioned_entity_info
from polyaxon._polyaxonfile import CompiledOperationSpecification
from polyaxon._polyaxonfile.manager import (
    get_op_from_schedule,
    get_ops_from_suggestions,
)
from polyaxon._schemas.lifecycle import ManagedBy
from polyaxon._utils.fqn_utils import (
    get_project_instance,
    get_run_instance,
    get_run_lineage_paths,
)
from polyaxon.exceptions import PolyaxonCompilerError, PQLException
from polyaxon.schemas import (
    DagOpSpec,
    LifeCycle,
    V1ArtifactsType,
    V1CloningKind,
    V1CompiledOperation,
    V1Init,
    V1Join,
    V1JoinParam,
    V1Operation,
    V1OptimizationMetric,
    V1Param,
    V1Plugins,
    V1ProjectVersionKind,
    V1RunEdgeKind,
    V1RunPending,
    V1StatusCondition,
    V1Statuses,
    ops_params,
)


class SchedulingResolver(resolver.BaseResolver):
    def __init__(
        self,
        run: BaseRun,
        compiled_operation: V1CompiledOperation,
        owner_name: str,
        project_name: str,
        project_uuid: str,
        run_name: str,
        run_uuid: str,
        run_path: str,
        params: Optional[Dict],
        created_at: Optional[datetime] = None,
        compiled_at: Optional[datetime] = None,
        cloning_kind: V1CloningKind = None,
        original_uuid: Optional[str] = None,
        is_independent: bool = True,
    ):
        super().__init__(
            run=run,
            compiled_operation=compiled_operation,
            owner_name=owner_name,
            project_name=project_name,
            project_uuid=project_uuid,
            run_name=run_name,
            run_uuid=run_uuid,
            run_path=run_path,
            params=params,
            created_at=created_at,
            compiled_at=compiled_at,
            cloning_kind=cloning_kind,
            original_uuid=original_uuid,
            is_independent=is_independent,
        )
        self.project = self.run.project
        self.schedule_at = self.run.schedule_at
        self.started_at = self.run.started_at
        self.finished_at = self.run.finished_at
        self.duration = self.run.duration
        self.owner = self.project.owner

    @staticmethod
    def _collect_hub_refs(ops: List[V1Operation], owner_name: str) -> Dict:
        return {}

    @staticmethod
    def _get_upstream_run_params(
        owner_id: int,
        run_name: str,
        run_id: int,
        params: Dict[str, Dict],
        edge_kind: V1RunEdgeKind,
    ):
        if not params:
            return []

        params = {p: V1Param.construct(**params[p]) for p in params}

        upstream_run_params_by_names = ops_params.get_upstream_run_params_by_names(
            params=params
        )
        run_uuids = {
            param_spec.param.entity_ref
            for param_specs in upstream_run_params_by_names.values()
            for param_spec in param_specs
        }
        runs_queryset = Models.Run.objects
        if settings.HAS_ORG_MANAGEMENT:
            runs_queryset = runs_queryset.filter(project__owner__id=owner_id)
        run_ids_by_uuids = {
            v["uuid"].hex: v
            for v in runs_queryset.filter(uuid__in=run_uuids).values(
                "id", "uuid", "meta_info"
            )
        }
        if len(run_uuids) != len(run_ids_by_uuids):
            raise ValueError(
                f"Operation {run_name} is requesting outputs access to a run(s) that does not exists: "
                f"{set(run_uuids) - set(run_ids_by_uuids)}"
            )
        for run_upstream in upstream_run_params_by_names:
            if edge_kind not in V1RunEdgeKind.to_set():
                edge_kind = V1RunEdgeKind.RUN
            yield Models.RunEdge(
                upstream_id=run_ids_by_uuids[run_upstream]["id"],
                downstream_id=run_id,
                kind=edge_kind,
                values={
                    param_spec.name: param_spec.param.value
                    for param_spec in upstream_run_params_by_names[run_upstream]
                },
            )

    @classmethod
    def _resolve_edges(cls, run: BaseRun):
        # We check if we need to resolve any missing run params
        run_edges = []
        try:
            run_edges.extend(
                cls._get_upstream_run_params(
                    owner_id=run.project.owner_id,
                    run_name=run.name,
                    run_id=run.id,
                    params=run.params,
                    edge_kind=run.meta_info.get(META_EDGE, V1RunEdgeKind.RUN),
                )
            )
        except ValueError as e:
            raise AccessNotAuthorized(e)
        if run_edges:
            upstream_ids = {r.upstream_id for r in run_edges}
            # We check if any of the runs does not exist on the current project
            if (
                Models.Run.objects.exclude(project_id=run.project_id)
                .filter(id__in=upstream_ids)
                .count()
                > 0
            ):
                raise AccessNotAuthorized(
                    f"Run {run.name} request access to runs outside of the current project."
                )
            # We check the edge that require updating/creating (handles resume use case)
            run_edges_by_runs = {(r.upstream_id, r.downstream_id): r for r in run_edges}
            run_edges_keys = list(run_edges_by_runs.keys())
            query = reduce(
                or_, (Q(upstream_id=k[0], downstream_id=k[1]) for k in run_edges_keys)
            )
            to_update = Models.RunEdge.objects.filter(query).only(
                "id",
                "upstream_id",
                "downstream_id",
                "kind",
                "values",
            )
            _to_update = {(m.upstream_id, m.downstream_id) for m in to_update}
            to_create = {m for m in run_edges_keys if m not in _to_update}
            if to_update:
                updated = []
                for m in to_update:
                    key = (m.upstream_id, m.downstream_id)
                    m.kind = run_edges_by_runs[key].kind
                    m.values = run_edges_by_runs[key].values
                    updated.append(m)
                Models.RunEdge.objects.bulk_update(updated, ["kind", "values"])
            if to_create:
                Models.RunEdge.objects.bulk_create(
                    [run_edges_by_runs[m] for m in to_create]
                )

        return run_edges

    @staticmethod
    def _get_edge_queryset(queryset):
        return queryset.prefetch_related("artifacts").only(
            "id",
            "inputs",
            "outputs",
            "uuid",
            "name",
            "status",
            "created_at",
            "schedule_at",
            "started_at",
            "finished_at",
            "wait_time",
            "duration",
            "cloning_kind",
            "artifacts__id",
            "artifacts__name",
            "artifacts__path",
        )

    @staticmethod
    def _get_edge_param_value(
        edge_v: Union[str, Dict],
        inputs: Dict,
        outputs: Dict,
        artifacts: Dict,
        owner: str,
        project_name,
        uuid: str,
        name: str,
        status: str,
        condition: Dict,
        created_at: datetime,
        schedule_at: datetime,
        started_at: datetime,
        finished_at: datetime,
        duration: float,
        cloning_kind: V1CloningKind,
    ):
        artifacts_path = ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(uuid)
        outputs_path = ctx_paths.CONTEXT_MOUNT_RUN_OUTPUTS_FORMAT.format(uuid)

        e_outputs = outputs or {}
        e_inputs = inputs or {}
        e_artifacts = artifacts or {}
        for k, v in e_artifacts.items():
            if v is not None:
                e_artifacts[k] = get_run_lineage_paths(uuid, [v])[0]
        e_globals = {
            ctx_keys.UUID: uuid,
            ctx_keys.NAME: name,
            ctx_keys.STATUS: status,
            ctx_keys.CONDITION: condition,
            ctx_keys.OWNER_NAME: owner,
            ctx_keys.PROJECT_NAME: project_name,
            ctx_keys.PROJECT_UNIQUE_NAME: get_project_instance(owner, project_name),
            ctx_keys.RUN_INFO: get_run_instance(owner, project_name, uuid),
            ctx_keys.CONTEXT_PATH: ctx_paths.CONTEXT_ROOT,
            ctx_keys.ARTIFACTS_PATH: ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
            ctx_keys.RUN_ARTIFACTS_PATH: artifacts_path,
            ctx_keys.RUN_OUTPUTS_PATH: outputs_path,
            ctx_keys.CREATED_AT: created_at,
            ctx_keys.SCHEDULE_AT: schedule_at,
            ctx_keys.STARTED_AT: started_at,
            ctx_keys.FINISHED_AT: finished_at,
            ctx_keys.DURATION: duration,
            ctx_keys.CLONING_KIND: cloning_kind,
        }

        def from_outputs():
            if not entity_value:
                return e_outputs
            if entity_value in e_outputs:
                return e_outputs[entity_value]

        def from_inputs():
            if not entity_value:
                return e_inputs
            if entity_value in e_inputs:
                return e_inputs[entity_value]

        def from_artifacts():
            outputs_subpath = ctx_paths.CONTEXTS_OUTPUTS_SUBPATH_FORMAT.format(uuid)
            if not entity_value:
                return dict(
                    {ctx_keys.BASE: uuid, ctx_sections.OUTPUTS: outputs_subpath},
                    **e_artifacts,
                )
            if entity_value == ctx_keys.BASE:
                return uuid
            if entity_value == ctx_sections.OUTPUTS:
                return outputs_subpath
            if entity_value in e_artifacts:
                return e_artifacts[entity_value]

        def from_globals():
            if not entity_value:
                return e_globals
            if entity_value in e_globals:
                return e_globals[entity_value]

        if isinstance(edge_v, dict):
            param_value = {}
            if "files" in edge_v:
                param_value["files"] = [
                    "{}/{}".format(uuid, i)
                    for i in to_list(edge_v["files"], check_none=True)
                ]
            if "dirs" in edge_v:
                param_value["dirs"] = [
                    "{}/{}".format(uuid, i)
                    for i in to_list(edge_v["dirs"], check_none=True)
                ]

            return param_value, True

        entity_type = ctx_refs.get_entity_type(edge_v)
        entity_value = ctx_refs.get_entity_value(edge_v)
        if entity_type == ctx_sections.INPUTS_OUTPUTS:
            return {
                ctx_sections.INPUTS: e_inputs,
                ctx_sections.OUTPUTS: e_outputs,
                ctx_sections.ARTIFACTS: e_artifacts,
            }, False
        if entity_type == ctx_sections.OUTPUTS:
            param_value = from_outputs()
        elif entity_type == ctx_sections.INPUTS:
            param_value = from_inputs()
        elif entity_type == ctx_sections.GLOBALS:
            param_value = from_globals()
        elif entity_type == ctx_sections.ARTIFACTS:
            param_value = from_artifacts()
        else:
            param_value = None

        return param_value, False

    @classmethod
    def _resolve_params(cls, run: BaseRun) -> Dict:
        # Get params by name
        params = run.params or {}
        if not params:
            return params

        def populate_context_from_results():
            owner = run.project.owner.name
            project_name = run.project.name
            for edge in edges:
                edge_values = edge.values
                edge_io = upstream_runs.get(edge.upstream_id)
                # Check if the edge still exists, user might have deleted the upstream run
                if not edge_io:
                    continue
                for edge_k, edge_v in edge_values.items():
                    param_value, is_value_artifacts = cls._get_edge_param_value(
                        edge_v=edge_v,
                        inputs=edge_io.inputs,
                        outputs=edge_io.outputs,
                        artifacts={a.name: a.path for a in edge_io.artifacts.all()},
                        owner=owner,
                        project_name=project_name,
                        uuid=edge_io.uuid.hex,
                        name=edge_io.name,
                        status=edge_io.status,
                        condition=edge_io.get_last_condition(),
                        created_at=edge_io.created_at,
                        schedule_at=edge_io.schedule_at,
                        started_at=edge_io.started_at,
                        finished_at=edge_io.finished_at,
                        duration=edge_io.duration,
                        cloning_kind=edge_io.cloning_kind,
                    )
                    if param_value:
                        current_param = params.get(edge_k, {})
                        current_param.pop("ref", None)
                        current_param["value"] = param_value
                        params[edge_k] = current_param

        # We get all run edges's values and then we resolve against the inputs/outputs
        edges = run.upstream_edges.exclude(values__isnull=True)
        queryset_without_cache = cls._get_edge_queryset(
            run.upstream_runs.exclude(cloning_kind=V1CloningKind.CACHE)
        )
        # Handle cache hits
        op_to_original = {
            v["original_id"]: v["id"]
            for v in run.upstream_runs.filter(cloning_kind=V1CloningKind.CACHE).values(
                "id", "original_id"
            )
        }
        queryset_cached = cls._get_edge_queryset(
            Models.Run.objects.filter(id__in=op_to_original.keys())
        )
        queryset = queryset_without_cache.union(queryset_cached)
        upstream_runs = {}
        for r in queryset:
            if r.id in op_to_original:
                upstream_runs[op_to_original[r.id]] = r
            else:
                upstream_runs[r.id] = r
        populate_context_from_results()

        # We get the params from the op
        return params

    def _resolve_joins(self) -> Dict:
        joins = self.compiled_operation.joins
        offline_filter = RunsOfflineFilter()
        edge_values_by_ids = {}
        param_values = {}
        owner = self.run.project.owner.name
        project_name = self.run.project.name

        def resolve_join_runs(j: V1Join):
            edge_values = {p: j.params[p].value for p in j.params}
            try:
                limit = RunsOfflineFilter.positive_int(
                    j.limit or 5000, strict=True, cutoff=5000
                )
                offset = RunsOfflineFilter.positive_int(j.offset or 0, strict=False)
            except (ValueError, TypeError):
                raise PolyaxonCompilerError(
                    "Received a wrong join (limit/offset) specification. "
                    "Join: {}.".format(join.to_dict())
                )
            queryset = Models.Run.objects.filter(project_id=self.run.project_id)
            try:
                queryset = offline_filter.filter_join(queryset=queryset, join=j)
            except PQLException as e:
                raise PolyaxonCompilerError(
                    "Received a wrong join specification. "
                    "Join: {}. Error: {}".format(join.to_dict(), e)
                )

            queryset = self._get_edge_queryset(queryset)[offset : offset + limit]
            for run_values in queryset:
                if run_values.id not in edge_values_by_ids:
                    edge_values_by_ids[run_values.id] = {}
                edge_values_by_ids[run_values.id].update(edge_values)
                for edge_k, edge_v in edge_values.items():
                    param_value, is_value_artifacts = self._get_edge_param_value(
                        edge_v=edge_v,
                        inputs=run_values.inputs,
                        outputs=run_values.outputs,
                        artifacts={a.name: a.path for a in run_values.artifacts.all()},
                        owner=owner,
                        project_name=project_name,
                        uuid=run_values.uuid.hex,
                        name=run_values.name,
                        status=run_values.status,
                        condition=run_values.get_last_condition(),
                        created_at=run_values.created_at,
                        schedule_at=run_values.schedule_at,
                        started_at=run_values.started_at,
                        finished_at=run_values.finished_at,
                        duration=run_values.duration,
                        cloning_kind=run_values.cloning_kind,
                    )
                    if param_value:
                        if is_value_artifacts:
                            if edge_k not in param_values:
                                param_values[edge_k] = {"files": [], "dirs": []}
                            param_values[edge_k] = {
                                "files": param_values[edge_k]["files"]
                                + param_value.get("files", []),
                                "dirs": param_values[edge_k]["dirs"]
                                + param_value.get("dirs", []),
                            }
                        else:
                            if edge_k not in param_values:
                                param_values[edge_k] = []
                            param_values[edge_k].append(param_value)
                    else:
                        if edge_k not in param_values:
                            param_values[edge_k] = []
                        param_values[edge_k].append(param_value)

        for join in joins:
            resolve_join_runs(join)

        run_edges = []
        for run_id in edge_values_by_ids:
            run_edges.append(
                Models.RunEdge(
                    upstream_id=run_id,
                    downstream_id=self.run.id,
                    kind=V1RunEdgeKind.JOIN,
                    values=edge_values_by_ids[run_id],
                )
            )

        if run_edges:
            Models.RunEdge.objects.bulk_create(run_edges)

        # Create params
        params = {}
        for join in joins:
            for edge_k in join.params:
                current_param = join.params.get(edge_k)
                if not current_param:
                    continue
                if edge_k not in params:
                    params[edge_k] = {}
                params[edge_k]["value"] = param_values.get(edge_k)
                if current_param.context_only:
                    params[edge_k]["contextOnly"] = current_param.context_only
                if current_param.connection:
                    params[edge_k]["connection"] = current_param.connection
                if current_param.to_init:
                    params[edge_k]["toInit"] = current_param.to_init

        return params

    def _resolve_joins_params(self):
        if self.compiled_operation.joins:
            self.apply_params(should_be_resolved=False)
            self.compiled_operation.joins = [
                V1Join.read(
                    CompiledOperationSpecification.apply_section_contexts(
                        config=self.compiled_operation,
                        section=join.to_dict(),
                        param_spec=self.param_spec,
                    )
                )  # TODO: Use construct
                for join in self.compiled_operation.joins
            ]
            self.params.update(self._resolve_joins())

    def _resolve_matrix_params(self):
        if self.compiled_operation.matrix:
            self.apply_params(should_be_resolved=False)
            self.compiled_operation.matrix = (
                self.compiled_operation.matrix.__class__.read(
                    CompiledOperationSpecification.apply_section_contexts(
                        config=self.compiled_operation,
                        section=self.compiled_operation.matrix.to_dict(),
                        param_spec=self.param_spec,
                    )
                )
            )

    def resolve_edges(self):
        self._resolve_edges(run=self.run)

    def resolve_params(self):
        self.params = self._resolve_params(run=self.run)
        self._resolve_joins_params()
        self._resolve_matrix_params()

    def resolve_io(self):
        if self.compiled_operation.inputs:
            self.run.inputs = {
                io.name: io.value for io in self.compiled_operation.inputs
            }
        if self.compiled_operation.outputs:
            self.run.outputs = {
                io.name: io.value for io in self.compiled_operation.outputs
            }

    def _get_meta_artifacts_presets(self) -> List:
        if not self.run.meta_info or META_COPY_ARTIFACTS not in self.run.meta_info:
            return []

        artifacts = self.run.meta_info.pop(META_COPY_ARTIFACTS)
        artifacts = V1ArtifactsType.read(artifacts)

        def get_relative_to_run_artifacts(v: str):
            paths = v.split("/")[1:]
            paths = ["{{ globals.run_artifacts_path }}"] + paths
            return "/".join(paths)

        # Populate all paths
        if artifacts.dirs:
            artifacts.dirs = [
                [d, get_relative_to_run_artifacts(d)] for d in artifacts.dirs
            ]
        if artifacts.files:
            artifacts.files = [
                [d, get_relative_to_run_artifacts(d)] for d in artifacts.files
            ]
        init = V1Init.construct(artifacts=artifacts)
        return [{"runPatch": {"init": [init.to_dict()]}}]

    def _get_meta_destination_image(self) -> Optional[str]:
        meta_info = self.run.meta_info or {}
        return meta_info.get(META_DESTINATION_IMAGE)

    def resolve_presets(self):
        for preset in self._get_meta_artifacts_presets():
            self.compiled_operation = CompiledOperationSpecification.apply_preset(
                config=self.compiled_operation, preset=preset
            )

    def _pre_persist_state(self):
        # Slow sync process
        if not self.run.controller_id and not self.run.pipeline_id:
            return
        self.compiled_operation.plugins = self.compiled_operation.plugins or V1Plugins()
        self.compiled_operation.plugins.sidecar = (
            self.compiled_operation.plugins.sidecar or V1PolyaxonSidecarContainer()
        )
        if self.compiled_operation.plugins.sidecar.sync_interval is None:
            self.compiled_operation.plugins.sidecar.sync_interval = 60

    def _persist_meta_info(self):
        # Handle concurrency
        if self.run.is_matrix and self.compiled_operation.matrix.concurrency:
            self.run.meta_info[
                META_CONCURRENCY
            ] = self.compiled_operation.matrix.concurrency
        elif self.run.is_dag and self.compiled_operation.run.concurrency:
            self.run.meta_info[
                META_CONCURRENCY
            ] = self.compiled_operation.run.concurrency

        # Handle early stopping
        if self.run.is_matrix and self.compiled_operation.matrix.early_stopping:
            self.run.meta_info[META_HAS_EARLY_STOPPING] = True
        elif self.run.is_dag and self.compiled_operation.run.early_stopping:
            self.run.meta_info[META_HAS_EARLY_STOPPING] = True
        # handle services path
        if (
            self.compiled_operation.is_service_run
            and self.compiled_operation.run.rewrite_path
        ):
            self.run.meta_info[META_REWRITE_PATH] = True
        # handle services visibility
        if (
            self.compiled_operation.is_service_run
            and self.compiled_operation.run.is_external
        ):
            self.run.meta_info[META_IS_EXTERNAL] = True
        # handle services ports
        if self.compiled_operation.is_service_run and self.compiled_operation.run.ports:
            self.run.meta_info[META_PORTS] = self.compiled_operation.run.ports

    def _persist_resources(self):
        if self.compiled_operation.has_pipeline:
            return False
        resources = self.compiled_operation.run.get_resources()
        self.run.memory = resources.memory or 0
        self.run.cpu = resources.cpu or 0
        self.run.gpu = resources.gpu or 0
        self.run.custom = resources.custom or 0
        return True

    def _resolve_artifacts_lineage_state(self):
        self.artifacts = self.artifacts or []
        # Check upload and add it as a lineage
        if self.run.meta_info and META_UPLOAD_ARTIFACTS in self.run.meta_info:
            artifacts_path = self.run.meta_info[META_UPLOAD_ARTIFACTS]
            if artifacts_path:
                upload_artifact = collect_lineage_artifacts_path(artifacts_path)
                self.artifacts.append(upload_artifact)
        if self.artifacts:
            set_artifacts(self.run, self.artifacts)

    def _check_approval(self):
        if self.compiled_operation.is_approved is False and self.run.pending is None:
            self.run.pending = V1RunPending.APPROVAL
            return True
        return False

    def _persist_agent(self) -> bool:
        return False

    def resolve_state(self):
        self.run.state = get_run_state(
            cache=self.compiled_operation.cache,
            inputs=self.compiled_operation.inputs,
            outputs=self.compiled_operation.outputs,
            contexts=self.compiled_operation.contexts,
            init=self.compiled_operation.run.get_all_init(),
            connections=self.compiled_operation.run.get_all_connections(),
            containers=self.compiled_operation.run.get_all_containers(),
            namespace=self.project.uuid,
            component_state=self.run.component_state,
        )

    def persist_state(self):
        update_fields = [
            "content",
            "state",
            "inputs",
            "outputs",
            "meta_info",
        ]
        self._pre_persist_state()
        self._persist_meta_info()
        self._persist_resources()
        if self._persist_agent():
            update_fields += ["agent", "queue", "namespace", "artifacts_store"]
        if self._check_approval():
            update_fields.append("pending")
        if self.compiled_operation.cost:
            self.run.cost = self.compiled_operation.cost
            self.compiled_operation.cost = None
            update_fields.append("cost")
        if self._persist_resources():
            update_fields += ["memory", "cpu", "gpu", "custom"]

        self.run.content = self.compiled_operation.to_json()
        self.run.save(update_fields=update_fields)
        self._resolve_artifacts_lineage_state()

    @classmethod
    def _create_operation_dag(
        cls, run: BaseRun, compiled_operation: V1CompiledOperation
    ) -> BaseRun:
        run_config = compiled_operation.run  # type: V1Dag
        has_jobs = False
        has_services = False
        has_dags = False
        has_matrices = False
        has_schedules = False

        def get_upstream_op_params(op_dag_spec: DagOpSpec):
            if not op_dag_spec.upstream:
                return []
            upstream_op_params_by_names = ops_params.get_upstream_op_params_by_names(
                params=op_dag_spec.op.params
            )
            statuses_by_refs = op_dag_spec.op.get_upstream_statuses_events(
                op_dag_spec.upstream
            )
            for op_upstream in op_dag_spec.upstream:
                run_edge = Models.RunEdge(
                    upstream_id=runs_by_names[op_upstream].related_instance,
                    downstream_id=runs_by_names[op_name].related_instance,
                    kind=V1RunEdgeKind.DAG,
                    statuses=statuses_by_refs.get(op_upstream),
                )
                if op_upstream in upstream_op_params_by_names:
                    run_edge.values = {
                        param_spec.name: param_spec.param.value
                        for param_spec in upstream_op_params_by_names[op_upstream]
                    }

                yield run_edge

        def update_pipeline_params():
            # Resolve pipeline params
            pipeline_params = ops_params.get_dag_params_by_names(params=op_spec.params)
            if pipeline_params:
                pipeline_inputs = {i.name: i for i in (compiled_operation.inputs or {})}
                pipeline_contexts = {
                    i.name: i for i in (compiled_operation.contexts or {})
                }
                for pipeline_param in pipeline_params[ctx_refs.DAG_ENTITY_REF]:
                    param = pipeline_param.param
                    if pipeline_param.param.entity_value in pipeline_inputs:
                        io = pipeline_inputs[param.entity_value]
                        param = V1Param.construct(
                            value=io.value,
                            to_init=param.to_init or io.to_init,
                            connection=param.connection or io.connection,
                            context_only=param.context_only,
                        )
                    elif pipeline_param.param.entity_value in pipeline_contexts:
                        io = pipeline_contexts[pipeline_param.param.entity_value]
                        param = V1Param.construct(
                            value=io.value,
                            to_init=param.to_init or io.to_init,
                            connection=param.connection or io.connection,
                            context_only=param.context_only,
                        )
                    elif pipeline_param.param.entity_type == ctx_sections.GLOBALS:
                        # handles uid, uuid, and id
                        if pipeline_param.param.entity_value in ctx_keys.UUID:
                            param = V1Param.construct(
                                value=run.uuid.hex,
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.NAME:
                            param = V1Param.construct(
                                value=run.name,
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.STATUS:
                            param = V1Param.construct(
                                value=run.status,
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.CONDITION:
                            param = V1Param.construct(
                                value=run.get_last_condition(),
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.OWNER_NAME:
                            param = V1Param.construct(
                                value=run.project.owner.name,
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.PROJECT_UUID:
                            param = V1Param.construct(
                                value=run.project.uuid.hex,
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.PROJECT_NAME:
                            param = V1Param.construct(
                                value=run.project.name,
                                context_only=param.context_only,
                            )
                        elif (
                            pipeline_param.param.entity_value
                            == ctx_keys.PROJECT_UNIQUE_NAME
                        ):
                            param = V1Param.construct(
                                value=get_project_instance(
                                    run.project.owner.name, run.project.name
                                ),
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.RUN_INFO:
                            param = V1Param.construct(
                                value=get_run_instance(
                                    run.project.owner.name,
                                    run.project.name,
                                    run.uuid.hex,
                                ),
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.CONTEXT_PATH:
                            param = V1Param.construct(
                                value=ctx_paths.CONTEXT_ROOT,
                                context_only=param.context_only,
                            )
                        elif (
                            pipeline_param.param.entity_value == ctx_keys.ARTIFACTS_PATH
                        ):
                            param = V1Param.construct(
                                value=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
                                context_only=param.context_only,
                            )
                        elif (
                            pipeline_param.param.entity_value
                            == ctx_keys.RUN_ARTIFACTS_PATH
                        ):
                            param = V1Param.construct(
                                value=ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(
                                    run.uuid.hex
                                ),
                                context_only=param.context_only,
                            )
                        elif (
                            pipeline_param.param.entity_value
                            == ctx_keys.RUN_OUTPUTS_PATH
                        ):
                            param = V1Param.construct(
                                value=ctx_paths.CONTEXT_MOUNT_RUN_OUTPUTS_FORMAT.format(
                                    run.uuid.hex
                                ),
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.CREATED_AT:
                            param = V1Param.construct(
                                value=run.created_at,
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.SCHEDULE_AT:
                            param = V1Param.construct(
                                value=run.schedule_at,
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.STARTED_AT:
                            param = V1Param.construct(
                                value=run.started_at,
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.FINISHED_AT:
                            param = V1Param.construct(
                                value=run.finished_at,
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.DURATION:
                            param = V1Param.construct(
                                value=run.duration,
                                context_only=param.context_only,
                            )
                        elif pipeline_param.param.entity_value == ctx_keys.CLONING_KIND:
                            param = V1Param.construct(
                                value=run.cloning_kind,
                                context_only=param.context_only,
                            )

                    else:
                        param = None
                    if param:
                        op_spec.params[pipeline_param.name] = param

        hub_refs_to_components = cls._collect_hub_refs(
            ops=run_config.operations, owner_name=run.project.owner.name
        )
        topological_sort = run_config.sort_topologically()
        # We create ops for each stage
        runs_by_names = {}
        tags_by_names = {}
        pipeline_override = {"patchStrategy": PatchStrategy.PRE_MERGE}
        if compiled_operation.cache:
            pipeline_override["cache"] = compiled_operation.cache.to_dict()
        if run_config.environment:
            pipeline_override["runPatch"] = {}
            pipeline_override["runPatch"][
                "environment"
            ] = run_config.environment.to_dict()
        if compiled_operation.termination:
            pipeline_override["termination"] = compiled_operation.termination.to_dict()
        if compiled_operation.plugins:
            pipeline_override["plugins"] = compiled_operation.plugins.to_dict()
        if compiled_operation.queue:
            pipeline_override["queue"] = compiled_operation.queue
        for stage in topological_sort:
            for op_name in stage:
                component_state = None
                if op_name in run_config.dag:
                    op_spec = run_config.dag[op_name]
                    if (
                        not op_spec.op.has_component_reference
                        and op_spec.op.has_hub_reference
                        and op_spec.op.hub_ref in hub_refs_to_components
                    ):
                        op_spec.op.set_definition(
                            hub_refs_to_components[op_spec.op.hub_ref][
                                "component_content"
                            ]
                        )
                        component_state = hub_refs_to_components[op_spec.op.hub_ref][
                            "component_state"
                        ]
                run_config.set_op_component(op_name)
                op_spec = run_config.get_op_spec_by_name(op_name)
                update_pipeline_params()
                meta_info = cls._pass_down_uploaded_artifacts(run=run)
                runs_by_names[op_name] = operations.init_run(
                    project_id=run.project_id,
                    user_id=run.user_id,
                    pipeline_id=run.id,
                    op_spec=op_spec,
                    controller_id=run.controller_id or run.id,
                    managed_by=run.managed_by,
                    override=pipeline_override,
                    supported_owners={run.project.owner.name},
                    component_state=component_state,
                    meta_info=meta_info,
                )
                cls._set_pipeline_run_pending_logic(
                    current_run=runs_by_names[op_name].instance, parent_run=run
                )

                # Add events trigger flags
                if run_config.dag[op_spec.name].downstream:
                    for downstream_op in run_config.dag[op_spec.name].downstream:
                        if run_config.dag[downstream_op].op.has_events_for_upstream(
                            op_spec.name
                        ):
                            runs_by_names[op_name].instance.meta_info[
                                META_HAS_DOWNSTREAM_EVENTS_TRIGGER
                            ] = True
                            break

                # Add meta information
                if not has_jobs and runs_by_names[op_name].instance.is_job:
                    has_jobs = True
                if not has_services and runs_by_names[op_name].instance.is_service:
                    has_services = True
                if not has_dags and runs_by_names[op_name].instance.is_dag:
                    has_dags = True
                if not has_matrices and runs_by_names[op_name].instance.is_matrix:
                    has_matrices = True
                if not has_schedules and runs_by_names[op_name].instance.is_schedule:
                    has_schedules = True

                # Setting tags by op names
                tags = op_spec.tags or op_spec.definition.tags
                if tags:
                    tags_by_names[op_name] = tags

        # Create batch runs
        runs = Models.Run.objects.bulk_create(
            [runs_by_names[op_name].instance for op_name in runs_by_names]
        )
        # Extend tuple by run ids
        for pipeline_run in runs:
            runs_by_names[pipeline_run.name] = runs_by_names[pipeline_run.name].update(
                related_instance=pipeline_run.id,
            )

        run_edges = []
        for op_name in run_config.dag:
            run_edges.extend(get_upstream_op_params(run_config.dag[op_name]))

        if run_edges:
            Models.RunEdge.objects.bulk_create(run_edges)

        # Add meta to pipeline
        if has_jobs:
            run.meta_info[META_HAS_JOBS] = has_jobs
        if has_services:
            run.meta_info[META_HAS_SERVICES] = has_services
        if has_dags:
            run.meta_info[META_HAS_DAGS] = has_dags
        if has_matrices:
            run.meta_info[META_HAS_MATRICES] = has_matrices
        if has_schedules:
            run.meta_info[META_HAS_SCHEDULES] = has_schedules

        return run

    @staticmethod
    def _normalize_cron(cron: str) -> str:
        cron_presets = {
            "@hourly": "0 * * * *",
            "@daily": "0 0 * * *",
            "@weekly": "0 0 * * 0",
            "@monthly": "0 0 1 * *",
            "@quarterly": "0 0 1 */3 *",
            "@yearly": "0 0 1 1 *",
        }

        return cron_presets.get(cron, cron)

    @staticmethod
    def _is_schedule_done(
        num_runs: int,
        compiled_operation: V1CompiledOperation,
    ) -> bool:
        if (
            compiled_operation.schedule.max_runs
            and num_runs >= compiled_operation.schedule.max_runs
        ):
            return True
        if not compiled_operation.schedule.end_at:
            return False
        return now() >= compiled_operation.schedule.end_at

    @staticmethod
    def _get_next_from_interval(
        frequency: timedelta, start_at: datetime, last_start_at: datetime
    ) -> datetime:
        num_skips = 0
        if last_start_at:
            num_skips = (
                last_start_at - start_at
            ).total_seconds() / frequency.total_seconds()

        # if the last_start_at date is before the start date, we jump to the start date
        if num_skips < 0:
            num_skips = 0
        # if the `last_start_at` date falls exactly on an interval, jump to the next interval
        elif int(num_skips) == num_skips:
            num_skips += 1
        # otherwise jump to the next integer interval
        else:
            num_skips = int(num_skips + 1)

        interval = frequency * num_skips

        return start_at + interval

    @classmethod
    def _get_next_from_cron(
        cls, cron: str, start_at: datetime, last_start_at: datetime
    ) -> datetime:
        cron = cls._normalize_cron(cron)
        cron = croniter(cron, last_start_at or start_at)
        return cron.get_next(datetime)

    @classmethod
    def _get_next(
        cls, num_runs: int, run: BaseRun, compiled_operation: V1CompiledOperation
    ) -> datetime:
        if compiled_operation.has_datetime_schedule:
            return compiled_operation.schedule.start_at

        start_at = compiled_operation.schedule.start_at
        if num_runs == 0 and start_at:
            return start_at

        start_at = compiled_operation.schedule.start_at or run.created_at
        last_start_at = None
        if num_runs > 0:
            last_run = (
                run.pipeline_runs.order_by("created_at")
                .only("id", "schedule_at")
                .last()
            )
            if last_run and last_run.schedule_at:
                last_start_at = last_run.schedule_at
            else:
                last_start_at = now()
        if compiled_operation.has_interval_schedule:
            return cls._get_next_from_interval(
                frequency=compiled_operation.schedule.frequency,
                start_at=start_at,
                last_start_at=last_start_at,
            )
        elif compiled_operation.has_cron_schedule:
            return cls._get_next_from_cron(
                cron=compiled_operation.schedule.cron,
                start_at=start_at,
                last_start_at=last_start_at,
            )
        else:
            raise ValueError(
                "I should not be here, schedule not handled {}".format(
                    compiled_operation.schedule.kind
                )
            )

    @classmethod
    def _create_operation_schedule(
        cls,
        run: BaseRun,
        compiled_operation: V1CompiledOperation,
    ) -> bool:
        num_runs = run.pipeline_runs.count()
        success_condition = V1StatusCondition.get_condition(
            type=V1Statuses.SUCCEEDED,
            status="True",
            reason="PolyaxonScheduleFinished",
            message="Schedule finished.",
        )
        if cls._is_schedule_done(
            compiled_operation=compiled_operation, num_runs=num_runs
        ):
            new_run_status(run=run, condition=success_condition)
            return False

        start_at = cls._get_next(
            num_runs=num_runs, run=run, compiled_operation=compiled_operation
        )
        if (
            compiled_operation.schedule.end_at
            and start_at > compiled_operation.schedule.end_at
        ):
            new_run_status(run=run, condition=success_condition)
            return False

        op_spec = get_op_from_schedule(
            content=run.raw_content,
            compiled_operation=compiled_operation,
        )
        meta_info = cls._pass_down_uploaded_artifacts(run=run)
        schedule_run = operations.init_run(
            project_id=run.project_id,
            user_id=run.user_id,
            pipeline_id=run.id,
            name=run.name,
            description=run.description,
            tags=run.tags,
            readme=run.readme,
            managed_by=run.managed_by,
            op_spec=op_spec,
            schedule_at=start_at,
            supported_owners={run.project.owner.name},
            component_state=run.component_state,
            meta_info=meta_info,
        ).instance
        cls._set_pipeline_run_pending_logic(current_run=schedule_run, parent_run=run)
        # Create batch runs to avoid sending any signal yet
        Models.Run.objects.bulk_create([schedule_run])
        return True

    @staticmethod
    def _pass_down_uploaded_artifacts(run: BaseRun):
        run = run.controller if run.controller_id else run
        meta_info = {}
        if META_UPLOAD_ARTIFACTS in run.meta_info:
            meta_info[META_COPY_ARTIFACTS] = V1ArtifactsType(
                dirs=[run.uuid.hex]
            ).to_dict()
            meta_info[META_UPLOAD_ARTIFACTS] = run.meta_info[META_UPLOAD_ARTIFACTS]
        return meta_info

    @staticmethod
    def _set_pipeline_run_pending_logic(current_run: BaseRun, parent_run: BaseRun):
        # Add approval for manually managed runs in pipelines
        if current_run.pending is None and parent_run.managed_by == ManagedBy.CLI:
            current_run.pending = V1RunPending.APPROVAL

    @classmethod
    def _get_runs_from_ops(
        cls,
        run: BaseRun,
        compiled_operation: V1CompiledOperation,
        suggestions: List[Dict],
        iteration: Optional[int] = None,
    ) -> List[BaseRun]:
        ops = get_ops_from_suggestions(
            content=run.raw_content,
            compiled_operation=compiled_operation,
            suggestions=suggestions,
        )

        date_now = now()
        meta_info = cls._pass_down_uploaded_artifacts(run=run)
        component_state = None
        for op_spec in ops:
            # We make sure that the component state resolves to the correct runs' state
            # Calculate this value once
            if not component_state:
                component_state = get_component_version_state(op_spec.component)
            op_run = operations.init_run(
                project_id=run.project_id,
                user_id=run.user_id,
                pipeline_id=run.id,
                name=run.name,
                description=run.description,
                tags=run.tags,
                readme=run.readme,
                managed_by=run.managed_by,
                op_spec=op_spec,
                controller_id=run.controller_id or run.id,
                iteration=iteration,
                supported_owners={run.project.owner.name},
                component_state=component_state,
                meta_info=meta_info,
            ).instance
            op_run.uuid = uuid.uuid4().hex
            op_run.created_at = date_now
            op_run.updated_at = date_now
            cls._set_pipeline_run_pending_logic(current_run=op_run, parent_run=run)
            yield op_run

    @classmethod
    def _create_mapping_matrix(
        cls, run: BaseRun, compiled_operation: V1CompiledOperation
    ):
        suggestions = MappingManager(compiled_operation.matrix).get_suggestions()
        runs = cls._get_runs_from_ops(
            run=run, compiled_operation=compiled_operation, suggestions=suggestions
        )
        # Create batch runs
        bulk_create_runs(runs)

    @classmethod
    def _create_grid_matrix(cls, run: BaseRun, compiled_operation: V1CompiledOperation):
        suggestions = GridSearchManager(compiled_operation.matrix).get_suggestions()
        runs = cls._get_runs_from_ops(
            run=run, compiled_operation=compiled_operation, suggestions=suggestions
        )
        # Create batch runs
        bulk_create_runs(runs)

    @classmethod
    def _create_random_matrix(
        cls, run: BaseRun, compiled_operation: V1CompiledOperation
    ):
        suggestions = RandomSearchManager(compiled_operation.matrix).get_suggestions()
        runs = cls._get_runs_from_ops(
            run=run, compiled_operation=compiled_operation, suggestions=suggestions
        )
        # Create batch runs
        bulk_create_runs(runs)

    @classmethod
    def _create_operation_matrix(
        cls, run: BaseRun, compiled_operation: V1CompiledOperation
    ) -> None:
        if compiled_operation.has_random_search_matrix:
            cls._create_random_matrix(run=run, compiled_operation=compiled_operation)
        elif compiled_operation.has_grid_search_matrix:
            cls._create_grid_matrix(run=run, compiled_operation=compiled_operation)
        elif compiled_operation.has_mapping_matrix:
            cls._create_mapping_matrix(run=run, compiled_operation=compiled_operation)

    @staticmethod
    def _get_pipeline_join(
        pipeline: str,
        metric: V1OptimizationMetric,
        limit: int = 1000,
        additional_filters: Optional[str] = None,
    ):
        query = "pipeline:{}, metrics.{}:~nil, status: {}".format(
            pipeline, metric.name, V1Statuses.SUCCEEDED
        )
        if additional_filters:
            query = "{}, {}".format(query, additional_filters)

        return V1Join.construct(
            query=query,
            sort=metric.get_for_sort(),
            limit=limit,
            params={
                "configs": V1JoinParam.construct(value="inputs"),
                "metrics": V1JoinParam.construct(
                    value="outputs.{}".format(metric.name)
                ),
            },
        )

    @classmethod
    def _create_iteration_matrix(
        cls,
        run: BaseRun,
        suggestions: List[Dict],
        iteration: int,
        compiled_operation: V1CompiledOperation,
    ) -> Optional[List[int]]:
        runs = cls._get_runs_from_ops(
            run=run,
            compiled_operation=compiled_operation,
            suggestions=suggestions,
            iteration=iteration,
        )
        # Create batch runs
        if runs:
            runs = Models.Run.objects.bulk_create(runs)
            return [r.id for r in runs]
        else:
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.SUCCEEDED,
                status="True",
                reason="SchedulerEmptySuggestions",
                message="Iteration algorithm received an empty suggestion list.",
            )
            new_run_status(run=run, condition=condition)
            return False

    def _apply_pipeline_contexts(self):
        if self.compiled_operation.schedule:
            self._create_operation_schedule(
                run=self.run, compiled_operation=self.compiled_operation
            )
        elif self.compiled_operation.matrix:
            self._create_operation_matrix(
                run=self.run, compiled_operation=self.compiled_operation
            )
        elif self.compiled_operation.is_dag_run:
            self.run = self._create_operation_dag(
                run=self.run, compiled_operation=self.compiled_operation
            )
        return self.compiled_operation

    @staticmethod
    def _get_cache_query(
        run, filters: Optional[Dict] = None, excludes: Optional[Dict] = None
    ):
        queryset = Models.Run.objects.filter(
            state=run.state, kind=run.kind, runtime=run.runtime
        ).exclude(id=run.id)
        if filters:
            queryset = queryset.filter(**filters)
        if excludes:
            queryset = queryset.exclude(**excludes)

        return queryset.order_by("created_at").only("id", "original").last()

    @classmethod
    def _is_cache_hit(
        cls, run: BaseRun, compiled_operation: V1CompiledOperation
    ) -> bool:
        # Check if the run was approved to be scheduled
        if run.original_id and run.cloning_kind == V1CloningKind.CACHE:
            run.cloning_kind = None
            run.original_id = None
            run.pending = None
            run.save(
                update_fields=["original_id", "cloning_kind", "updated_at", "pending"]
            )
            return False
        if compiled_operation.cache and compiled_operation.cache.disable:
            return False

        if not compiled_operation.cache or compiled_operation.cache.disable is None:
            # Cache is disabled by default for independent ops
            if not run.pipeline_id:
                return False
            # Cache is disabled by default for schedules
            if run.is_schedule:
                return False
        # Cache is disabled by default for cloned ops
        if run.original_id:
            return False
        # User did not define a state to check
        if not run.state:
            return False

        cached = cls._get_cache_query(
            run,
            filters={
                "status__in": {
                    V1Statuses.PROCESSING,
                    V1Statuses.SCHEDULED,
                    V1Statuses.STARTING,
                    V1Statuses.RUNNING,
                    V1Statuses.SUCCEEDED,
                }
            },
        )

        # Not cached check all runs from the same queue
        if not cached:
            cached = cls._get_cache_query(
                run,
                excludes={
                    "status__in": {
                        V1Statuses.FAILED,
                        V1Statuses.SKIPPED,
                        V1Statuses.UPSTREAM_FAILED,
                        V1Statuses.STOPPED,
                    }
                },
            )

        # No cache found
        if not cached:
            return False

        # Check if cache has expired
        cached = cached.original if cached.original else cached
        if (
            compiled_operation.cache
            and compiled_operation.cache.ttl is not None
            and cached.finished_at
        ):
            if (
                now() - cached.finished_at
            ).total_seconds() >= compiled_operation.cache.ttl:
                return False

        # Check if cache has a stopping triggered
        if LifeCycle.is_stopping(cached.status):
            return False

        # Cache finished but not successfully
        if LifeCycle.is_done(cached.status) and not LifeCycle.succeeded(cached.status):
            return False

        # Use cache
        run.original_id = cached.id
        run.cloning_kind = V1CloningKind.CACHE
        if LifeCycle.succeeded(cached.status):
            run.outputs = cached.outputs
            condition = V1StatusCondition.get_condition(
                type=V1Statuses.SUCCEEDED,
                status="True",
                reason="CacheHit",
                message="Run is using cached results",
            )
            new_run_status(
                run=run,
                condition=condition,
                additional_fields=["original_id", "cloning_kind", "outputs"],
            )
        else:
            run.pending = V1RunPending.CACHE
            run.save(
                update_fields=["original_id", "cloning_kind", "updated_at", "pending"]
            )
        return True

    @staticmethod
    def _validation_conditions(
        run: BaseRun,
        conditions: Any = None,
    ) -> bool:
        if conditions is None:
            return True

        try:
            conditions = to_bool(conditions)
        except Exception as e:
            raise PolyaxonCompilerError(
                "Received a wrong expression for the key: conditions. "
                "The expression could be evaluated to a boolean value. "
                "Condition: {}. Error: {}".format(conditions, e)
            )

        if conditions:
            return True

        condition = V1StatusCondition.get_condition(
            type=V1Statuses.SKIPPED,
            status="True",
            reason="ConditionsCheckFailed",
            message="The 'conditions' field was evaluated to False.",
        )
        new_run_status(run=run, condition=condition)
        return False

    @staticmethod
    def _validation_hook_conditions(
        hook_index: int,
        conditions: Any = None,
    ) -> bool:
        if conditions is None:
            return True

        try:
            conditions = to_bool(conditions)
        except Exception as e:
            raise PolyaxonCompilerError(
                "Hook `{}` received a wrong expression for the key: conditions. "
                "The expression could be evaluated to a boolean value. "
                "Condition: {}. Error: {}".format(hook_index, conditions, e)
            )

        return conditions

    def _should_skip_runtime_resolution(self):
        # Check conditions
        if not self._validation_conditions(
            run=self.run, conditions=self.compiled_operation.conditions
        ):
            return True
        # Check cache
        return self._is_cache_hit(
            run=self.run, compiled_operation=self.compiled_operation
        )

    def _get_project_version_refs(
        self,
        names: Union[List[str], Set[str]],
        kind: V1ProjectVersionKind,
    ) -> List[BaseProjectVersion]:
        names = set(names)
        entities = []
        query = []
        for name in names:
            try:
                owner, entity_namespace, version = get_versioned_entity_info(
                    entity=name,
                    entity_name="{} version".format(kind),
                    default_owner=self.owner_name,
                )
                entities.append((owner, entity_namespace, version))
                query.append(
                    Q(
                        project__owner__name=owner,
                        project__name=entity_namespace,
                        name=version,
                    )
                    if settings.HAS_ORG_MANAGEMENT
                    else Q(
                        project__name=entity_namespace,
                        name=version,
                    )
                )
            except Exception as e:
                raise AccessNotFound(
                    "A {} version reference was provided "
                    "but could not be parsed correctly: `{}`. "
                    "Error: {}".format(kind, name, e)
                )
        versions = Models.ProjectVersion.objects.filter(kind=kind)
        if settings.HAS_ORG_MANAGEMENT:
            versions = versions.filter(project__owner__name=self.owner_name)
        versions = versions.filter(reduce(or_, query))
        additional_fields = ()
        if settings.HAS_ORG_MANAGEMENT:
            versions.select_related("connection")
            additional_fields = (
                "connection_id",
                "connection__name",
            )
        versions = (
            versions.prefetch_related("lineage", "lineage__artifact")
            .annotate(lineage_count=Count("lineage"))
            .filter(lineage_count__gt=0)
        )
        versions = versions.only(
            "id",
            "project_id",
            "lineage__id",
            "lineage__artifact__id",
            "lineage__artifact__name",
            "lineage__artifact__path",
            "lineage__artifact__kind",
            "run_id",
            "run__uuid",
            *additional_fields,
        )
        ids = {v.id for v in versions}
        # connection_ids = {v.connection_id for v in versions}
        # project_ids = {
        #     v.project_id for v in versions if v.project_id != project_settings.id
        # }
        if len(ids) != len(names):
            raise AccessNotFound(
                "Some {} version refs were provided "
                "but were not found: `{}`".format(kind, names)
            )

        # if (
        #     project_ids
        #     and project_settings
        #     and project_settings.projects.exists()
        #     and project_settings.projects.filter(id__in=project_ids).count()
        #     != len(project_ids)
        # ):
        #     raise AccessNotAuthorized(
        #         "Some {} versions were provided but are not authorised on this project.".format(
        #             kind
        #         )
        #     )
        # if (
        #     connection_ids
        #     and project_settings
        #     and project_settings.connections.exists()
        #     and project_settings.connections.filter(id__in=connection_ids).count()
        #     != len(connection_ids)
        # ):
        #     raise AccessNotAuthorized(
        #         "Some {} versions were provided but they are stored on connections not authorised on this project.".format(
        #             kind
        #         )
        #     )
        return versions

    def _get_project_version_paths(
        self,
        version_names: Set[str],
        kind: V1ProjectVersionKind,
    ) -> Tuple[List[V1Init], Set[str]]:
        refs = self._get_project_version_refs(
            names=version_names,
            kind=kind,
        )

        init = []
        connections = set([])
        for r in refs:
            connection_name = r.connection.name if getattr(r, "connection_id") else None
            if connection_name:
                connections.add(connection_name)
            paths = get_run_lineage_paths(
                r.run.uuid.hex,
                r.lineage.values_list("artifact__path", flat=True),
            )
            if paths:
                init.append(
                    V1Init.construct(
                        connection=connection_name,
                        paths=paths,
                    )
                )
        return init, connections

    def _get_run_refs(
        self,
        names: Union[List[str], Set[str]],
    ) -> List[List[str]]:
        names = set(names)
        entities = []
        query = []
        lineages_by_run = {}
        for name in names:
            try:
                owner, entity_namespace, lineage = get_versioned_entity_info(
                    entity=name,
                    entity_name="lineage",
                    default_owner=self.owner_name,
                )
                entities.append((owner, entity_namespace, lineage))
                if entity_namespace not in lineages_by_run:
                    lineages_by_run[entity_namespace] = []
                lineages_by_run[entity_namespace].append(lineage)
                query.append(
                    Q(
                        project__owner__name=owner,
                        uuid=entity_namespace,
                    )
                    if settings.HAS_ORG_MANAGEMENT
                    else Q(uuid=entity_namespace)
                )
            except Exception as e:
                raise AccessNotFound(
                    "A lineage reference was provided "
                    "but could not be parsed correctly: `{}`. "
                    "Error: {}".format(name, e)
                )
        runs = Models.Run.objects
        if settings.HAS_ORG_MANAGEMENT:
            runs = runs.filter(project__owner__name=self.owner_name)
        runs = (
            runs.filter(reduce(or_, query))
            .prefetch_related("artifacts")
            .annotate(artifacts_count=Count("artifacts"))
            .filter(artifacts_count__gt=0)
        )
        runs = runs.only(
            "id",
            "uuid",
            "project_id",
            "artifacts__id",
            "artifacts__name",
            "artifacts__path",
            "artifacts__kind",
        )
        ids = {v.id for v in runs}
        # connection_ids = {v.connection_id for v in versions}
        # project_ids = {
        #     v.project_id for v in versions if v.project_id != project_settings.id
        # }
        lineage_runs = list(lineages_by_run.keys())
        if len(ids) != len(lineage_runs):
            raise AccessNotFound(
                "Some lineage refs were provided but were not found. "
                "Please check that the runs `{}` exist and are available".format(
                    lineage_runs
                )
            )

        # if (
        #     project_ids
        #     and project_settings
        #     and project_settings.projects.exists()
        #     and project_settings.projects.filter(id__in=project_ids).count()
        #     != len(project_ids)
        # ):
        #     raise AccessNotAuthorized(
        #         "Some {} versions were provided but are not authorised on this project.".format(
        #             kind
        #         )
        #     )
        # if (
        #     connection_ids
        #     and project_settings
        #     and project_settings.connections.exists()
        #     and project_settings.connections.filter(id__in=connection_ids).count()
        #     != len(connection_ids)
        # ):
        #     raise AccessNotAuthorized(
        #         "Some {} versions were provided but they are stored on connections not authorised on this project.".format(
        #             kind
        #         )
        #     )
        return [
            get_run_lineage_paths(
                r.uuid.hex,
                r.artifacts.filter(name__in=lineages_by_run[r.uuid.hex]).values_list(
                    "path", flat=True
                ),
            )
            for r in runs
        ]

    def _get_lineage_init_paths(self) -> Tuple[List[V1Init], Set[str]]:
        lineage_names = CompiledOperationSpecification.get_init_lineage_refs(
            config=self.compiled_operation,
        )
        if not lineage_names:
            return [], set([])

        refs = self._get_run_refs(names=lineage_names)

        init = []
        connections = set([])
        for r in refs:
            # connection_name = r.connection.name if r.connection_id else None
            # if connection_name:
            #     connections.add(connection_name)
            if r:
                init.append(
                    V1Init.construct(
                        # connection=connection_name,
                        paths=r,
                    )
                )
        return init, connections

    def _get_model_version_paths(
        self,
    ) -> Tuple[List[V1Init], Set[str]]:
        version_names = CompiledOperationSpecification.get_init_model_refs(
            config=self.compiled_operation,
        )
        if not version_names:
            return [], set([])

        return self._get_project_version_paths(
            version_names=version_names,
            kind=V1ProjectVersionKind.MODEL,
        )

    def _get_artifact_version_paths(self) -> Tuple[List[V1Init], Set[str]]:
        version_names = CompiledOperationSpecification.get_init_artifact_refs(
            config=self.compiled_operation,
        )
        if not version_names:
            return [], set([])

        return self._get_project_version_paths(
            version_names=version_names,
            kind=V1ProjectVersionKind.ARTIFACT,
        )

    def resolve_init_refs(self):
        m_init, _ = self._get_model_version_paths()
        a_init, _ = self._get_artifact_version_paths()
        l_init, _ = self._get_lineage_init_paths()
        init = m_init + a_init + l_init
        if not init:
            return
        init = [i.to_dict() for i in init]
        model_preset = {"runPatch": {"init": init}}

        self.compiled_operation = CompiledOperationSpecification.apply_preset(
            config=self.compiled_operation, preset=model_preset
        )

    def clean_init_refs(self):
        self.compiled_operation = (
            CompiledOperationSpecification.clean_init_version_refs(
                self.compiled_operation
            )
        )

    def resolve_build(self):
        if not self.compiled_operation.build:
            return

        inputs = {i.name: i.value for i in self.compiled_operation.inputs or {}}
        build_instance = operations.resolve_build(
            project_id=self.run.project_id,
            user_id=self.run.user_id,
            compiled_operation=self.compiled_operation,
            inputs=inputs,
            meta_info=None,
            pending=None,
            supported_owners={self.owner_name},
        )
        # Change the pending logic to wait for the build
        self.compiled_operation.build = None
        self.run.pending = V1RunPending.BUILD
        self.run.content = self.compiled_operation.to_json()
        self.run.save(update_fields=["content", "updated_at", "pending"])

        operations.save_build_relation(
            operations.OperationInitSpec(
                compiled_operation=None,
                instance=self.run,
                related_instance=build_instance,
            )
        )
        return self.compiled_operation

    def apply_hooks_contexts(self):
        contexts = self._resolve_contexts()
        return CompiledOperationSpecification.apply_hooks_contexts(
            self.compiled_operation, contexts=contexts
        )

    def resolve_hooks(self) -> List[V1Operation]:
        self.resolve_agent_environment()
        hooks = self.apply_hooks_contexts()
        ops = []
        contexts = dict(
            name=self.run.name,
            uuid=self.run.uuid.hex,
            kind=self.run.kind,
            status=self.run.status,
            runtime=self.run.runtime,
            wait_time=self.run.wait_time,
            duration=self.run.duration,
            inputs=self.run.inputs,
            outputs=self.run.outputs,
            condition=self.run.get_last_condition(),
        )
        for i, hook in enumerate(hooks):
            if hook.check_trigger_for_status(
                status=self.run.status
            ) and self._validation_hook_conditions(
                hook_index=i, conditions=hook.conditions
            ):
                ops.append(
                    V1Operation.from_hook(
                        hook,
                        contexts=contexts,
                    ),
                )
        return ops
