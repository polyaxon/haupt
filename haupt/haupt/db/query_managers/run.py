from collections import namedtuple

from django.conf import settings

from haupt.common.apis.filters import OrderingFilter, QueryFilter
from haupt.db.query_managers import callback_conditions
from haupt.db.query_managers.manager import BaseQueryManager
from polyaxon._pql.builder import (
    ArrayCondition,
    BoolCondition,
    CallbackCondition,
    ComparisonCondition,
    DateTimeCondition,
    KeysCondition,
    SearchCondition,
    ValueCondition,
)
from polyaxon._pql.parser import (
    parse_cpu_operation,
    parse_datetime_operation,
    parse_memory_operation,
    parse_scalar_operation,
    parse_search_operation,
    parse_value_operation,
)
from polyaxon.schemas import V1Join


class RunQueryManager(BaseQueryManager):
    NAME = "run"
    FIELDS_USE_NAME = {
        "project",
        "agent",
        "queue",
        "artifacts_store",
        "connections",
    }
    FIELDS_USE_STATE = {"artifacts"}
    FIELDS_USE_UUID = {
        "original",
        "upstream",
        "downstream",
        "pipeline",
        "controller",
        "upstream_runs",
        "downstream_runs",
    }
    FIELDS_PROXY = {
        "params": "inputs",
        "in": "inputs",
        "out": "outputs",
        "metrics": "outputs",
        "meta_values": "meta_info",
        "meta_flags": "meta_info",
        "id": "uuid",
        "uid": "uuid",
        "upstream": "upstream_runs",
        "downstream": "downstream_runs",
        "user": "user__username",
        "teams": "project__teams__name",
    }
    FIELDS_DISTINCT = {
        "artifacts",
        "connections",
    }
    FIELDS_ORDERING = (
        "created_at",
        "updated_at",
        "started_at",
        "finished_at",
        "schedule_at",
        "name",
        "kind",
        "namespace",
        "runtime",
        "user",
        "uuid",
        "duration",
        "wait_time",
        "status",
        "cost",
        "cpu",
        "memory",
        "gpu",
        "custom",
        "state",
        "component_state",
    )
    FIELDS_ORDERING_PROXY = {
        "metrics": {"field": "outputs", "annotate": True},
        "params": {"field": "inputs", "annotate": True},
        "inputs": {"field": "inputs", "annotate": True},
        "in": {"field": "inputs", "annotate": True},
        "outputs": {"field": "outputs", "annotate": True},
        "out": {"field": "outputs", "annotate": True},
        "meta_flags": {"field": "meta_info", "annotate": True},
        "meta_info": {"field": "meta_info", "annotate": True},
        "meta_values": {"field": "meta_info", "annotate": True},
    }
    FIELDS_DEFAULT_ORDERING = ("-updated_at",)
    CHECK_ALIVE = True
    DEFAULT_FILTERS = {"created_at": "last_month"}
    PARSERS_BY_FIELD = {
        # Uuid
        "id": parse_search_operation,
        "uid": parse_search_operation,
        "uuid": parse_search_operation,
        # Dates
        "created_at": parse_datetime_operation,
        "updated_at": parse_datetime_operation,
        "started_at": parse_datetime_operation,
        "finished_at": parse_datetime_operation,
        "schedule_at": parse_datetime_operation,
        # Name
        "name": parse_search_operation,
        # Description
        "description": parse_search_operation,
        # User
        "user": parse_value_operation,
        # Status
        "status": parse_value_operation,
        # Project
        "project": parse_value_operation,
        # Original
        "original": parse_value_operation,
        # Pipeline
        "pipeline": parse_value_operation,
        # Controller
        "controller": parse_value_operation,
        # Upstream
        "upstream": parse_value_operation,
        # Downstream
        "downstream": parse_value_operation,
        # Cloning kind
        "cloning_kind": parse_value_operation,
        # Artifact
        "in_artifact_kind": parse_value_operation,
        "out_artifact_kind": parse_value_operation,
        # Backend
        "backend": parse_value_operation,
        # Framework
        "framework": parse_value_operation,
        # Commit
        "commit": parse_value_operation,
        # Kind
        "kind": parse_value_operation,
        # Meta Kind
        "runtime": parse_value_operation,
        # Namespace
        "namespace": parse_value_operation,
        # Params
        "params": parse_value_operation,
        "inputs": parse_value_operation,
        "in": parse_value_operation,
        # Results
        "outputs": parse_value_operation,
        "out": parse_value_operation,
        # Metrics
        "metrics": parse_scalar_operation,
        # Meta
        "meta_flags": parse_value_operation,
        "meta_info": parse_value_operation,
        "meta_values": parse_scalar_operation,
        # Tags
        "tags": parse_value_operation,
        # Live state
        "live_state": parse_value_operation,
        # Duration
        "duration": parse_scalar_operation,
        # Wait time
        "wait_time": parse_scalar_operation,
        # Agent
        "agent": parse_value_operation,
        "queue": parse_value_operation,
        # Artifacts store
        "artifacts_store": parse_value_operation,
        # States
        "state": parse_value_operation,
        "component_state": parse_value_operation,
        # Flags
        "is_managed": parse_value_operation,
        "managed_by": parse_value_operation,
        "pending": parse_value_operation,
        # Resources
        "cost": parse_scalar_operation,
        "cpu": parse_cpu_operation,
        "memory": parse_memory_operation,
        "gpu": parse_scalar_operation,
        "custom": parse_scalar_operation,
        # Artifacts
        "artifacts": parse_value_operation,
        # Connections
        "connections": parse_value_operation,
        # Teams
        "teams": parse_value_operation,
        # My runs
        "mine": parse_value_operation,
    }
    CONDITIONS_BY_FIELD = {
        # Uuid
        "id": SearchCondition,
        "uid": SearchCondition,
        "uuid": SearchCondition,
        # Dates
        "created_at": DateTimeCondition,
        "updated_at": DateTimeCondition,
        "started_at": DateTimeCondition,
        "finished_at": DateTimeCondition,
        "schedule_at": DateTimeCondition,
        # Name
        "name": SearchCondition,
        # Description
        "description": SearchCondition,
        # User
        "user": ValueCondition,
        # Status
        "status": ValueCondition,
        # Project
        "project": ValueCondition,
        # Original
        "original": ValueCondition,
        # Pipeline
        "pipeline": ValueCondition,
        # Controller
        "controller": ValueCondition,
        # Upstream
        "upstream": ValueCondition,
        # Downstream
        "downstream": ValueCondition,
        # Cloning kind
        "cloning_kind": ValueCondition,
        # Artifact
        "in_artifact_kind": CallbackCondition(
            callback_conditions.in_artifact_kind_condition
        ),
        "out_artifact_kind": CallbackCondition(
            callback_conditions.in_artifact_kind_condition
        ),
        # Backend
        "backend": ValueCondition,
        # Framework
        "framework": ValueCondition,
        # Commit
        "commit": CallbackCondition(callback_conditions.commit_condition),
        # Kind
        "kind": ValueCondition,
        # Meta Kind
        "runtime": ValueCondition,
        # Namespace
        "namespace": ValueCondition,
        # Params
        "params": ComparisonCondition,
        "inputs": ComparisonCondition,
        "in": ComparisonCondition,
        # Results
        "outputs": ComparisonCondition,
        "out": ComparisonCondition,
        # Metrics
        "metrics": ComparisonCondition,
        # Meta
        "meta_flags": BoolCondition,
        "meta_info": ValueCondition,
        "meta_values": ValueCondition,
        # Tags
        "tags": KeysCondition
        if settings.DB_ENGINE_NAME == "sqlite"
        else ArrayCondition,
        # Live state
        "live_state": ValueCondition,
        # Duration
        "duration": ComparisonCondition,
        # Wait time
        "wait_time": ComparisonCondition,
        # Agent
        "agent": ValueCondition,
        "queue": ValueCondition,
        # Artifacts store
        "artifacts_store": ValueCondition,
        # States
        "state": ValueCondition,
        "component_state": ValueCondition,
        # Flags
        "is_managed": CallbackCondition(callback_conditions.is_managed_condition),
        "managed_by": ValueCondition,
        "pending": ValueCondition,
        # Resources
        "cost": ComparisonCondition,
        "cpu": ComparisonCondition,
        "memory": ComparisonCondition,
        "gpu": ComparisonCondition,
        "custom": ComparisonCondition,
        # Artifacts
        "artifacts": ValueCondition,
        # Connections
        "connections": ValueCondition,
        # Teams
        "teams": ValueCondition,
        # My runs
        "mine": CallbackCondition(callback_conditions.mine_condition),
    }


class RunsFilterRequest(namedtuple("RunsFilterRequest", "query_params")):
    pass


class RunsOfflineFilter:
    serializer_class = "_"
    queryset = "_"
    filter_backends = (QueryFilter, OrderingFilter)
    query_manager = RunQueryManager
    check_alive = RunQueryManager.CHECK_ALIVE
    ordering_fields = RunQueryManager.FIELDS_ORDERING
    ordering_proxy_fields = RunQueryManager.FIELDS_ORDERING_PROXY
    raise_original = True

    def filter_join(self, queryset, join: V1Join):
        request = RunsFilterRequest(query_params=join.to_dict())
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(request, queryset, self)
        return queryset

    def filter_stats(self, queryset, request):
        # We only use QueryFilter, order can change the annotations/aggregations
        queryset = QueryFilter().filter_queryset(request, queryset, self)
        return queryset

    @staticmethod
    def positive_int(integer_string, strict=False, cutoff=None):
        ret = int(integer_string)
        if ret < 0 or (ret == 0 and strict):
            raise ValueError()
        if cutoff:
            return min(ret, cutoff)
        return ret
