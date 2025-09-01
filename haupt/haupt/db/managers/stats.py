from collections import namedtuple
from typing import Any, Tuple
from datetime import timedelta, timezone

from rest_framework.exceptions import ValidationError

from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.db.models.functions import Trunc
from django.utils.timezone import now

from clipped.utils.dates import DateTimeFormatter
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


class SeriesSerializer(
    namedtuple(
        "SeriesSerializer",
        "queryset start_date end_date boundary serializer_class",
    )
):
    @property
    def data(self):
        if self.queryset is None or self.serializer_class is None:
            raise Exception("SeriesSerializer was not configured correctly")

        queryset = self.queryset

        start_date = self.start_date
        end_date = self.end_date

        if isinstance(start_date, str):
            # Try to parse with timezone info first
            start_date = DateTimeFormatter.extract_datetime(
                start_date, timezone=str(timezone.utc), force_tz=True
            )
        if isinstance(end_date, str):
            end_date = DateTimeFormatter.extract_datetime(
                end_date, timezone=str(timezone.utc), force_tz=True
            )
        if not all([start_date, end_date]):
            end_date = end_date or now()
            start_date = start_date or end_date - timedelta(days=7)
        # Apply date filtering if provided
        queryset = queryset.filter(created_at__range=[start_date, end_date])
        # infer interval from date range
        interval = (end_date - start_date).days

        # Apply sampling based on interval
        if self.boundary:
            # Get only first and last snapshots
            snapshots = self._get_boundary_snapshots(queryset)
        else:
            snapshots = self._sample_snapshots(queryset, interval)

        serializer_class = self.serializer_class

        # Return paginated response in DRF format
        return {
            "count": snapshots.count(),
            "next": None,
            "previous": None,
            "results": serializer_class(snapshots, many=True).data,
        }

    def _get_boundary_snapshots(self, queryset):
        """
        Get only the first and last snapshots from the queryset
        """
        if not queryset.exists():
            return queryset.none()

        # Get first and last IDs
        ordered_qs = queryset.order_by("created_at")
        first_id = ordered_qs.values_list("id", flat=True).first()
        last_id = ordered_qs.values_list("id", flat=True).last()

        # If there's only one snapshot, return it
        if first_id == last_id:
            return queryset.filter(id=first_id)

        # Return both first and last
        return queryset.filter(id__in=[first_id, last_id]).order_by("created_at")

    def _sample_snapshots(self, queryset, interval):
        """
        Sample snapshots based on interval to avoid returning too much data

        Intervals in hours
        """
        total_count = queryset.count()

        if total_count <= 100 and interval < 24:
            # If the total count is small and the interval is short (less than a day),
            # Return all points for short intervals
            return queryset.order_by("created_at")

        # Calculate sampling rate
        max_points = {
            "day": 24,
            "week": 168,  # 7 * 24
            "month": 720,  # 30 * 24
            "year": 8760,  # 365 * 24
        }

        target_points = max_points.get(interval, 1000)

        if total_count <= target_points:
            return queryset.order_by("created_at")

        # Sample evenly distributed points
        step = total_count // target_points
        sampled_ids = list(
            queryset.order_by("created_at").values_list("id", flat=True)[::step]
        )
        return queryset.filter(id__in=sampled_ids).order_by("created_at")


def annotate_statuses(queryset, include_total=False):
    # Determine the field path based on the model
    model_name = queryset.model.__name__

    # For Organization and Team models, runs are accessed through projects
    if model_name in ["Organization", "Team"]:
        runs_field = "projects__runs"
    else:
        # For Project, Agent, Queue models, runs are directly accessible
        runs_field = "runs"

    agg = {
        "running": Count(
            runs_field,
            filter=Q(**{f"{runs_field}__status__in": LifeCycle.RUNNING_VALUES}),
            distinct=True,
        ),
        "pending": Count(
            runs_field,
            filter=Q(**{f"{runs_field}__status__in": LifeCycle.ALL_PENDING_VALUES}),
            distinct=True,
        ),
        "warning": Count(
            runs_field,
            filter=Q(**{f"{runs_field}__status__in": LifeCycle.ALL_WARNING_VALUES}),
            distinct=True,
        ),
    }
    if include_total:
        agg["count"] = Count(
            runs_field,
            distinct=True,
        )
    return queryset.annotate(**agg)


def annotate_quota(queryset):
    queryset_filter = Q(runs__status__in=LifeCycle.ON_K8S_VALUES)
    return queryset.annotate(
        cost=Sum("runs__cost", filter=queryset_filter),
        custom=Sum("runs__custom", filter=queryset_filter),
        gpu=Sum("runs__gpu", filter=queryset_filter),
        cpu=Sum("runs__cpu", filter=queryset_filter),
        memory=Sum("runs__memory", filter=queryset_filter),
    )


def collect_entity_run_status_stats(**filters):
    data = (
        Models.Run.objects.filter(**filters)
        .values("status")
        .annotate(run_count=Count("id"))
    )
    return {item["status"]: item["run_count"] for item in data}


class ProjectRunStats(
    namedtuple("ProjectRunStats", "run_count tracking_time wait_time resources")
):
    pass


def collect_entity_run_stats(**filters):
    data = (
        Models.Run.all.filter(**filters)
        .values("live_state")
        .annotate(
            run_count=Count("id"),
            sum_duration=Sum("duration"),
            sum_wait_time=Sum("wait_time"),
            sum_cpu=Sum("cpu"),
            sum_memory=Sum("memory"),
            sum_gpu=Sum("gpu"),
            sum_cost=Sum("cost"),
            sum_custom=Sum("custom"),
        )
    )
    rolling = collect_entity_run_rolling_stats(**filters)
    run_count = {item["live_state"]: item["run_count"] for item in data}
    tracking_time = {item["live_state"]: item["sum_duration"] for item in data}
    tracking_time["rolling"] = rolling.get("duration", {})
    wait_time = {item["live_state"]: item["sum_wait_time"] for item in data}
    wait_time["rolling"] = rolling.get("wait_time", {})
    cpu = {item["live_state"]: item["sum_cpu"] for item in data}
    cpu["rolling"] = rolling.get("cpu", {})
    memory = {item["live_state"]: item["sum_memory"] for item in data}
    memory["rolling"] = rolling.get("memory", {})
    gpu = {item["live_state"]: item["sum_gpu"] for item in data}
    gpu["rolling"] = rolling.get("gpu", {})
    cost = {item["live_state"]: item["sum_cost"] for item in data}
    cost["rolling"] = rolling.get("cost", {})
    custom = {item["live_state"]: item["sum_custom"] for item in data}
    custom["rolling"] = rolling.get("custom", {})
    resources = {
        "cpu": cpu,
        "memory": memory,
        "gpu": gpu,
        "cost": cost,
        "custom": custom,
    }
    return ProjectRunStats(run_count, tracking_time, wait_time, resources)


def collect_entity_run_rolling_stats(**filters):
    last_time = now() - timedelta(days=30)
    duration_filter = Q(duration__gt=0)
    wait_time_filter = Q(duration__gt=0)
    cpu_filter = Q(cpu__gt=0)
    memory_filter = Q(memory__gt=0)
    gpu_filter = Q(gpu__gt=0)
    cost_filter = Q(cost__gt=0)
    custom_filter = Q(custom__gt=0)
    _data = Models.Run.all.filter(created_at__gte=last_time, **filters).aggregate(
        avg_duration=Avg("duration", filter=duration_filter),
        min_duration=Min("duration", filter=duration_filter),
        max_duration=Max("duration", filter=duration_filter),
        avg_wait_time=Avg("wait_time", filter=wait_time_filter),
        min_wait_time=Min("wait_time", filter=wait_time_filter),
        max_wait_time=Max("wait_time", filter=wait_time_filter),
        avg_cpu=Avg("cpu", filter=cpu_filter),
        min_cpu=Min("cpu", filter=cpu_filter),
        max_cpu=Max("cpu", filter=cpu_filter),
        avg_memory=Avg("memory", filter=memory_filter),
        min_memory=Min("memory", filter=memory_filter),
        max_memory=Max("memory", filter=memory_filter),
        avg_gpu=Avg("gpu", filter=gpu_filter),
        min_gpu=Min("gpu", filter=gpu_filter),
        max_gpu=Max("gpu", filter=gpu_filter),
        avg_cost=Avg("cost", filter=cost_filter),
        max_cost=Max("cost", filter=cost_filter),
        min_cost=Min("cost", filter=cost_filter),
        avg_custom=Avg("custom", filter=custom_filter),
        min_custom=Min("custom", filter=custom_filter),
        max_custom=Max("custom", filter=custom_filter),
    )
    data = {}
    for key in [
        "duration",
        "wait_time",
        "cpu",
        "memory",
        "gpu",
        "cost",
        "custom",
    ]:
        key_data = {
            "avg": _data.get(f"avg_{key}", 0),
            "min": _data.get(f"min_{key}", 0),
            "max": _data.get(f"max_{key}", 0),
        }
        data[key] = key_data

    return data


def collect_project_version_stats(**filters):
    data = (
        Models.ProjectVersion.objects.filter(**filters)
        .values("kind")
        .annotate(kind_count=Count("kind"))
    )
    return {item["kind"]: item["kind_count"] for item in data}


def collect_entity_unique_user_stats(**filters):
    unique_users = list(
        Models.Run.all.filter(**filters)
        .filter(contributors__isnull=False)
        .values_list("contributors__id", flat=True)
        .distinct()
    )
    if not unique_users:
        return {}
    return {"count": len(unique_users), "ids": unique_users}


def collect_project_unique_user_stats(project):
    runs_unique_users = collect_entity_unique_user_stats(project=project)
    if runs_unique_users:
        runs_unique_users = runs_unique_users.get("ids", [])
    else:
        runs_unique_users = []
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


def collect_agent_queue_count_stats(agent: Any):
    data = agent.queues.values("live_state").annotate(queue_count=Count("id"))
    return {item["live_state"]: item["queue_count"] for item in data}


def collect_agent_project_count_stats(agent: Any):
    """Collect distinct project count for agent grouped by live_state."""
    data = (
        Models.Run.objects.filter(agent=agent)
        .values("project__live_state")
        .annotate(project_count=Count("project", distinct=True))
    )
    return {item["project__live_state"]: item["project_count"] for item in data}


def collect_queue_project_count_stats(queue: Any):
    """Collect distinct project count for queue grouped by live_state."""
    data = (
        Models.Run.objects.filter(queue=queue)
        .values("project__live_state")
        .annotate(project_count=Count("project", distinct=True))
    )
    return {item["project__live_state"]: item["project_count"] for item in data}


def collect_org_projects_contributors(org: Any):
    return set(
        list(
            Models.Project.all.filter(owner=org)
            .filter(contributors__isnull=False)
            .values_list("contributors__id", flat=True)
            .distinct()
        )
    )
