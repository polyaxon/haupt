import base64
import struct
import uuid

from rest_framework import status

from haupt.db.factories.users import UserFactory
from haupt.db.models.user_ssh_keys import UserSshKey
from polyaxon.api import API_V1
from tests.base.case import BaseTest


KEY_BODY = "AAAAC3NzaC1lZDI1NTE5AAAAIAABAgMEBQYHCAkKCwwNDg8QERITFBUWFxgZGhscHR4f"
PUBLIC_KEY = "ssh-ed25519 {} user@example.com".format(KEY_BODY)


def _public_key(index: int) -> str:
    key_type = b"ssh-ed25519"
    key = bytes((index + value) % 256 for value in range(32))
    blob = (
        struct.pack(">I", len(key_type))
        + key_type
        + struct.pack(">I", len(key))
        + key
    )
    return "ssh-ed25519 {} user-{}@example.com".format(
        base64.b64encode(blob).decode("ascii"),
        index,
    )


def _results(response):
    return response.data["results"] if "results" in response.data else response.data


class TestUserSshKeyViewsV1(BaseTest):
    def setUp(self):
        super().setUp()
        self.url = "/{}/users/ssh-keys".format(API_V1)

    def register_key(self, public_key=PUBLIC_KEY, user=None, name=None):
        key, _ = UserSshKey.objects.register(
            user=user,
            public_key=public_key,
            name=name,
        )
        return key

    def test_create_without_authenticated_user(self):
        resp = self.client.post(
            self.url,
            {
                "public_key": PUBLIC_KEY,
                "name": "macbook-pro",
            },
        )

        assert resp.status_code == status.HTTP_201_CREATED
        assert set(resp.data.keys()) == {
            "uuid",
            "name",
            "key_type",
            "fingerprint",
            "created_at",
            "updated_at",
            "last_used_at",
            "revoked_at",
            "public_key",
        }
        assert "id" not in resp.data
        assert resp.data["name"] == "macbook-pro"
        assert resp.data["public_key"] == PUBLIC_KEY
        key = UserSshKey.objects.get(uuid=resp.data["uuid"])
        assert key.user_id is None

    def test_create_rejects_invalid_name(self):
        resp = self.client.post(
            self.url,
            {
                "public_key": PUBLIC_KEY,
                "name": "MacBook Pro",
            },
        )

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in resp.data

    def test_create_existing_active_key_returns_ok(self):
        first = self.client.post(self.url, {"public_key": PUBLIC_KEY})
        second = self.client.post(self.url, {"public_key": PUBLIC_KEY})

        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_200_OK
        assert second.data["uuid"] == first.data["uuid"]
        assert UserSshKey.objects.count() == 1

    def test_create_malformed_public_key_returns_bad_request(self):
        resp = self.client.post(self.url, {"public_key": "ssh-ed25519 not-base64"})

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in resp.data

    def test_create_multiline_public_key_returns_bad_request(self):
        resp = self.client.post(
            self.url,
            {"public_key": "{}\n{}".format(PUBLIC_KEY, PUBLIC_KEY)},
        )

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.data == {"detail": "SSH public key must contain exactly one line."}

    def test_list_returns_nullable_user_active_keys_only(self):
        key = self.register_key(public_key=_public_key(1), user=None, name="local")
        self.register_key(public_key=_public_key(2), user=UserFactory(), name="owned")
        revoked = self.register_key(public_key=_public_key(3), user=None)
        UserSshKey.objects.revoke(user=None, key_uuid=revoked.uuid)

        resp = self.client.get(self.url)

        assert resp.status_code == status.HTTP_200_OK
        data = _results(resp)
        assert len(data) == 1
        assert data[0]["uuid"] == key.uuid.hex
        assert "updated_at" in data[0]
        assert "public_key" not in data[0]
        assert "id" not in data[0]

    def test_delete_revokes_nullable_user_key(self):
        key = self.register_key(user=None)

        resp = self.client.delete("{}/{}".format(self.url, key.uuid.hex))

        assert resp.status_code == status.HTTP_204_NO_CONTENT
        key.refresh_from_db()
        assert key.revoked_at is not None

        list_resp = self.client.get(self.url)
        assert _results(list_resp) == []

    def test_delete_unknown_key_returns_not_found(self):
        resp = self.client.delete("{}/{}".format(self.url, uuid.uuid4().hex))

        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_user_owned_key_returns_not_found(self):
        key = self.register_key(public_key=_public_key(4), user=UserFactory())

        resp = self.client.delete("{}/{}".format(self.url, key.uuid.hex))

        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_already_revoked_key_returns_not_found(self):
        key = self.register_key(user=None)
        UserSshKey.objects.revoke(user=None, key_uuid=key.uuid)

        resp = self.client.delete("{}/{}".format(self.url, key.uuid.hex))

        assert resp.status_code == status.HTTP_404_NOT_FOUND
