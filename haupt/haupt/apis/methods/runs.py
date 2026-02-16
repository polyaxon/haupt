from clipped.compact.pydantic import ValidationError as PydanticValidationError
from clipped.utils.json import orjson_loads
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from django.conf import settings

from haupt.common.authentication.base import is_normal_user
from haupt.common.permissions import PERMISSIONS_MAPPING
from haupt.db.defs import Models
from haupt.db.managers.runs import (
    add_run_contributors,
    archive_run_action,
    base_approve_run,
    invalidate_run_action,
    restore_run_action,
    skip_run_action,
    stop_run_action,
    transfer_run_action,
)
from haupt.db.managers.statuses import new_run_status
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
    actor_info = None
    if settings.HAS_ORG_MANAGEMENT and is_normal_user(request.user):
        actor_info = {
            "user": {
                "username": request.user.username,
                "email": request.user.email,
            },
        }
    if stop_run_action(
        run=view.run,
        message="User requested to stop the run.",
        actor_info=actor_info,
        contributor_user=request.user,
    ):
        view.audit(request, *args, **kwargs)
    return Response(status=status.HTTP_200_OK, data={})


def skip_run(view, request, *args, **kwargs):
    actor_info = None
    if settings.HAS_ORG_MANAGEMENT and is_normal_user(request.user):
        actor_info = {
            "user": {
                "username": request.user.username,
                "email": request.user.email,
            },
        }
    if skip_run_action(
        run=view.run,
        message="User requested to skip the run.",
        actor_info=actor_info,
        contributor_user=request.user,
    ):
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

    # Check user has write access to destination project
    permission_classes = PERMISSIONS_MAPPING.get(["PROJECT_RESOURCE_PERMISSION"])
    if permission_classes:
        permission = permission_classes[0]()
        if not permission.has_object_permission(request, view, dest_project):
            raise PermissionDenied(
                f"You don't have permission to transfer runs to project '{project_name}'"
            )

    if transfer_run_action(view.run, dest_project, contributor_user=request.user):
        view.audit(request, *args, **kwargs)
    return Response(status=status.HTTP_200_OK, data={})


def invalidate_run(view, request, *args, **kwargs):
    invalidate_run_action(view.run, contributor_user=request.user)
    view.audit(request, *args, **kwargs)
    return Response(status=status.HTTP_200_OK, data={})


def archive_run(view, request, *args, **kwargs):
    view.run = view.get_object()
    view.audit(request, *args, **kwargs)
    archive_run_action(view.run, contributor_user=request.user)
    return Response(status=status.HTTP_200_OK, data={})


def restore_run(view, request, *args, **kwargs):
    view.run = view.get_object()
    view.audit(request, *args, **kwargs)
    restore_run_action(view.run, contributor_user=request.user)
    return Response(status=status.HTTP_200_OK, data={})
