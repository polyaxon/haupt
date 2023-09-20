from rest_framework import fields, serializers
from rest_framework.exceptions import ValidationError

from django.conf import settings
from django.db import IntegrityError
from django.db.models import Count

from haupt.apis.serializers.artifacts import (
    RunArtifactBackwardCompatibleSerializer,
    RunArtifactSerializer,
)
from haupt.apis.serializers.base.owner_mixin import ProjectOwnerMixin
from haupt.apis.serializers.base.project import ProjectMixin
from haupt.apis.serializers.base.tags import TagsMixin
from haupt.apis.serializers.base.uuid_slug_related_field import UuidSlugRelatedField
from haupt.db.defs import Models
from haupt.db.managers.versions import get_component_version_state
from polyaxon._config.spec import ConfigSpec
from polyaxon._constants.metadata import META_IS_PROMOTED
from polyaxon._polyaxonfile import ComponentSpecification
from polyaxon.schemas import V1ProjectVersionKind


class ProjectVersionStageSerializer(serializers.ModelSerializer):
    uuid = fields.UUIDField(format="hex", read_only=True)
    condition = fields.DictField(
        write_only=True, allow_empty=True, allow_null=True, required=False
    )

    class Meta:
        model = Models.ProjectVersion
        fields = ("uuid", "stage", "condition", "stage_conditions")
        extra_kwargs = {
            "stage": {"read_only": True},
            "stage_conditions": {"read_only": True},
        }


class ProjectVersionNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Models.ProjectVersion
        fields = ("name",)


class ProjectVersionSerializer(serializers.ModelSerializer):
    uuid = fields.UUIDField(format="hex", read_only=True)
    state = fields.UUIDField(format="hex", read_only=True)

    class Meta:
        model = Models.ProjectVersion
        fields = (
            "uuid",
            "name",
            "description",
            "tags",
            "created_at",
            "updated_at",
            "stage",
            "state",
            "kind",
        )

    def _validate_run(self, run, owner):
        org_filters = {"project__owner": owner} if settings.HAS_ORG_MANAGEMENT else {}
        if run and Models.Run.objects.filter(**org_filters, uuid=run).count() != 1:
            raise ValidationError(
                f"The run({run}) does not exist,"
                f"not valid,"
                f"or not part of this organization."
            )


class ProjectVersionDetailSerializer(
    ProjectVersionSerializer,
    ProjectMixin,
    ProjectOwnerMixin,
    TagsMixin,
):
    meta_info = fields.SerializerMethodField()
    owner = fields.SerializerMethodField()
    project = fields.SerializerMethodField()
    run = UuidSlugRelatedField(
        slug_field="uuid",
        queryset=Models.Run.objects.select_related("project").only(
            "id", "name", "project__id", "project__name"
        ),
        required=False,
        allow_null=True,
    )
    artifacts = serializers.SerializerMethodField()

    _LINEAGE_SERIALIZER = RunArtifactSerializer

    class Meta(ProjectVersionSerializer.Meta):
        fields = ProjectVersionSerializer.Meta.fields + (
            "owner",
            "project",
            "content",
            "readme",
            "run",
            "artifacts",
            "meta_info",
        )

    def get_meta_info(self, obj: Models.ProjectVersion):
        info = {}
        if obj.run_id:
            info["run"] = {
                "project": obj.run.project.name,
                "name": obj.run.name,
                "uuid": obj.run.uuid.hex,
            }
        if settings.HAS_ORG_MANAGEMENT and obj.connection_id:
            info["connection"] = {
                "uuid": obj.connection.uuid.hex,
                "name": "{}/{}".format(obj.connection.agent.name, obj.connection.name),
            }

        lineage = obj.lineage.all()
        compatibility = self.context.get("compatibility")

        if compatibility in ["old", "both"]:
            artifacts = [
                RunArtifactBackwardCompatibleSerializer(a).data for a in lineage
            ]
            if artifacts:
                info["artifacts"] = artifacts
        if not compatibility or compatibility in ["new", "both"]:
            lineage = [
                self._LINEAGE_SERIALIZER(a, context={"run": obj.run}).data
                for a in lineage
            ]
            if lineage:
                info["lineage"] = lineage
        return info

    def get_artifacts(self, obj: Models.ProjectVersion):
        return list(obj.lineage.values_list("artifact__name", flat=True))

    def validated_content(self, kind, content):
        if kind == V1ProjectVersionKind.COMPONENT:
            if not content:
                raise serializers.ValidationError(
                    "the `content` is required to create a component version."
                )
            try:
                return ComponentSpecification.read(content)
            except Exception as e:
                raise serializers.ValidationError(e)
        else:
            if content:
                try:
                    return ConfigSpec.read_from(content, config_type=".yaml")
                except Exception as e:
                    raise serializers.ValidationError(e)

    def validated_project_run(self, project, run):
        if not run or run.project_id == project.id:
            return

        if settings.HAS_ORG_MANAGEMENT and run.project.owner_id != project.owner_id:
            raise ValidationError(
                "The run referenced is not accessible from your organization."
            )

        projects = set(project.projects.values_list("id", flat=True))
        if projects:
            projects.add(project.id)
        if projects and run.project_id not in projects:
            raise ValidationError(
                "The run referenced is not accessible from this project."
            )

    def validated_project_connection(self, project, connection):
        if not connection:
            return

        if connection.owner_id != project.owner_id:
            raise ValidationError(
                "The connection referenced is not accessible from your organization."
            )

        connections = set(project.connections.values_list("id", flat=True))
        if connections and connection.id not in connections:
            raise ValidationError(
                "The connection referenced is not accessible from this project."
            )

    def validated_project_artifacts(self, run, artifacts):
        if artifacts is None:
            return None
        if not artifacts:
            return artifacts
        if not run:
            raise ValidationError(
                "A run is required to link the artifacts: `{}`.".format(artifacts)
            )
        artifacts = set(artifacts)
        found = run.artifacts_lineage.filter(artifact__name__in=artifacts).values_list(
            "id", "artifact_id", "artifact__name"
        )
        missing = artifacts - set(f[2] for f in found)
        if missing:
            raise ValidationError(
                "Some artifacts could not be found: `{}`.".format(missing)
            )
        return set(f[0] for f in found)

    def update(self, instance, validated_data):
        kind = validated_data.pop("c" "kind", None)
        if kind and instance.kind != kind:
            raise ValidationError("Changing a version kind is not permitted.")
        content = validated_data.get("content")
        if content:
            json_content = self.validated_content(instance.kind, content)
            if kind == V1ProjectVersionKind.COMPONENT:
                validated_data["state"] = get_component_version_state(
                    component=json_content
                )
        current_run_id = instance.run_id
        validated_data = self.validated_tags(
            validated_data=validated_data, tags=instance.tags
        )
        self.validated_project_run(instance.project, validated_data.get("run"))
        if settings.HAS_ORG_MANAGEMENT:
            self.validated_project_connection(
                instance.project, validated_data.get("connection")
            )
        lineage = self.validated_project_artifacts(
            validated_data.get("run", instance.run if instance.run_id else None),
            validated_data.pop("artifacts", None),
        )

        try:
            instance = super().update(instance=instance, validated_data=validated_data)
        except IntegrityError:
            raise ValidationError(
                f"A version with name {validated_data['name']} already exists "
                f"on the requested project."
            )

        if lineage is not None:
            instance.lineage.set(lineage)

        new_run_id = instance.run_id
        if current_run_id != new_run_id:
            runs = Models.Run.restorable.filter(id__in=[current_run_id, new_run_id])
            runs = runs.annotate(versions_count=Count("versions"))
            runs = runs.only("id", "meta_info")
            runs_by_id = {run.id: run for run in runs}
            if (
                current_run_id
                and current_run_id in runs_by_id
                and runs_by_id[current_run_id].versions_count == 0
            ):
                runs_by_id[current_run_id].meta_info.pop(META_IS_PROMOTED, None)
            if (
                new_run_id
                and new_run_id in runs_by_id
                and not runs_by_id[new_run_id].meta_info.get(META_IS_PROMOTED)
            ):
                runs_by_id[new_run_id].meta_info[META_IS_PROMOTED] = True
            Models.Run.objects.bulk_update(runs, ["meta_info"])

        return instance

    def create(self, validated_data):
        kind = None
        if hasattr(self, "get_kind"):
            kind = self.get_kind()
        if not kind:
            kind = validated_data.pop("kind", None)
        if not kind:
            raise ValidationError("A project version kind is required.")
        validated_data["kind"] = kind
        content = validated_data.get("content")
        json_content = self.validated_content(kind, content)
        if kind == V1ProjectVersionKind.COMPONENT:
            validated_data["state"] = get_component_version_state(
                component=json_content
            )

        project = validated_data["project"]
        self.validated_project_run(project, validated_data.get("run"))
        if settings.HAS_ORG_MANAGEMENT:
            self.validated_project_connection(project, validated_data.get("connection"))
        lineage = self.validated_project_artifacts(
            validated_data.get("run"), validated_data.pop("artifacts", None)
        )
        try:
            instance = super().create(validated_data)
        except IntegrityError:
            raise ValidationError(
                f"A version with name {validated_data['name']} already exists "
                f"on the requested project."
            )

        if lineage is not None:
            instance.lineage.set(lineage)

        if instance.run_id:
            run = Models.Run.restorable.only("id", "meta_info").get(id=instance.run_id)
            if not run.meta_info.get(META_IS_PROMOTED):
                run.meta_info[META_IS_PROMOTED] = True
                run.save(update_fields=["meta_info"])

        return instance


class ProjectWriteVersionDetailSerializer(ProjectVersionDetailSerializer):
    kind = fields.SerializerMethodField()
    artifacts = serializers.ListField(
        child=serializers.CharField(allow_null=True, required=False),
        allow_null=True,
        required=False,
        write_only=True,
    )


class ComponentVersionDetailSerializer(ProjectWriteVersionDetailSerializer):
    def get_kind(self, obj=None):
        return V1ProjectVersionKind.COMPONENT


class ModelVersionDetailSerializer(ProjectWriteVersionDetailSerializer):
    def get_kind(self, obj=None):
        return V1ProjectVersionKind.MODEL


class ArtifactVersionDetailSerializer(ProjectWriteVersionDetailSerializer):
    def get_kind(self, obj=None):
        return V1ProjectVersionKind.ARTIFACT
