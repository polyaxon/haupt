from typing import Any, Iterable, Optional, Union

from clipped.utils.bools import to_bool
from clipped.utils.lists import to_list

from polyaxon.schemas import LiveState, ManagedBy
from traceml.artifacts import V1ArtifactKind


def archived_condition(
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
    queryset: Any = None,
    request: Optional[Any] = None,
) -> Any:
    """
    Example:
        >>>  {"archived": CallbackCondition(callback_conditions.archived_condition)}
    """
    params = to_list(params)
    if len(params) == 1 and to_bool(params[0]) is True:
        return (
            queryset.filter(live_state=LiveState.ARCHIVED)
            if queryset
            else query_backend(live_state=LiveState.ARCHIVED)
        )
    return query_backend(live_state=LiveState.LIVE)


def independent_condition(
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
    queryset: Any = None,
    request: Optional[Any] = None,
) -> Any:
    params = to_list(params)
    if len(params) == 1 and to_bool(params[0]) is True:
        return query_backend(experiment_group__isnull=True)
    return None


def metric_condition(
    queryset: Any,
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
    request: Optional[Any] = None,
) -> Any:
    params = to_list(params)
    if len(params) == 1 and to_bool(params[0]) is True:
        return query_backend(metric_annotations__name=True)
    return None


def commit_condition(
    queryset: Any,
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
    request: Optional[Any] = None,
) -> Any:
    params = to_list(params)
    if len(params) == 1:
        if negation:
            return ~query_backend(
                artifacts__kind=V1ArtifactKind.CODEREF,
                artifacts__name=params[0],
            )
        return query_backend(
            artifacts__kind=V1ArtifactKind.CODEREF,
            artifacts__name=params[0],
        )
    return None


def _artifact_kind_condition(
    is_input: bool,
    query_backend: Any,
    params: Union[str, Iterable],
    negation: bool,
) -> Any:
    params = to_list(params)
    if len(params) == 1:
        if negation:
            return ~query_backend(
                artifacts_lineage__is_input=is_input,
                artifacts__kind=params[0],
            )
        return query_backend(
            artifacts_lineage__is_input=is_input,
            artifacts__kind=params[0],
        )
    return None


def in_artifact_kind_condition(
    queryset: Any,
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
    request: Optional[Any] = None,
) -> Any:
    return _artifact_kind_condition(True, query_backend, params, negation)


def out_artifact_kind_condition(
    queryset: Any,
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
    request: Optional[Any] = None,
) -> Any:
    return _artifact_kind_condition(False, query_backend, params, negation)


def is_managed_condition(
    queryset: Any,
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
    request: Optional[Any] = None,
) -> Any:
    params = to_list(params)
    if len(params) == 1:
        if (to_bool(params[0]) is True and not negation) or (
            to_bool(params[0]) is False and negation
        ):
            return ~query_backend(managed_by=ManagedBy.USER)
        else:
            return query_backend(managed_by=ManagedBy.USER)
    return None


def mine_condition(
    queryset: Any,
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
    request: Optional[Any] = None,
) -> Any:
    params = to_list(params)
    if len(params) == 1:
        query = query_backend(user=request.user)
        if negation:
            return ~query
        return query
    return None
