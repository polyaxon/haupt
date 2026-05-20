from rest_framework.permissions import IsAuthenticated

from django.conf import settings

from haupt.apis.serializers.user_ssh_keys import (
    UserSshKeyCreateSerializer,
    UserSshKeySerializer,
)
from haupt.common.apis.regex import UUID_KEY
from haupt.common.endpoints.base import BaseEndpoint, DestroyEndpoint, ListEndpoint
from haupt.db.abstracts.user_ssh_keys import (
    fingerprint_public_key_body,
    normalize_public_key,
)
from haupt.db.defs import Models


MAX_SSH_KEYS_PER_USER = 50


def get_ssh_key_user(request):
    if settings.HAS_ORG_MANAGEMENT:
        return request.user
    return None


class UserSshKeyMixin:
    permission_classes = (IsAuthenticated,) if settings.HAS_ORG_MANAGEMENT else ()
    queryset = Models.UserSshKey.objects
    lookup_field = UUID_KEY

    def get_queryset(self):
        return (
            Models.UserSshKey.objects.filter(
                user=get_ssh_key_user(self.request),
                revoked_at__isnull=True,
            )
            .only(
                "id",
                "uuid",
                "user_id",
                "name",
                "key_type",
                "fingerprint",
                "public_key",
                "created_at",
                "updated_at",
                "last_used_at",
                "revoked_at",
            )
            .order_by("-created_at")
        )


class UserSshKeyListEndpoint(UserSshKeyMixin, BaseEndpoint, ListEndpoint):
    ALLOWED_METHODS = ["GET", "POST"]
    serializer_class_mapping = {
        "GET": UserSshKeySerializer,
        "POST": UserSshKeyCreateSerializer,
    }

    def check_key_cap(self, user, public_key: str):
        if user is None:
            return None

        _, key_body, _ = normalize_public_key(public_key)
        fingerprint = fingerprint_public_key_body(key_body)
        active_count = Models.UserSshKey.objects.filter(
            user=user,
            revoked_at__isnull=True,
        ).count()
        if active_count < MAX_SSH_KEYS_PER_USER:
            return None

        existing = Models.UserSshKey.objects.filter(
            fingerprint=fingerprint,
        ).first()
        if existing and existing.user_id != user.id:
            return None
        if existing and existing.revoked_at is None:
            return None

        raise ValueError("You have reached the maximum number of SSH keys.")


class UserSshKeyDetailEndpoint(UserSshKeyMixin, BaseEndpoint, DestroyEndpoint):
    ALLOWED_METHODS = ["DELETE"]
    serializer_class = UserSshKeySerializer
