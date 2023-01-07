#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from rest_framework import fields, serializers

from haupt.apis.serializers.base.is_managed import IsManagedMixin
from haupt.apis.serializers.base.project import ProjectMixin
from haupt.apis.serializers.project_resources import RunSerializer
from haupt.db.abstracts.getter import get_run_model


class RunStatusSerializer(serializers.ModelSerializer):
    uuid = fields.UUIDField(format="hex", read_only=True)
    condition = fields.DictField(
        write_only=True, allow_empty=True, allow_null=True, required=False
    )
    force = fields.BooleanField(write_only=True, required=False)

    class Meta:
        model = get_run_model()
        fields = (
            "uuid",
            "status",
            "condition",
            "status_conditions",
            "meta_info",
            "force",
        )
        extra_kwargs = {
            "status": {"read_only": True},
            "status_conditions": {"read_only": True},
        }


class RunDetailSerializer(RunSerializer, ProjectMixin, IsManagedMixin):
    project = fields.SerializerMethodField()
    merge = fields.BooleanField(write_only=True, required=False)

    class Meta(RunSerializer.Meta):
        fields = RunSerializer.Meta.fields + (
            "project",
            "readme",
            "description",
            "raw_content",
            "content",
            "live_state",
            "merge",
        )
        extra_kwargs = {
            "content": {"read_only": True},
            "raw_content": {"read_only": True},
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        self.check_if_entity_is_managed(attrs=attrs, entity_name="Run")
        return attrs

    def validated_inputs(self, validated_data, inputs):
        new_inputs = validated_data.get("inputs")
        if not validated_data.get("merge") or not inputs or not new_inputs:
            # This is the default behavior
            return validated_data

        inputs.update(new_inputs)
        validated_data["inputs"] = inputs
        return validated_data

    def validated_meta(self, validated_data, meta_info):
        new_meta_info = validated_data.get("meta_info")
        if not validated_data.get("merge") or not meta_info or not new_meta_info:
            # This is the default behavior
            return validated_data

        meta_info.update(new_meta_info)
        validated_data["meta_info"] = meta_info
        return validated_data

    def validated_outputs(self, validated_data, outputs):
        new_outputs = validated_data.get("outputs")
        if not validated_data.get("merge") or not outputs or not new_outputs:
            # This is the default behavior
            return validated_data

        outputs.update(new_outputs)
        validated_data["outputs"] = outputs
        return validated_data

    def update(self, instance, validated_data):
        validated_data = self.validated_tags(
            validated_data=validated_data, tags=instance.tags
        )
        validated_data = self.validated_outputs(
            validated_data=validated_data, outputs=instance.outputs
        )
        validated_data = self.validated_inputs(
            validated_data=validated_data, inputs=instance.inputs
        )
        validated_data = self.validated_meta(
            validated_data=validated_data, meta_info=instance.meta_info
        )

        return super().update(instance=instance, validated_data=validated_data)
