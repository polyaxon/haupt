from rest_framework import fields, serializers

from haupt.db.defs import Models


class UserSshKeySerializer(serializers.ModelSerializer):
    uuid = fields.UUIDField(format="hex", read_only=True)

    class Meta:
        model = Models.UserSshKey
        fields = (
            "uuid",
            "name",
            "key_type",
            "fingerprint",
            "created_at",
            "updated_at",
            "last_used_at",
            "revoked_at",
        )


class UserSshKeyCreateResponseSerializer(UserSshKeySerializer):
    class Meta(UserSshKeySerializer.Meta):
        fields = UserSshKeySerializer.Meta.fields + ("public_key",)


class UserSshKeyCreateSerializer(serializers.ModelSerializer):
    public_key = serializers.CharField()

    class Meta:
        model = Models.UserSshKey
        fields = ("public_key", "name")
        extra_kwargs = {
            "name": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
        }
