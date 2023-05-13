from collections.abc import Mapping
from typing import Dict, List, Optional

from clipped.utils.lists import to_list

from django.conf import settings


class TagsMixin:
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if settings.DB_ENGINE_NAME == "sqlite" and isinstance(
            representation.get("tags"), Mapping
        ):
            representation["tags"] = list((representation.get("tags") or {}).keys())
        return representation

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if settings.DB_ENGINE_NAME == "sqlite" and "tags" in data:
            data["tags"] = {t: "" for t in data["tags"]}
        return data

    @staticmethod
    def validated_tags(validated_data: Dict, tags: Optional[List[str]]):
        new_tags = validated_data.get("tags")

        if new_tags:
            if settings.DB_ENGINE_NAME == "sqlite" and isinstance(new_tags, Mapping):
                new_tags = list(new_tags.keys())
            new_tags = to_list(new_tags, check_none=True, to_unique=True)
            validated_data["tags"] = new_tags

        if not validated_data.get("merge") or not tags or not new_tags:
            # This is the default behavior
            return validated_data

        if settings.DB_ENGINE_NAME == "sqlite" and isinstance(tags, Mapping):
            tags = list(tags.keys())
        new_tags = tags + [tag for tag in new_tags if tag not in tags]
        validated_data["tags"] = new_tags
        return validated_data
