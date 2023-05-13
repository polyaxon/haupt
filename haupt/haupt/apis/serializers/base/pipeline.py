from rest_framework import serializers

from haupt.db.abstracts.runs import BaseRun


class PipelineMixin(serializers.Serializer):
    def get_pipeline(self, obj: BaseRun) -> str:
        if not obj.pipeline_id:
            return None

        return {
            "uuid": obj.pipeline.uuid.hex,
            "name": obj.pipeline.name,
            "kind": obj.pipeline.kind,
        }
