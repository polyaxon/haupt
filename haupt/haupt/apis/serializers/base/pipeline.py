#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

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
