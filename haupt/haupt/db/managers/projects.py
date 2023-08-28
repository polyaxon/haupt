from datetime import datetime

from django.db.models import Max, OuterRef, Subquery

from haupt.db.defs import Models


def update_project_based_on_last_runs(
    last_created_at_threshold: datetime,
    last_updated_at_threshold: datetime,
):
    project_ids_with_recent_runs = (
        Models.Run.objects.filter(
            created_at__gte=last_created_at_threshold,
            project__updated_at__lt=last_updated_at_threshold,
        )
        .values_list("project_id", flat=True)
        .distinct()
    )

    if not project_ids_with_recent_runs:
        return

    latest_run_time = (
        Models.Run.objects.filter(
            project_id__in=project_ids_with_recent_runs,
            created_at__gte=last_created_at_threshold,
        )
        .filter(project_id=OuterRef("id"))
        .values("project_id")
        .annotate(latest_created_at=Max("created_at"))
        .values("latest_created_at")
    )

    Models.Project.objects.filter(id__in=project_ids_with_recent_runs).update(
        updated_at=Subquery(latest_run_time)
    )


def update_project_based_on_last_versions(
    last_created_at_threshold: datetime,
    last_updated_at_threshold: datetime,
):
    project_ids_with_recent_versions = (
        Models.ProjectVersion.objects.filter(
            created_at__gte=last_created_at_threshold,
            project__updated_at__lt=last_updated_at_threshold,
        )
        .values_list("project_id", flat=True)
        .distinct()
    )

    if not project_ids_with_recent_versions:
        return

    latest_version_time = (
        Models.ProjectVersion.objects.filter(
            project_id__in=project_ids_with_recent_versions,
            created_at__gte=last_created_at_threshold,
        )
        .filter(project_id=OuterRef("id"))
        .values("project_id")
        .annotate(latest_version_created_at=Max("created_at"))
        .values("latest_version_created_at")
    )

    Models.Project.objects.filter(id__in=project_ids_with_recent_versions).update(
        updated_at=Subquery(latest_version_time)
    )
