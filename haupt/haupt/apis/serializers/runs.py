from typing import Dict, Optional

from clipped.compact.pydantic import ValidationError as PydanticValidationError
from rest_framework import fields, serializers
from rest_framework.exceptions import ValidationError

from django.db import IntegrityError

from haupt.apis.serializers.base.bookmarks_mixin import BookmarkedSerializerMixin
from haupt.apis.serializers.base.cloning import CloningMixin
from haupt.apis.serializers.base.is_managed import IsManagedMixin
from haupt.apis.serializers.base.owner_mixin import ProjectOwnerMixin
from haupt.apis.serializers.base.pipeline import PipelineMixin
from haupt.apis.serializers.base.project import ProjectMixin
from haupt.apis.serializers.base.resources_mixin import ResourcesMixin
from haupt.apis.serializers.base.settings import FullSettingsMixin, SettingsMixin
from haupt.apis.serializers.base.tags import TagsMixin
from haupt.apis.serializers.base.user_mixin import UserMixin
from haupt.db.defs import Models
from haupt.db.managers.runs import create_run
from haupt.orchestration import operations
from polyaxon._polyaxonfile import OperationSpecification
from polyaxon.exceptions import PolyaxonException
from polyaxon.schemas import ManagedBy, V1RunEdgeKind, V1RunPending


class BaseRunEdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Models.RunEdge
        fields = (
            "values",
            "kind",
            "statuses",
        )

    def get_run(self, obj: Models.Run) -> Optional[Dict]:
        return {
            "uuid": obj.uuid.hex,
            "name": obj.name,
            "kind": obj.kind,
            "runtime": obj.runtime,
        }


class UpstreamRunEdgeSerializer(BaseRunEdgeSerializer):
    upstream = fields.SerializerMethodField()

    class Meta(BaseRunEdgeSerializer.Meta):
        fields = BaseRunEdgeSerializer.Meta.fields + ("upstream",)

    def get_upstream(self, obj: Models.RunEdge):
        if not obj.upstream_id:
            return None
        return self.get_run(obj.upstream)


class DownstreamRunEdgeSerializer(BaseRunEdgeSerializer):
    downstream = fields.SerializerMethodField()

    class Meta(BaseRunEdgeSerializer.Meta):
        fields = BaseRunEdgeSerializer.Meta.fields + ("downstream",)

    def get_downstream(self, obj: Models.RunEdge):
        if not obj.downstream_id:
            return None
        return self.get_run(obj.downstream)


class RunStatusSerializer(serializers.ModelSerializer):
    uuid = fields.UUIDField(format="hex", read_only=True)
    condition = fields.DictField(
        write_only=True, allow_empty=True, allow_null=True, required=False
    )
    force = fields.BooleanField(write_only=True, required=False)

    class Meta:
        model = Models.Run
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


class RunCloneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Models.Run
        fields = (
            "uuid",
            "name",
            "kind",
            "status",
            "runtime",
            "cloning_kind",
        )


class BaseRunSerializer(
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
    schedule_at = fields.DateTimeField(read_only=True)
    settings = fields.SerializerMethodField()

    class Meta:
        model = Models.Run
        fields = (
            "uuid",
            "name",
            "created_at",
            "updated_at",
            "started_at",
            "finished_at",
            "schedule_at",
            "wait_time",
            "duration",
            "kind",
            "runtime",
            "meta_info",
            "status",
            "pipeline",
            "original",
            "is_managed",
            "managed_by",
            "pending",
            "inputs",
            "outputs",
            "tags",
            "settings",
        )
        extra_kwargs = {
            "is_managed": {"read_only": True},
            "managed_by": {"read_only": True},
        }


class RunSerializer(
    BaseRunSerializer,
    UserMixin,
    ProjectMixin,
    ProjectOwnerMixin,
):
    owner = fields.SerializerMethodField()
    user = fields.SerializerMethodField()
    project = fields.SerializerMethodField()

    class Meta(BaseRunSerializer.Meta):
        fields = BaseRunSerializer.Meta.fields + (
            "user",
            "owner",
            "project",
        )


class BookmarkedRunSerializer(
    BaseRunSerializer, UserMixin, ResourcesMixin, BookmarkedSerializerMixin
):
    bookmarked_model = "run"

    resources = fields.SerializerMethodField()
    user = fields.SerializerMethodField()

    class Meta(BaseRunSerializer.Meta):
        fields = BaseRunSerializer.Meta.fields + (
            "user",
            "bookmarked",
            "resources",
        )


class BookmarkedTimelineRunSerializer(BookmarkedRunSerializer):
    class Meta:
        model = Models.Run
        fields = (
            "uuid",
            "name",
            "created_at",
            "updated_at",
            "started_at",
            "finished_at",
            "schedule_at",
            "wait_time",
            "duration",
            "kind",
            "runtime",
            "status",
            "tags",
            "user",
            "bookmarked",
            "pipeline",
            "original",
            "is_managed",
            "managed_by",
            "pending",
            "tags",
        )


class GraphRunSerializer(RunSerializer, UserMixin):
    graph = fields.SerializerMethodField()

    class Meta:
        model = Models.Run
        fields = (
            "uuid",
            "name",
            "created_at",
            "updated_at",
            "started_at",
            "finished_at",
            "schedule_at",
            "wait_time",
            "duration",
            "kind",
            "runtime",
            "status",
            "tags",
            "user",
            "pipeline",
            "pending",
            "graph",
        )

    def get_graph(self, obj):
        graph = self.context.get("graph", None)

        if graph is not None:
            return graph.get(obj.uuid.hex)
        return None


class RunDetailSerializer(
    RunSerializer,
    FullSettingsMixin,
    IsManagedMixin,
    ResourcesMixin,
    BookmarkedSerializerMixin,
):
    bookmarked_model = "run"
    merge = fields.BooleanField(write_only=True, required=False)
    resources = fields.SerializerMethodField()

    class Meta(RunSerializer.Meta):
        fields = RunSerializer.Meta.fields + (
            "readme",
            "description",
            "raw_content",
            "content",
            "live_state",
            "merge",
            "bookmarked",
            "resources",
        )
        extra_kwargs = {
            "content": {"read_only": True},
            "raw_content": {"read_only": True},
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs = self.check_if_entity_is_managed(attrs=attrs, entity_name="Run")
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


class OfflineRunSerializer(
    serializers.ModelSerializer,
    IsManagedMixin,
    TagsMixin,
):
    uuid = fields.UUIDField(format="hex")
    created_at = fields.DateTimeField()

    class Meta:
        model = Models.Run
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
            "managed_by",
            "inputs",
            "outputs",
            "content",
            "raw_content",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs = self.check_if_entity_is_managed(attrs=attrs, entity_name="Run")
        return attrs

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
    settings = fields.SerializerMethodField()

    class Meta:
        model = Models.Run
        fields = (
            "uuid",
            "kind",
            "name",
            "description",
            "content",
            "is_managed",
            "managed_by",
            "pending",
            "meta_info",
            "tags",
            "is_approved",
            "settings",
        )
        extra_kwargs = {
            "is_approved": {"write_only": True},
            "kind": {"read_only": True},
        }

    def get_settings(self, obj):
        build = (
            obj.upstream_runs.filter(downstream_edges__kind=V1RunEdgeKind.BUILD)
            .order_by("created_at")
            .last()
        )
        return {
            "build": {
                "name": build.name,
                "status": build.status,
                "uuid": build.uuid.hex,
            }
            if build
            else None,
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs = self.check_if_entity_is_managed(attrs=attrs, entity_name="Run")
        return attrs

    def create(self, validated_data):
        managed_by = validated_data.get("managed_by")
        if managed_by is None:
            managed_by = ManagedBy.AGENT
        content = validated_data.get("content")
        meta_info = validated_data.get("meta_info") or {}

        if managed_by is None:
            raise ValidationError("Run is not validated correctly")

        is_managed = ManagedBy.is_managed(managed_by)
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
                    managed_by=managed_by,
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
                managed_by=managed_by,
            )
