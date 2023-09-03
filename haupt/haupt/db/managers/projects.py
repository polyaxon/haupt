from datetime import datetime
from typing import List, Optional

from django.conf import settings
from django.db.models import Q
from django.utils.timezone import now

from haupt.common.authentication.base import is_normal_user
from haupt.db.defs import Models


def update_project_based_on_last_updated_entities(
    last_created_at_threshold: datetime,
    last_updated_at_threshold: datetime,
):
    current_check = now()
    project_ids_with_recent_runs = (
        Models.Run.all.filter(
            project__updated_at__lt=last_updated_at_threshold,
        )
        .filter(
            Q(created_at__gte=last_created_at_threshold)
            | Q(updated_at__gte=last_created_at_threshold)
        )
        .values_list("project_id", flat=True)
        .distinct()
    )
    project_ids_with_recent_versions = (
        Models.ProjectVersion.objects.filter(
            project__updated_at__lt=last_updated_at_threshold,
            created_at__gte=last_created_at_threshold,
        )
        .values_list("project_id", flat=True)
        .distinct()
    )

    project_ids_with_recent_entities = set(project_ids_with_recent_runs) | set(
        project_ids_with_recent_versions
    )
    if not project_ids_with_recent_entities:
        return

    Models.Project.objects.filter(id__in=project_ids_with_recent_entities).update(
        updated_at=current_check
    )


def add_project_contributors(
    project: Models.Project,
    users: Optional[List[Models.User]] = None,
    user_ids: Optional[List[int]] = None,
):
    if not settings.HAS_ORG_MANAGEMENT:
        return
    if not project:
        return
    _users = [u.id for u in users if is_normal_user(u)] if users else user_ids
    if not _users:
        return

    project.contributors.add(*_users)
