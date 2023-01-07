#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class IsManagedMixin(serializers.Serializer):
    is_managed = serializers.BooleanField(initial=True, default=True, allow_null=True)

    def _get_is_managed(self, value):
        return value if isinstance(value, bool) else True

    def check_if_entity_is_managed(self, attrs, entity_name, config_field="content"):
        cond = (
            "is_managed" in attrs
            and self._get_is_managed(attrs.get("is_managed"))
            and not attrs.get(config_field)
        )
        if cond:
            raise ValidationError(
                "{} expects a `{}`.".format(entity_name, config_field)
            )

    def validate_is_managed(self, value):
        return self._get_is_managed(value)
