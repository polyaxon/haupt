#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from traceml.artifacts import V1RunArtifacts


def create(view, request, *args, **kwargs):
    if not request.data:
        raise ValidationError("Received no artifacts.")

    try:
        V1RunArtifacts.from_dict(request.data)
    except PydanticValidationError as e:
        raise ValidationError(e)

    view.audit(request, *args, **kwargs, artifacts=request.data.get("artifacts"))
    return Response(status=status.HTTP_201_CREATED)
