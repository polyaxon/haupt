from typing import Dict, List, Optional

from clipped.utils.lists import to_list

from haupt.db.managers.tags import denormalize_tags, normalize_tags


class TagsMixin:
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if "tags" in representation:
            representation["tags"] = normalize_tags(representation.get("tags"))
        return representation

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if "tags" in data:
            data["tags"] = denormalize_tags(data["tags"])
        return data

    @staticmethod
    def validated_tags(validated_data: Dict, tags: Optional[List[str]]):
        new_tags = validated_data.get("tags")

        if new_tags:
            new_tags = normalize_tags(new_tags)
            new_tags = to_list(new_tags, check_none=True, to_unique=True)
            validated_data["tags"] = new_tags

        if not validated_data.get("merge") or not tags or not new_tags:
            return validated_data

        tags = normalize_tags(tags)
        new_tags = tags + [tag for tag in new_tags if tag not in tags]
        validated_data["tags"] = new_tags
        return validated_data
