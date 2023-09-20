import pytest

from rest_framework import status

from haupt.apis.serializers.runs import RunCloneSerializer
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.models.runs import Run
from polyaxon.api import API_V1
from polyaxon.schemas import ManagedBy, V1CloningKind, V1RunKind, V1Statuses
from tests.base.case import BaseTest


@pytest.mark.lineages_mark
class TestRunClonesListViewV1(BaseTest):
    serializer_class = RunCloneSerializer
    model_class = Run
    num_objects = 3

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()
        self.run = RunFactory(
            user=self.user,
            project=self.project,
            content="test",
            raw_content="test",
            managed_by=ManagedBy.AGENT,
        )
        self.runs = []
        obj = RunFactory(
            user=self.user,
            project=self.project,
            name="job",
            kind=V1RunKind.JOB,
            runtime=V1RunKind.JOB,
            original=self.run,
            cloning_kind=V1CloningKind.CACHE,
        )
        self.runs.append(obj)
        obj = RunFactory(
            user=self.user,
            project=self.project,
            name="service",
            kind=V1RunKind.SERVICE,
            runtime=V1RunKind.SERVICE,
            original=self.run,
            cloning_kind=V1CloningKind.RESTART,
        )
        self.runs.append(obj)
        obj = RunFactory(
            user=self.user,
            project=self.project,
            name="tfjob",
            kind=V1RunKind.JOB,
            runtime=V1RunKind.TFJOB,
            original=self.run,
            cloning_kind=V1CloningKind.COPY,
        )
        self.runs.append(obj)
        # other run
        other_object = RunFactory(
            user=self.user,
            project=self.project,
            content="test",
            raw_content="test",
            managed_by=ManagedBy.AGENT,
        )
        RunFactory(
            user=self.user,
            project=self.project,
            name="tfjob",
            kind=V1RunKind.JOB,
            runtime=V1RunKind.TFJOB,
            original=other_object,
            cloning_kind=V1CloningKind.COPY,
        )

        self.url = "/{}/{}/{}/runs/{}/lineage/clones/".format(
            API_V1, self.user.username, self.project.name, self.run.uuid.hex
        )
        self.query = Run.objects.filter(original=self.run)

    def test_get(self):
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

        assert resp.data["next"] is None
        assert resp.data["count"] == len(self.runs)

        data = resp.data["results"]
        assert len(data) == Run.objects.count() - 3
        assert data == self.serializer_class(self.query, many=True).data

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_get_filter(self):  # pylint:disable=too-many-statements
        # Status
        resp = self.client.get(
            self.url + "?query=status:{}".format(V1Statuses.CREATED.value)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 3

        resp = self.client.get(
            self.url + "?query=status:~{}".format(V1Statuses.WARNING.value)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 3

        resp = self.client.get(self.url + "?query=status:foo200")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 0

        # Values
        resp = self.client.get(self.url + f"?query=cloning_kind:restart")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        resp = self.client.get(self.url + f"?query=cloning_kind:copy")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        resp = self.client.get(self.url + f"?query=cloning_kind:cache")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        # Kind
        resp = self.client.get(self.url + "?query=kind:{}".format(V1RunKind.JOB.value))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 2

        resp = self.client.get(self.url + "?query=kind:~{}".format(V1RunKind.JOB.value))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        resp = self.client.get(
            self.url + "?query=kind:{}".format(V1RunKind.SERVICE.value)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1
