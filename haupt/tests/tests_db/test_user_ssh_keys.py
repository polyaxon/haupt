import base64
import struct

from django.test import TestCase

from haupt.db.abstracts.user_ssh_keys import (
    MAX_NORMALIZED_PUBLIC_KEY_LENGTH,
    UserSshKeyConflict,
    fingerprint_public_key_body,
    normalize_public_key,
)
from haupt.db.factories.users import UserFactory
from haupt.db.managers.tags import normalize_tags
from haupt.db.models.user_ssh_keys import UserSshKey


KEY_BODY = "AAAAC3NzaC1lZDI1NTE5AAAAIAABAgMEBQYHCAkKCwwNDg8QERITFBUWFxgZGhscHR4f"
PUBLIC_KEY = "ssh-ed25519 {} user@example.com".format(KEY_BODY)
PUBLIC_KEY_NO_COMMENT = "ssh-ed25519 {}".format(KEY_BODY)
PUBLIC_KEY_FINGERPRINT = "SHA256:ZkAslGjFiUHdGf/WUL8rQvkib4PTvQatUV0OUQSncCA"


def _key_body_with_blob_type(key_type: str) -> str:
    blob_type = key_type.encode("ascii")
    key_blob = struct.pack(">I", len(blob_type)) + blob_type + b"payload"
    return base64.b64encode(key_blob).decode("ascii")


class TestUserSshKeyNormalization(TestCase):
    def test_normalize_public_key_round_trips_canonical_line(self):
        key_type, key_body, comment = normalize_public_key(PUBLIC_KEY)

        assert key_type == "ssh-ed25519"
        assert key_body == KEY_BODY
        assert comment == "user@example.com"

    def test_normalize_public_key_accepts_no_comment(self):
        key_type, key_body, comment = normalize_public_key(PUBLIC_KEY_NO_COMMENT)

        assert key_type == "ssh-ed25519"
        assert key_body == KEY_BODY
        assert comment == ""

    def test_normalize_public_key_preserves_comment_spaces(self):
        key_type, key_body, comment = normalize_public_key(
            "ssh-ed25519 {} user name on host".format(KEY_BODY)
        )

        assert key_type == "ssh-ed25519"
        assert key_body == KEY_BODY
        assert comment == "user name on host"

    def test_normalize_public_key_rejects_multi_line_input(self):
        with self.assertRaises(ValueError):
            normalize_public_key("{}\n{}".format(PUBLIC_KEY, PUBLIC_KEY))

    def test_normalize_public_key_rejects_unsupported_type(self):
        with self.assertRaises(ValueError):
            normalize_public_key("ssh-rsa {} user@example.com".format(KEY_BODY))

    def test_normalize_public_key_rejects_malformed_base64(self):
        with self.assertRaises(ValueError):
            normalize_public_key("ssh-ed25519 not-base64 user@example.com")

    def test_normalize_public_key_rejects_type_prefix_mismatch(self):
        rsa_body = _key_body_with_blob_type("ssh-rsa")

        with self.assertRaises(ValueError):
            normalize_public_key("ssh-ed25519 {} user@example.com".format(rsa_body))

    def test_normalize_public_key_rejects_options_prefix(self):
        with self.assertRaises(ValueError):
            normalize_public_key(
                'command="echo no" ssh-ed25519 {} user@example.com'.format(KEY_BODY)
            )

    def test_normalize_public_key_rejects_control_char_in_comment(self):
        with self.assertRaises(ValueError):
            normalize_public_key("ssh-ed25519 {} bad\x1fcomment".format(KEY_BODY))

    def test_normalize_public_key_rejects_oversized_input(self):
        with self.assertRaises(ValueError):
            normalize_public_key(
                "ssh-ed25519 {} {}".format(
                    KEY_BODY,
                    "x" * MAX_NORMALIZED_PUBLIC_KEY_LENGTH,
                )
            )

    def test_fingerprint_public_key_body_matches_openssh_sha256_format(self):
        assert fingerprint_public_key_body(KEY_BODY) == PUBLIC_KEY_FINGERPRINT


class TestUserSshKeyManager(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def register(
        self,
        user=None,
        public_key=PUBLIC_KEY,
        name="laptop",
        description=None,
        tags=None,
    ):
        key, _ = UserSshKey.objects.register(
            user=self.user if user is None else user,
            public_key=public_key,
            name=name,
            description=description,
            tags=tags,
        )
        return key

    def test_register_creates_user_ssh_key(self):
        key, created = UserSshKey.objects.register(
            user=self.user,
            public_key=PUBLIC_KEY,
            name="macbook-pro",
            description="Work laptop",
            tags=["work", "laptop"],
        )

        assert created is True
        assert key.user == self.user
        assert key.uuid
        assert key.name == "macbook-pro"
        assert key.description == "Work laptop"
        assert normalize_tags(key.tags) == ["work", "laptop"]
        assert key.key_type == "ssh-ed25519"
        assert key.public_key == PUBLIC_KEY
        assert key.fingerprint == PUBLIC_KEY_FINGERPRINT
        assert key.revoked_at is None
        assert key.last_used_at is None

    def test_register_requires_name(self):
        with self.assertRaises(ValueError):
            UserSshKey.objects.register(
                user=self.user, public_key=PUBLIC_KEY, name=""
            )

    def test_register_existing_active_key_for_same_user_is_idempotent(self):
        key = self.register(
            name="laptop",
            description="Original",
            tags=["original"],
        )
        same_key, created = UserSshKey.objects.register(
            user=self.user,
            public_key=PUBLIC_KEY,
            name="new-name",
            description="Changed",
            tags=["changed"],
        )

        assert created is False
        assert same_key == key
        assert UserSshKey.objects.count() == 1
        key.refresh_from_db()
        assert key.name == "laptop"
        assert key.description == "Original"
        assert normalize_tags(key.tags) == ["original"]
        assert key.last_used_at is None

    def test_register_existing_key_for_another_user_raises_conflict(self):
        self.register()
        other_user = UserFactory()

        with self.assertRaises(UserSshKeyConflict):
            UserSshKey.objects.register(
                user=other_user, public_key=PUBLIC_KEY, name="other"
            )
        assert UserSshKey.objects.count() == 1

    def test_register_existing_key_for_nullable_user_raises_conflict(self):
        self.register()

        with self.assertRaises(UserSshKeyConflict):
            UserSshKey.objects.register(
                user=None, public_key=PUBLIC_KEY, name="local"
            )
        assert UserSshKey.objects.count() == 1

    def test_register_existing_nullable_user_key_for_user_raises_conflict(self):
        key, created = UserSshKey.objects.register(
            user=None, public_key=PUBLIC_KEY, name="local"
        )

        assert created is True
        with self.assertRaises(UserSshKeyConflict):
            UserSshKey.objects.register(
                user=self.user, public_key=PUBLIC_KEY, name="laptop"
            )
        assert UserSshKey.objects.count() == 1

    def test_register_existing_nullable_user_key_is_idempotent(self):
        key, created = UserSshKey.objects.register(
            user=None, public_key=PUBLIC_KEY, name="local"
        )
        same_key, same_created = UserSshKey.objects.register(
            user=None, public_key=PUBLIC_KEY, name="other-name"
        )

        assert created is True
        assert same_created is False
        assert same_key == key
        assert UserSshKey.objects.count() == 1

    def test_register_revoked_key_for_same_user_unrevokes_existing_row(self):
        key = self.register()
        UserSshKey.objects.revoke(user=self.user, key_uuid=key.uuid)
        key.refresh_from_db()
        assert key.revoked_at is not None

        same_key, created = UserSshKey.objects.register(
            user=self.user,
            public_key=PUBLIC_KEY_NO_COMMENT,
            name="restored",
            description="Restored laptop",
            tags=["restored"],
        )

        assert created is False
        assert same_key == key
        assert UserSshKey.objects.count() == 1
        same_key.refresh_from_db()
        assert same_key.revoked_at is None
        assert same_key.name == "restored"
        assert same_key.description == "Restored laptop"
        assert normalize_tags(same_key.tags) == ["restored"]
        assert same_key.public_key == PUBLIC_KEY_NO_COMMENT

    def test_lookup_by_fingerprint_returns_only_active_keys(self):
        key = self.register()

        assert UserSshKey.objects.lookup_by_fingerprint(PUBLIC_KEY_FINGERPRINT) == key

        UserSshKey.objects.revoke(user=self.user, key_uuid=key.uuid)

        assert UserSshKey.objects.lookup_by_fingerprint(PUBLIC_KEY_FINGERPRINT) is None

    def test_revoke_rejects_keys_owned_by_another_user(self):
        key = self.register()
        other_user = UserFactory()

        with self.assertRaises(UserSshKey.DoesNotExist):
            UserSshKey.objects.revoke(user=other_user, key_uuid=key.uuid)

    def test_revoke_already_revoked_key_is_noop(self):
        key = self.register()

        UserSshKey.objects.revoke(user=self.user, key_uuid=key.uuid)
        key.refresh_from_db()
        revoked_at = key.revoked_at

        UserSshKey.objects.revoke(user=self.user, key_uuid=key.uuid)
        key.refresh_from_db()

        assert key.revoked_at == revoked_at

    def test_touch_last_used_sets_timestamp(self):
        key = self.register()

        UserSshKey.objects.touch_last_used(key)

        key.refresh_from_db()
        assert key.last_used_at is not None
