from rest_framework import fields, serializers

from haupt.db.defs import Models


class RunArtifactLightSerializer(serializers.ModelSerializer):
    name = fields.SerializerMethodField()
    kind = fields.SerializerMethodField()

    class Meta:
        model = Models.ArtifactLineage
        fields = ("name", "kind", "is_input")

    def get_name(self, obj):
        return obj.artifact.name

    def get_kind(self, obj):
        return obj.artifact.kind


class RunArtifactBackwardCompatibleSerializer(RunArtifactLightSerializer):
    state = fields.SerializerMethodField()
    path = fields.SerializerMethodField()
    summary = fields.SerializerMethodField()

    class Meta(RunArtifactLightSerializer.Meta):
        fields = RunArtifactLightSerializer.Meta.fields + (
            "path",
            "summary",
            "state",
        )

    def get_state(self, obj):
        value = obj.artifact.state
        if value:
            return value.hex
        return value

    def get_path(self, obj):
        return obj.artifact.path

    def get_summary(self, obj):
        return obj.artifact.summary


class RunArtifactSerializer(RunArtifactBackwardCompatibleSerializer):
    run = fields.SerializerMethodField()
    meta_info = fields.SerializerMethodField()

    class Meta(RunArtifactBackwardCompatibleSerializer.Meta):
        fields = RunArtifactBackwardCompatibleSerializer.Meta.fields + (
            "run",
            "meta_info",
        )

    def get_run(self, obj):
        run = self.context.get("run")
        if not run:
            run = obj.run
        if run:
            return run.uuid.hex

    def get_meta_info(self, obj):
        run = self.context.get("run")
        if not run:
            run = obj.run
        if run:
            return {"run": {"name": run.name, "uuid": run.uuid.hex}}


class RunArtifactNameSerializer(serializers.ModelSerializer):
    name = fields.SerializerMethodField()

    class Meta:
        model = Models.ArtifactLineage
        fields = ("name",)

    def get_name(self, obj):
        return obj.artifact.name
