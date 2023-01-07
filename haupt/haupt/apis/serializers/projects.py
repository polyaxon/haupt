#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from rest_framework import fields, serializers
from rest_framework.exceptions import ValidationError

from django.db import IntegrityError

from haupt.apis.serializers.base.tags import TagsMixin
from haupt.db.abstracts.getter import get_project_model


class ProjectNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_project_model()
        fields = ("name",)


class ProjectSerializer(TagsMixin, serializers.ModelSerializer):
    uuid = fields.UUIDField(format="hex", read_only=True)

    class Meta:
        model = get_project_model()
        fields = (
            "uuid",
            "name",
            "description",
            "tags",
            "created_at",
            "updated_at",
        )


class ProjectDetailSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + (
            "readme",
            "live_state",
        )

    def update(self, instance, validated_data):
        validated_data = self.validated_tags(
            validated_data=validated_data, tags=instance.tags
        )

        try:
            return super().update(instance=instance, validated_data=validated_data)
        except IntegrityError:
            raise ValidationError(
                f"A project with name {validated_data['name']} already exists."
            )


class ProjectCreateSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ("readme",)

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise ValidationError(
                f"A project with name {validated_data['name']} already exists."
            )
