#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from typing import Any, Iterable, Optional, Union

from clipped.utils.bools import to_bool
from clipped.utils.lists import to_list

from polyaxon import live_state
from traceml.artifacts import V1ArtifactKind


def archived_condition(
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
    queryset: Any = None,
) -> Any:
    """
    Example:
        >>>  {"archived": CallbackCondition(callback_conditions.archived_condition)}
    """
    params = to_list(params)
    if len(params) == 1 and to_bool(params[0]) is True:
        return (
            queryset.filter(live_state=live_state.STATE_ARCHIVED)
            if queryset
            else query_backend(live_state=live_state.STATE_ARCHIVED)
        )
    return query_backend(live_state=live_state.STATE_LIVE)


def independent_condition(
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
    queryset: Any = None,
) -> Any:
    params = to_list(params)
    if len(params) == 1 and to_bool(params[0]) is True:
        return queryset.filter(experiment_group__isnull=True)
    return queryset


def metric_condition(
    queryset: Any,
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
) -> Any:
    params = to_list(params)
    if len(params) == 1 and to_bool(params[0]) is True:
        return queryset.filter(metric_annotations__name=True)
    return queryset


def commit_condition(
    queryset: Any,
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
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
) -> Any:
    return _artifact_kind_condition(True, queryset, params, negation)


def out_artifact_kind_condition(
    queryset: Any,
    params: Union[str, Iterable],
    negation: bool,
    query_backend: Any,
    timezone: Optional[str] = None,
) -> Any:
    return _artifact_kind_condition(False, queryset, params, negation)
