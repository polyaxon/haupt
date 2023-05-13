from rest_framework.relations import SlugRelatedField


class UuidSlugRelatedField(SlugRelatedField):
    def to_representation(self, obj):
        value = getattr(obj, self.slug_field)
        if value:
            return value.hex
        return value
