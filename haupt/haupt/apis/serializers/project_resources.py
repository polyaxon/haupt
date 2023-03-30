#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from pydantic import ValidationError as PydanticValidationError
from rest_framework import fields, serializers
from rest_framework.exceptions import ValidationError

from django.db import IntegrityError

from haupt.apis.serializers.base.cloning import CloningMixin
from haupt.apis.serializers.base.is_managed import IsManagedMixin
from haupt.apis.serializers.base.pipeline import PipelineMixin
from haupt.apis.serializers.base.settings import SettingsMixin
from haupt.apis.serializers.base.tags import TagsMixin
from haupt.db.abstracts.getter import get_run_model
from haupt.db.managers.runs import create_run
from haupt.orchestration import operations
from polyaxon.exceptions import PolyaxonException
from polyaxon.polyaxonfile import OperationSpecification
from polyaxon.schemas import V1RunPending


class RunSerializer(
    serializers.ModelSerializer,
    CloningMixin,
    PipelineMixin,
    SettingsMixin,
    TagsMixin,
):
    uuid = fields.UUIDField(format="hex", read_only=True)
    original = fields.SerializerMethodField()
    pipeline = fields.SerializerMethodField()
    started_at = fields.DateTimeField(read_only=True)
    finished_at = fields.DateTimeField(read_only=True)
    settings = fields.SerializerMethodField()

    class Meta:
        model = get_run_model()
        fields = (
            "uuid",
            "name",
            "created_at",
            "updated_at",
            "started_at",
            "finished_at",
            "wait_time",
            "duration",
            "kind",
            "runtime",
            "meta_info",
            "status",
            "pipeline",
            "original",
            "is_managed",
            "pending",
            "inputs",
            "outputs",
            "tags",
            "settings",
        )
        extra_kwargs = {
            "is_managed": {"read_only": True},
        }


class OfflineRunSerializer(
    serializers.ModelSerializer,
    TagsMixin,
):
    uuid = fields.UUIDField(format="hex")
    created_at = fields.DateTimeField()

    class Meta:
        model = get_run_model()
        fields = (
            "uuid",
            "name",
            "description",
            "tags",
            "created_at",
            "updated_at",
            "started_at",
            "finished_at",
            "wait_time",
            "duration",
            "kind",
            "runtime",
            "meta_info",
            "status",
            "status_conditions",
            "is_managed",
            "inputs",
            "outputs",
            "content",
            "raw_content",
        )

    def create(self, validated_data, commit: bool = True):
        try:
            obj = super().create(validated_data)
        except IntegrityError:
            raise ValidationError(
                f"A run with uuid {validated_data.get('uuid')} already exists."
            )
        # Override auto-field for created_at
        created_at = validated_data.get("created_at")
        if created_at:
            obj.created_at = created_at
        if commit:
            obj.save()
        return obj


class OperationCreateSerializer(serializers.ModelSerializer, IsManagedMixin, TagsMixin):
    uuid = fields.UUIDField(format="hex", read_only=True)
    is_approved = fields.BooleanField(write_only=True, allow_null=True, required=False)

    class Meta:
        model = get_run_model()
        fields = (
            "uuid",
            "name",
            "description",
            "content",
            "is_managed",
            "pending",
            "meta_info",
            "tags",
            "is_approved",
        )
        extra_kwargs = {
            "is_approved": {"write_only": True},
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        self.check_if_entity_is_managed(attrs=attrs, entity_name="Run")
        return attrs

    def create(self, validated_data):
        is_managed = validated_data["is_managed"]
        content = validated_data.get("content")
        meta_info = validated_data.get("meta_info") or {}
        if content:
            is_managed = True if is_managed is None else is_managed

        if is_managed and not content:
            raise ValidationError(
                "Managed runs require a content with valid specification"
            )

        project_id = validated_data["project"].id
        user = validated_data.get("user")
        name = validated_data.get("name")
        description = validated_data.get("description")
        tags = validated_data.get("tags")
        pending = validated_data.get("pending")
        # Check the deprecated `is_approved` flag
        if pending is None:
            is_approved = validated_data.get("is_approved")
            if is_approved is False:
                pending = V1RunPending.UPLOAD

        if is_managed or content:
            try:
                op_spec = OperationSpecification.read(content)
            except Exception as e:
                raise ValidationError(e)
            if op_spec.is_template():
                raise ValidationError(
                    "Received a template polyaxonfile, "
                    "Please customize the specification or disable the template."
                )
            try:
                return operations.init_and_save_run(
                    project_id=project_id,
                    user_id=user.id if user else None,
                    op_spec=op_spec,
                    name=name,
                    description=description,
                    tags=tags,
                    meta_info=meta_info,
                    is_managed=is_managed,
                    pending=pending,
                    supported_kinds=validated_data.get("supported_kinds"),
                    supported_owners=validated_data.get("supported_owners"),
                )
            except (PydanticValidationError, PolyaxonException, ValueError) as e:
                raise ValidationError(e)
        else:
            return create_run(
                project_id=project_id,
                user_id=user.id if user else None,
                name=name,
                description=description,
                tags=tags,
                meta_info=meta_info,
            )
