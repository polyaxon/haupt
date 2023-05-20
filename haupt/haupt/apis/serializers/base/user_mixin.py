from rest_framework import serializers


class UserMixin(serializers.Serializer):
    def get_user(self, obj):
        return obj.user.username if obj.user_id else None


class UserEmailMixin(serializers.Serializer):
    def get_user_email(self, obj):
        return obj.user.email if obj.user_id else None
