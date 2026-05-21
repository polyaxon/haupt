import base64
import binascii
import hashlib
import struct
from typing import Optional, Tuple

from django.conf import settings
from django.db import models
from django.utils import timezone

from haupt.db.abstracts.diff import DiffModel
from haupt.db.abstracts.nameable import NameableModel
from haupt.db.abstracts.uid import UuidModel


ALLOWED_PUBLIC_KEY_TYPES = {"ssh-ed25519"}
MAX_NORMALIZED_PUBLIC_KEY_LENGTH = 8192


class UserSshKeyConflict(ValueError):
    pass


def _decode_key_body(key_body: str) -> bytes:
    try:
        return base64.b64decode(key_body.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as e:
        raise ValueError("SSH public key body is not valid base64.") from e


def _validate_key_blob_type(key_type: str, key_blob: bytes):
    if len(key_blob) < 4:
        raise ValueError("SSH public key blob is malformed.")
    type_length = struct.unpack(">I", key_blob[:4])[0]
    type_end = 4 + type_length
    if type_end > len(key_blob):
        raise ValueError("SSH public key blob is malformed.")
    try:
        blob_key_type = key_blob[4:type_end].decode("ascii")
    except UnicodeDecodeError as e:
        raise ValueError("SSH public key blob type is malformed.") from e
    if blob_key_type != key_type:
        raise ValueError("SSH public key type does not match key blob.")


def fingerprint_public_key_body(key_body: str) -> str:
    key_blob = _decode_key_body(key_body)
    digest = hashlib.sha256(key_blob).digest()
    return "SHA256:{}".format(base64.b64encode(digest).decode("ascii").rstrip("="))


def normalize_public_key(raw: str) -> Tuple[str, str, str]:
    """Returns (key_type, key_body_b64, comment)."""
    if not isinstance(raw, str):
        raise ValueError("SSH public key must be a string.")

    value = raw.strip()
    if not value:
        raise ValueError("SSH public key is required.")
    if "\n" in value or "\r" in value:
        raise ValueError("SSH public key must contain exactly one line.")

    parts = value.split(None, 2)
    if len(parts) < 2:
        raise ValueError("SSH public key is malformed.")

    key_type, key_body = parts[:2]
    comment = parts[2] if len(parts) == 3 else ""

    if key_type not in ALLOWED_PUBLIC_KEY_TYPES:
        raise ValueError("SSH public key type is not supported.")
    if any(ord(char) < 32 or ord(char) == 127 for char in comment):
        raise ValueError("SSH public key comment contains control characters.")

    key_blob = _decode_key_body(key_body)
    _validate_key_blob_type(key_type=key_type, key_blob=key_blob)

    normalized = "{} {}{}".format(
        key_type,
        key_body,
        " {}".format(comment) if comment else "",
    )
    if len(normalized.encode("utf-8")) > MAX_NORMALIZED_PUBLIC_KEY_LENGTH:
        raise ValueError("SSH public key is too large.")

    return key_type, key_body, comment


def _format_public_key(key_type: str, key_body: str, comment: str) -> str:
    if comment:
        return "{} {} {}".format(key_type, key_body, comment)
    return "{} {}".format(key_type, key_body)


class UserSshKeyManager(models.Manager):
    def register(
        self,
        user,
        public_key: str,
        name: Optional[str] = None,
    ):
        """Register a key. Returns (key, created)."""
        name = name or None
        user_id = user.id if user else None
        key_type, key_body, comment = normalize_public_key(public_key)
        fingerprint = fingerprint_public_key_body(key_body)
        normalized_public_key = _format_public_key(
            key_type=key_type,
            key_body=key_body,
            comment=comment,
        )
        existing = self.filter(fingerprint=fingerprint).first()
        if existing:
            if existing.user_id != user_id:
                raise UserSshKeyConflict(
                    "SSH public key is already registered to another user."
                )
            if existing.revoked_at is None:
                return existing, False
            existing.revoked_at = None
            existing.public_key = normalized_public_key
            if name:
                existing.name = name
            existing.save(
                update_fields=["revoked_at", "public_key", "name", "updated_at"]
            )
            return existing, False

        return (
            self.create(
                user=user,
                name=name,
                key_type=key_type,
                public_key=normalized_public_key,
                fingerprint=fingerprint,
            ),
            True,
        )

    def revoke(self, user, key_uuid) -> None:
        """Revoke a key. Raises DoesNotExist if not owned by user."""
        key = self.get(uuid=key_uuid, user=user)
        if key.revoked_at is None:
            key.revoked_at = timezone.now()
            key.save(update_fields=["revoked_at", "updated_at"])

    def lookup_by_fingerprint(self, fingerprint: str, query_user: bool = False):
        query = self.filter(fingerprint=fingerprint, revoked_at__isnull=True)
        if query_user:
            query = query.select_related("user")
        return query.first()

    def touch_last_used(self, key) -> None:
        key.last_used_at = timezone.now()
        key.save(update_fields=["last_used_at", "updated_at"])


class BaseUserSshKey(UuidModel, DiffModel, NameableModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
    )
    key_type = models.CharField(max_length=32)
    public_key = models.TextField()
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = UserSshKeyManager()

    class Meta:
        abstract = True
        app_label = "db"
        db_table = "db_usersshkey"

    def __str__(self) -> str:
        return "UserSshKey <{}>".format(self.fingerprint)
