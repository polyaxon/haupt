from clipped.compact.pydantic import ValidationError as PydanticValidationError
from clipped.utils.json import orjson_loads
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from django.conf import settings
from django.db.models import Q

from haupt.common.authentication.base import is_normal_user
from haupt.db.defs import Models
from haupt.db.managers.live_state import archive_run as base_archive_run
from haupt.db.managers.live_state import restore_run as base_restore_run
from haupt.db.managers.runs import add_run_contributors, base_approve_run
from haupt.db.managers.statuses import (
    new_run_skipped_status,
    new_run_status,
    new_run_stopping_status,
)
from polyaxon.exceptions import PolyaxonException
from polyaxon.schemas import V1StatusCondition


def clone_run(view, request, *args, **kwargs):
    view.run = view.get_object()
    run = view.pre_validate(view.run)
    content = None
    if "content" in request.data:
        content = request.data["content"]
    if content and not isinstance(content, dict):
        try:
            content = orjson_loads(content)
        except Exception as e:
            raise ValidationError("Cloning was not successful, error: {}".format(e))
    try:
        new_obj = view.clone(
            obj=run,
            content=content,
            name=request.data.get("name"),
            description=request.data.get("description"),
            tags=request.data.get("tags"),
            meta_info=request.data.get("meta_info"),
        )
    except (PydanticValidationError, PolyaxonException, ValueError) as e:
        raise ValidationError("Cloning was not successful, error: {}".format(e))

    add_run_contributors(new_obj, users=[request.user])
    view.audit(request, *args, **kwargs)
    serializer = view.get_serializer(new_obj)
    return Response(status=status.HTTP_201_CREATED, data=serializer.data)


def create_status(view, serializer):
    serializer.is_valid()
    validated_data = serializer.validated_data
    if not validated_data:
        return
    condition = None
    if validated_data.get("condition"):
        condition = V1StatusCondition.get_condition(**validated_data.get("condition"))
    if not condition:
        return
    if settings.HAS_ORG_MANAGEMENT and is_normal_user(view.request.user):
        status_meta_info = {
            "user": {
                "username": view.request.user.username,
                "email": view.request.user.email,
            },
        }
        condition.meta_info = status_meta_info
    new_run_status(
        run=view.run, condition=condition, force=validated_data.get("force", False)
    )


def stop_run(view, request, *args, **kwargs):
    status_meta_info = None
    if settings.HAS_ORG_MANAGEMENT and is_normal_user(request.user):
        status_meta_info = {
            "user": {
                "username": view.request.user.username,
                "email": view.request.user.email,
            },
        }
    if new_run_stopping_status(
        run=view.run,
        message="User requested to stop the run.",
        meta_info=status_meta_info,
    ):
        add_run_contributors(view.run, users=[request.user])
        view.audit(request, *args, **kwargs)
    return Response(status=status.HTTP_200_OK, data={})


def skip_run(view, request, *args, **kwargs):
    status_meta_info = None
    if settings.HAS_ORG_MANAGEMENT and is_normal_user(request.user):
        status_meta_info = {
            "user": {
                "username": view.request.user.username,
                "email": view.request.user.email,
            },
        }
    if new_run_skipped_status(
        run=view.run,
        message="User requested to skip the run.",
        meta_info=status_meta_info,
    ):
        add_run_contributors(view.run, users=[request.user])
        view.audit(request, *args, **kwargs)
    return Response(status=status.HTTP_200_OK, data={})


def approve_run(view, request, *args, **kwargs):
    pending = view.run.pending
    if pending:
        base_approve_run(view.run)
        add_run_contributors(view.run, users=[request.user])
        view.audit(request, *args, **kwargs)
    return Response(status=status.HTTP_200_OK, data={})


def transfer_run(view, request, *args, **kwargs):
    project_name = request.data.get("project")
    if project_name == view.project_name:
        return Response(status=status.HTTP_200_OK, data={})
    if not project_name:
        raise ValidationError("The destination project was not provided.")
    try:
        filters = {"name": project_name}
        if settings.HAS_ORG_MANAGEMENT:
            filters["owner__name"] = view.owner_name
        dest_project = Models.Project.objects.only("id").get(**filters)
    except Models.Project.DoesNotExist:
        raise ValidationError(
            "The destination project `{}` does not exist.".format(project_name)
        )

    view.run.project_id = dest_project.id
    view.run.save(update_fields=["project_id", "updated_at"])
    if view.run.has_pipeline:
        Models.Run.all.filter(Q(pipeline=view.run) | Q(controller=view.run)).update(
            project_id=dest_project.id
        )
    add_run_contributors(view.run, users=[request.user])
    view.audit(request, *args, **kwargs)
    return Response(status=status.HTTP_200_OK, data={})


def invalidate_run(view, request, *args, **kwargs):
    view.run.state = None
    view.run.save(update_fields=["state"])
    add_run_contributors(view.run, users=[request.user])
    view.audit(request, *args, **kwargs)
    return Response(status=status.HTTP_200_OK, data={})


def archive_run(view, request, *args, **kwargs):
    view.run = view.get_object()
    view.audit(request, *args, **kwargs)
    add_run_contributors(view.run, users=[request.user])
    base_archive_run(view.run)
    return Response(status=status.HTTP_200_OK, data={})


def restore_run(view, request, *args, **kwargs):
    view.run = view.get_object()
    view.audit(request, *args, **kwargs)
    add_run_contributors(view.run, users=[request.user])
    base_restore_run(view.run)
    return Response(status=status.HTTP_200_OK, data={})
