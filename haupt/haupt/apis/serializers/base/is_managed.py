from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from polyaxon.schemas import ManagedBy


class IsManagedMixin(serializers.Serializer):
    is_managed = serializers.BooleanField(initial=True, default=True, allow_null=True)

    def _get_is_managed(self, value):
        return value if isinstance(value, bool) else True

    def check_if_entity_is_managed(self, attrs, entity_name, config_field="content"):
        is_managed = None
        managed_by = None
        if "managed_by" in attrs:
            managed_by = attrs.get("managed_by")
            if not managed_by:
                managed_by = ManagedBy.AGENT
            if managed_by == ManagedBy.USER:
                is_managed = False
            elif ManagedBy.is_managed(managed_by):
                is_managed = True
        elif "is_managed" in attrs:
            is_managed = self._get_is_managed(attrs.get("is_managed"))
            if is_managed:
                managed_by = ManagedBy.AGENT
            else:
                managed_by = ManagedBy.USER

        if is_managed is None and managed_by is None:
            return attrs
        if is_managed and not attrs.get(config_field):
            raise ValidationError(
                "{} expects a `{}`.".format(entity_name, config_field)
            )
        attrs["managed_by"] = managed_by
        attrs.pop("is_managed", None)
        return attrs

    def validate_is_managed(self, value):
        return self._get_is_managed(value)
