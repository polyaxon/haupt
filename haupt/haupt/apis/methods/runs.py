#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from clipped.utils.json import orjson_loads
from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

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
