from clipped.utils.json import orjson_loads
from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from django.conf import settings
from django.db.models import Q

from haupt.db.defs import Models
from haupt.db.managers.runs import base_approve_run
from haupt.db.managers.statuses import new_run_status, new_run_stopping_status
from polyaxon.exceptions import PolyaxonException
from polyaxon.lifecycle import V1StatusCondition


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
    if condition:
        new_run_status(
            run=view.run, condition=condition, force=validated_data.get("force", False)
        )


def stop_run(view, request, *args, **kwargs):
    if new_run_stopping_status(run=view.run, message="User requested to stop the run."):
        view.audit(request, *args, **kwargs)
    return Response(status=status.HTTP_200_OK, data={})


def approve_run(view, request, *args, **kwargs):
    pending = view.run.pending
    if pending:
        base_approve_run(view.run)
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
    view.run.save(update_fields=["project_id"])
    if view.run.has_pipeline:
        Models.Run.all.filter(Q(pipeline=view.run) | Q(controller=view.run)).update(
            project_id=dest_project.id
        )
    view.audit(request, *args, **kwargs)
    return Response(status=status.HTTP_200_OK, data={})
