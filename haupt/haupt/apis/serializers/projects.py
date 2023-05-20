from rest_framework import fields, serializers
from rest_framework.exceptions import ValidationError

from django.db import IntegrityError

from haupt.apis.serializers.base.bookmarks_mixin import BookmarkedSerializerMixin
from haupt.apis.serializers.base.tags import TagsMixin
from haupt.db.defs import Models


class ProjectNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Models.Project
        fields = ("name",)


class ProjectSerializer(TagsMixin, serializers.ModelSerializer):
    uuid = fields.UUIDField(format="hex", read_only=True)

    class Meta:
        model = Models.Project
        fields = (
            "uuid",
            "name",
            "description",
            "tags",
            "created_at",
            "updated_at",
        )


class BookmarkedProjectSerializer(ProjectSerializer, BookmarkedSerializerMixin):
    bookmarked_model = "project"

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ("bookmarked",)


class ProjectDetailSerializer(BookmarkedProjectSerializer):
    class Meta(BookmarkedProjectSerializer.Meta):
        fields = BookmarkedProjectSerializer.Meta.fields + (
            "readme",
            "live_state",
            "bookmarked",
        )

    def update(self, instance, validated_data):
        validated_data = self.validated_tags(
            validated_data=validated_data, tags=instance.tags
        )

        try:
            return super().update(instance=instance, validated_data=validated_data)
        except IntegrityError:
            raise ValidationError(
                f"A project with name {validated_data['name']} already exists."
            )


class ProjectCreateSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ("readme",)

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise ValidationError(
                f"A project with name {validated_data['name']} already exists."
            )
