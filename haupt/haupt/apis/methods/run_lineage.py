from clipped.utils.lists import to_list
from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from traceml.artifacts import V1RunArtifact, V1RunArtifacts


def create(view, request, *args, **kwargs):
    if not request.data:
        raise ValidationError("Received no artifacts.")

    data = request.data
    if "artifacts" in data:
        data = data["artifacts"]
        try:
            V1RunArtifacts.from_dict(request.data)
        except PydanticValidationError as e:
            raise ValidationError(e)
    else:  # Backward compatibility with legacy clients
        data = to_list(data)
        try:
            [V1RunArtifact.from_dict(r) for r in data]
        except PydanticValidationError as e:
            raise ValidationError(e)

    view.audit(request, *args, **kwargs, artifacts=data)
    return Response(status=status.HTTP_201_CREATED)
