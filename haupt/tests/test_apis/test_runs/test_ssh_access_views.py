import pytest

from rest_framework import status

from haupt.db.abstracts.user_ssh_keys import fingerprint_public_key_body
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.factories.users import UserFactory
from haupt.db.models.user_ssh_keys import UserSshKey
from polyaxon._services.values import PolyaxonServices
from polyaxon.api import API_V1
from polyaxon.schemas import (
    ManagedBy,
    V1CompiledOperation,
    V1Plugins,
    V1RunKind,
    V1Service,
    V1Statuses,
)
from tests.base.case import BaseTest


KEY_BODY = "AAAAC3NzaC1lZDI1NTE5AAAAIAABAgMEBQYHCAkKCwwNDg8QERITFBUWFxgZGhscHR4f"
PUBLIC_KEY = "ssh-ed25519 {} user@example.com".format(KEY_BODY)
FINGERPRINT = fingerprint_public_key_body(KEY_BODY)


def _content(ssh=True):
    return V1CompiledOperation(
        run=V1Service(),
        plugins=V1Plugins(ssh=ssh),
    ).to_json()


@pytest.mark.run_mark
class TestRunSshAccessValidateViewV1(BaseTest):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()
        content = _content()
        self.run = RunFactory(
            user=self.user,
            project=self.project,
            kind=V1RunKind.SERVICE,
            status=V1Statuses.RUNNING,
            content=content,
            raw_content=content,
            managed_by=ManagedBy.AGENT,
        )
        self.url = "/{}/{}/{}/runs/{}/ssh/access/validate/".format(
            API_V1,
            self.project.owner.name,
            self.project.name,
            self.run.uuid.hex,
        )
        self.client.polyaxon_service = PolyaxonServices.AGENT

    def register_key(self, user=None):
        key, _ = UserSshKey.objects.register(user=user, public_key=PUBLIC_KEY)
        return key

    def test_validate(self):
        key = self.register_key()

        resp = self.client.post(self.url, {"fingerprint": FINGERPRINT})

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data == {
            "key_uuid": key.uuid.hex,
            "username": None,
            "agent_uuid": None,
        }
        key.refresh_from_db()
        assert key.last_used_at is not None

    def test_requires_agent_service(self):
        self.client.polyaxon_service = None

        resp = self.client.post(self.url, {"fingerprint": FINGERPRINT})

        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_rejects_malformed_fingerprint(self):
        resp = self.client.post(self.url, {"fingerprint": "bad"})

        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_revoked_key(self):
        key = self.register_key()
        UserSshKey.objects.revoke(user=None, key_uuid=key.uuid)

        resp = self.client.post(self.url, {"fingerprint": FINGERPRINT})

        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_rejects_user_key(self):
        self.register_key(user=UserFactory())

        resp = self.client.post(self.url, {"fingerprint": FINGERPRINT})

        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_rejects_run_without_ssh_plugin(self):
        self.register_key()
        self.run.content = _content(ssh=False)
        self.run.save(update_fields=["content"])

        resp = self.client.post(self.url, {"fingerprint": FINGERPRINT})

        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_rejects_run_not_on_k8s(self):
        self.register_key()
        self.run.status = V1Statuses.STOPPED
        self.run.save(update_fields=["status"])

        resp = self.client.post(self.url, {"fingerprint": FINGERPRINT})

        assert resp.status_code == status.HTTP_404_NOT_FOUND
