#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from marshmallow import ValidationError as MarshmallowValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from polyaxon.utils.list_utils import to_list
from traceml.artifacts import V1RunArtifact


def create(view, request, *args, **kwargs):
    if not request.data:
        raise ValidationError("Received no artifacts.")

    data = to_list(request.data)
    try:
        [V1RunArtifact(r) for r in data]
    except MarshmallowValidationError as e:
        raise ValidationError(e)

    view.audit(request, *args, **kwargs, artifacts=data)
    return Response(status=status.HTTP_201_CREATED)
