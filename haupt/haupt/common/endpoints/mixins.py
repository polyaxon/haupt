from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import CreateModelMixin as DJRCreateModelMixin
from rest_framework.mixins import DestroyModelMixin as DJRDestroyModelMixin
from rest_framework.mixins import ListModelMixin as DRFListModelMixin
from rest_framework.mixins import RetrieveModelMixin as DRFRetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin as DJRUpdateModelMixin
from rest_framework.response import Response


class CreateModelMixin(DJRCreateModelMixin):
    """
    Create a model instance.
    """


class ListModelMixin(DRFListModelMixin):
    """
    List a queryset.
    """

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        self.audit(request, *args, **kwargs)
        return response


class RetrieveModelMixin(DRFRetrieveModelMixin):
    """
    Retrieve a model instance.
    """

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        self.audit(request, *args, **kwargs)
        return response


class UpdateModelMixin(DJRUpdateModelMixin):
    """
    Update a model instance.
    """

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        self.audit(request, *args, **kwargs)
        return response


class DestroyModelMixin(DJRDestroyModelMixin):
    """
    Destroy a model instance.
    """

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.audit(request, *args, **kwargs)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        return super().perform_destroy(instance)


class StatsMixin:
    def validate_stats_mode(self):
        mode = self.request.query_params.get("mode")
        if mode not in {"stats", "analytics"}:
            raise ValidationError("Received an unsupported mode: {}".format(mode))
        return mode
