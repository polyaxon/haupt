from typing import List, Optional

from haupt.db.managers.artifacts import set_artifacts
from polyaxon.compiler import resolver
from polyaxon.compiler.lineage import collect_lineage_artifacts_path
from polyaxon.constants.metadata import (
    META_COPY_ARTIFACTS,
    META_DESTINATION_IMAGE,
    META_IS_EXTERNAL,
    META_REWRITE_PATH,
    META_UPLOAD_ARTIFACTS,
)
from polyaxon.polyaxonfile import CompiledOperationSpecification
from polyaxon.polyflow import V1Init
from polyaxon.schemas import V1RunPending
from polyaxon.schemas.types import V1ArtifactsType


class PlatformResolver(resolver.BaseResolver):
    def resolve_params(self):
        self.params = self.run.params or {}

    def resolve_io(self):
        if self.compiled_operation.inputs:
            self.run.inputs = {
                io.name: io.value for io in self.compiled_operation.inputs
            }
        if self.compiled_operation.outputs:
            self.run.outputs = {
                io.name: io.value for io in self.compiled_operation.outputs
            }

    def _get_meta_artifacts_presets(self) -> List:
        if not self.run.meta_info or META_COPY_ARTIFACTS not in self.run.meta_info:
            return []

        artifacts = self.run.meta_info.pop(META_COPY_ARTIFACTS)
        artifacts = V1ArtifactsType.read(artifacts)

        def get_relative_to_run_artifacts(v: str):
            paths = v.split("/")[1:]
            paths = ["{{ globals.run_artifacts_path }}"] + paths
            return "/".join(paths)

        # Populate all paths
        if artifacts.dirs:
            artifacts.dirs = [
                [d, get_relative_to_run_artifacts(d)] for d in artifacts.dirs
            ]
        if artifacts.files:
            artifacts.files = [
                [d, get_relative_to_run_artifacts(d)] for d in artifacts.files
            ]
        init = V1Init.construct(artifacts=artifacts)
        return [{"runPatch": {"init": [init.to_dict()]}}]

    def _get_meta_destination_image(self) -> Optional[str]:
        meta_info = self.run.meta_info or {}
        return meta_info.get(META_DESTINATION_IMAGE)

    def resolve_presets(self):
        for preset in self._get_meta_artifacts_presets():
            self.compiled_operation = CompiledOperationSpecification.apply_preset(
                config=self.compiled_operation, preset=preset
            )

    def _persist_artifacts(self):
        if self.artifacts:
            set_artifacts(self.run, self.artifacts)

    def _resolve_artifacts_lineage_state(self):
        self.artifacts = self.artifacts or []
        # Check upload and add it as a lineage
        if self.run.meta_info and META_UPLOAD_ARTIFACTS in self.run.meta_info:
            artifacts_path = self.run.meta_info[META_UPLOAD_ARTIFACTS]
            if artifacts_path:
                upload_artifact = collect_lineage_artifacts_path(artifacts_path)
                self.artifacts.append(upload_artifact)
        self._persist_artifacts()

    def _check_approval(self):
        if self.compiled_operation.is_approved is False and self.run.pending is None:
            self.run.pending = V1RunPending.APPROVAL
            return True
        return False

    def persist_state(self):
        self.run.content = self.compiled_operation.to_json()
        if (
            self.compiled_operation.is_service_run
            and self.compiled_operation.run.rewrite_path
        ):
            self.run.meta_info[META_REWRITE_PATH] = True
        if (
            self.compiled_operation.is_service_run
            and self.compiled_operation.run.is_external
        ):
            self.run.meta_info[META_IS_EXTERNAL] = True
        update_fields = ["content", "inputs", "outputs", "meta_info"]
        if self._check_approval():
            update_fields.append("pending")
        self.run.save(update_fields=update_fields)
        self._resolve_artifacts_lineage_state()
