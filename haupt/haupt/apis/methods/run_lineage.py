from clipped.compact.pydantic import ValidationError as PydanticValidationError
from clipped.utils.lists import to_list
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from django.db.models import Q

from haupt.db.defs import Models
from polyaxon._flow import V1RunEdgeKind
from polyaxon._sdk.schemas import V1RunEdgesGraph
from traceml.artifacts import V1RunArtifact, V1RunArtifacts


def set_artifacts(view, request, *args, **kwargs):
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


def set_edges(view, request, *args, **kwargs):
    if not request.data:
        raise ValidationError("Received no edges.")

    data = request.data
    if "edges" not in data:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    try:
        lineage = V1RunEdgesGraph.from_dict(data)
    except PydanticValidationError as e:
        raise ValidationError(e)

    Models.RunEdge.objects.filter(
        Q(downstream=view.run) | Q(upstream=view.run)
    ).delete()
    if not lineage.edges:
        return Response(status=status.HTTP_201_CREATED)

    runs = Models.Run.all.filter(uuid__in=[e.run for e in lineage.edges]).values(
        "uuid", "id"
    )
    runs_uuid_to_id = {r["uuid"].hex: r["id"] for r in runs}
    edges = []
    for e in lineage.edges:
        if e.is_upstream:
            upstream = runs_uuid_to_id.get(e.run)
            downstream = view.run.id
        else:
            upstream = view.run.id
            downstream = runs_uuid_to_id.get(e.run)
        edges.append(
            Models.RunEdge(
                upstream_id=upstream,
                downstream_id=downstream,
                values=e.values,
                kind=V1RunEdgeKind.MANUAL,
            )
        )
    Models.RunEdge.objects.bulk_create(edges)
    view.audit(request, *args, **kwargs, artifacts=data)
    return Response(status=status.HTTP_201_CREATED)
