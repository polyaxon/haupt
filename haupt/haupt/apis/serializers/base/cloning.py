#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from typing import Dict, Optional

from rest_framework import serializers

from haupt.db.abstracts.runs import BaseRun


class CloningMixin(serializers.Serializer):
    def get_original(self, obj: BaseRun) -> Optional[Dict]:
        if not obj.original_id:
            return None

        return {
            "uuid": obj.original.uuid.hex,
            "name": obj.original.name,
            "kind": obj.cloning_kind,
        }
