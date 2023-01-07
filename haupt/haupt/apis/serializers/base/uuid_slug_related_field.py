#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from rest_framework.relations import SlugRelatedField


class UuidSlugRelatedField(SlugRelatedField):
    def to_representation(self, obj):
        value = getattr(obj, self.slug_field)
        if value:
            return value.hex
        return value
