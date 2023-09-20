from collections import namedtuple
from typing import Any, Tuple

from rest_framework.exceptions import ValidationError

from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.db.models.functions import Trunc

from haupt.db.defs import Models
from haupt.db.query_managers.bookmarks import filter_bookmarks
from haupt.db.query_managers.run import RunsOfflineFilter
from polyaxon.exceptions import PQLException
from polyaxon.schemas import LifeCycle

AGGREGATE_MAP = {
    "avg": Avg,
    "min": Min,
    "max": Max,
    "sum": Sum,
}

GROUPBY_FIELD = {
    "queue": "queue__name",
    "agent": "agent__name",
    "user": "user__username",
    "project": "project__name",
    "component": "component__name",
}


def get_groupby_field(groupby: str):
    if groupby in GROUPBY_FIELD:
        return {f"{groupby}_name": F(GROUPBY_FIELD[groupby])}
    return None


def check_count_groupby(aggregate: str, groupby: str):
    if groupby not in {
        "status",
        "kind",
        "queue",
        "agent",
        "user",
        "project",
        "component",
    }:
        raise ValidationError(
            f"Received an unsupported stats specification: {aggregate} - {groupby}"
        )


def check_aggregate_groupby(aggregate: str, groupby: str):
    if groupby not in {
        "wait_time",
        "duration",
        "cpu",
        "memory",
        "gpu",
        "custom",
        "cost",
    }:
        raise ValidationError(
            f"Received an unsupported stats specification: {aggregate} - {groupby}"
        )


def check_trunc(trunc: str) -> Tuple[str, str]:
    parts = trunc.split(".")
    if len(parts) != 2:
        raise ValidationError(f"Received an unsupported trunc value: {trunc}")

    if parts[1] not in {
        "minute",
        "hour",
        "day",
        "week",
        "month",
    }:
        raise ValidationError(f"Received an unsupported trunc value: {trunc}")

    if parts[0] not in {
        "created_at",
        "started_at",
        "finished_at",
    }:
        raise ValidationError(f"Received an unsupported trunc value: {trunc}")

    return parts[0], parts[1]


def get_aggregation(aggregate: str, groupby: str):
    aggregate = aggregate.split(",")
    results = {}
    for agg in aggregate:
        if agg in AGGREGATE_MAP:
            results["{}__{}".format(groupby, agg)] = AGGREGATE_MAP[agg](groupby)
        elif agg == "total":
            results["{}__total".format(groupby)] = Sum(F(groupby) * F("duration"))
        else:
            raise ValidationError(
                f"Received an unsupported stats specification: "
                f"annotations - {aggregate} - {groupby}. "
                f"Please check the aggregate ({agg})."
            )

    return results


def get_annotation_stats(queryset, aggregate: str, groupby: str):
    if aggregate == "progress":
        return queryset.aggregate(
            done=Count("id", filter=Q(status__in=LifeCycle.DONE_VALUES), distinct=True),
            count=Count("id", distinct=True),
        )
    if aggregate == "count":
        check_count_groupby(aggregate, groupby)
        groupby_field = get_groupby_field(groupby)
        queryset = (
            queryset.values(**groupby_field)
            if groupby_field
            else queryset.values(groupby)
        )
        return queryset.annotate(count=Count("id", distinct=True))

    if aggregate:
        check_aggregate_groupby(aggregate, groupby)
        agg = get_aggregation(aggregate, groupby)
        return queryset.aggregate(**agg)

    raise ValidationError(
        f"Received an unsupported stats specification: annotations - {aggregate} - {groupby}"
    )


def get_series_stats(queryset, aggregate: str, groupby: str, trunc: str):
    if not trunc:
        raise ValidationError(
            f"Received an unsupported stats specification: {aggregate} - {groupby} - {trunc}"
        )
    trunc_field, trunc_frequency = check_trunc(trunc)
    queryset = queryset.annotate(trunc_time=Trunc(trunc_field, trunc_frequency))
    if aggregate == "count":
        check_count_groupby(aggregate, groupby)
        groupby_field = get_groupby_field(groupby)
        queryset = (
            queryset.values("trunc_time", **groupby_field)
            if groupby_field
            else queryset.values(groupby, "trunc_time")
        )
        return queryset.annotate(count=Count("id", distinct=True))
    if aggregate:
        check_aggregate_groupby(aggregate, groupby)
        agg = get_aggregation(aggregate, groupby)
        return queryset.values("trunc_time").annotate(**agg).order_by("trunc_time")

    raise ValidationError(
        f"Received an unsupported stats specification: "
        f"annotations - {aggregate} - {groupby} - {trunc}"
    )


def get_stats(queryset, kind: str, aggregate: str, groupby: str, trunc: str):
    if kind == "annotations":
        return get_annotation_stats(
            queryset=queryset, aggregate=aggregate, groupby=groupby
        )
    elif kind == "series":
        return get_series_stats(
            queryset=queryset, aggregate=aggregate, groupby=groupby, trunc=trunc
        )

    raise ValidationError(f"Received an unsupported kind: {kind}")


class StatsSerializer(
    namedtuple("StatsSerializer", "queryset kind aggregate groupby trunc")
):
    @property
    def data(self):
        if self.queryset is not None:
            return get_stats(
                queryset=self.queryset,
                kind=self.kind,
                aggregate=self.aggregate,
                groupby=self.groupby,
                trunc=self.trunc,
            )
        raise Exception("StatsSerializer was not configured correctly")

    @classmethod
    def filter_queryset(cls, queryset, request, view):
        queryset = filter_bookmarks(queryset, request, view)
        offline_filter = RunsOfflineFilter()
        try:
            queryset = offline_filter.filter_stats(queryset=queryset, request=request)
        except PQLException as e:
            raise ValidationError(
                "Received a wrong join specification. Error: {}".format(e)
            )

        limit = request.query_params.get("limit")
        offset = request.query_params.get("offset")
        if limit:
            try:
                limit = RunsOfflineFilter.positive_int(limit, strict=True)
                offset = RunsOfflineFilter.positive_int(offset or 0, strict=True)
            except (ValueError, TypeError):
                raise ValidationError(
                    "Received a wrong (limit/offset) specification. "
                    "limit: {}, offset: {}".format(limit, offset)
                )
        if limit:
            return Models.Run.all.filter(
                id__in=queryset.values_list("id", flat=True)[offset : offset + limit]
            )
        return queryset


def annotate_statuses(queryset):
    return queryset.annotate(
        count=Count(
            "runs",
            distinct=True,
        ),
        running=Count(
            "runs",
            filter=Q(runs__status__in=LifeCycle.RUNNING_VALUES),
            distinct=True,
        ),
        pending=Count(
            "runs",
            filter=Q(runs__status__in=LifeCycle.ALL_PENDING_VALUES),
            distinct=True,
        ),
        warning=Count(
            "runs",
            filter=Q(runs__status__in=LifeCycle.ALL_WARNING_VALUES),
            distinct=True,
        ),
    )


def annotate_quota(queryset):
    queryset_filter = Q(runs__status__in=LifeCycle.ON_K8S_VALUES)
    return queryset.annotate(
        cost=Sum("runs__cost", filter=queryset_filter),
        custom=Sum("runs__custom", filter=queryset_filter),
        gpu=Sum("runs__gpu", filter=queryset_filter),
        cpu=Sum("runs__cpu", filter=queryset_filter),
        memory=Sum("runs__memory", filter=queryset_filter),
    )


def collect_project_run_count_stats(project: Models.Project):
    data = (
        Models.Run.all.filter(project=project)
        .values("live_state")
        .annotate(run_count=Count("id"))
    )
    return {item["live_state"]: item["run_count"] for item in data}


def collect_project_run_status_stats(project: Models.Project):
    data = (
        Models.Run.objects.filter(project=project)
        .values("status")
        .annotate(run_count=Count("id"))
    )
    return {item["status"]: item["run_count"] for item in data}


def collect_project_run_duration_stats(project: Models.Project):
    data = (
        Models.Run.all.filter(project=project)
        .values("live_state")
        .annotate(sum_duration=Sum("duration"))
    )
    return {item["live_state"]: item["sum_duration"] for item in data}


def collect_project_version_stats(project: Models.Project):
    data = project.versions.values("kind").annotate(kind_count=Count("kind"))
    return {item["kind"]: item["kind_count"] for item in data}


def collect_project_unique_user_stats(project):
    runs_unique_users = list(
        Models.Run.all.filter(project=project)
        .filter(contributors__isnull=False)
        .values_list("contributors__id", flat=True)
        .distinct()
    )
    versions_unique_users = list(
        project.versions.filter(contributors__isnull=False)
        .values_list("contributors__id", flat=True)
        .distinct()
    )
    unique_users = set(runs_unique_users + versions_unique_users)
    if not unique_users:
        return {}
    return {"count": len(unique_users), "ids": list(unique_users)}


def collect_org_project_count_stats(org: Any):
    data = (
        Models.Project.all.filter(owner=org)
        .values("live_state")
        .annotate(project_count=Count("id"))
    )
    return {item["live_state"]: item["project_count"] for item in data}


def collect_org_projects_contributors(org: Any):
    return set(
        list(
            Models.Project.all.filter(owner=org)
            .filter(contributors__isnull=False)
            .values_list("contributors__id", flat=True)
            .distinct()
        )
    )
