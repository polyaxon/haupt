import pytest

from rest_framework import status

from django.conf import settings

from haupt.apis.serializers.runs import (
    DownstreamRunEdgeSerializer,
    UpstreamRunEdgeSerializer,
)
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.models.run_edges import RunEdge
from polyaxon.api import API_V1
from polyaxon.schemas import ManagedBy, V1RunEdgeKind, V1RunKind, V1Statuses
from tests.base.case import BaseTest


@pytest.mark.lineages_mark
class BaseRunEdgeListViewV1(BaseTest):
    serializer_class = None
    model_class = RunEdge
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
        )
        self.runs.append(obj)
        obj = RunFactory(
            user=self.user,
            project=self.project,
            name="service",
            kind=V1RunKind.SERVICE,
            runtime=V1RunKind.SERVICE,
        )
        self.runs.append(obj)
        obj = RunFactory(
            user=self.user,
            project=self.project,
            name="tfjob",
            kind=V1RunKind.JOB,
            runtime=V1RunKind.TFJOB,
        )
        self.runs.append(obj)
        obj = RunFactory(
            user=self.user,
            project=self.project,
            name="tuner",
            kind=V1RunKind.TUNER,
            runtime=V1RunKind.TUNER,
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
        run_dep = RunFactory(
            user=self.user,
            project=self.project,
            name="job",
            kind=V1RunKind.JOB,
            runtime=V1RunKind.JOB,
        )
        RunEdge.objects.create(upstream=other_object, downstream=run_dep)
        RunEdge.objects.create(upstream=run_dep, downstream=other_object)

        self.url = self.set_url()
        self.set_edges()
        self.query = self.set_query()

    @staticmethod
    def _get_status(status):
        if settings.DB_ENGINE_NAME == "sqlite":
            return {status: ""}
        else:
            return [status]

    def set_url(self):
        raise NotImplementedError

    def set_edges(self):
        raise NotImplementedError

    def set_query(self):
        raise NotImplementedError

    def test_get(self):
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

        assert resp.data["next"] is None
        assert resp.data["count"] == len(self.runs)

        data = resp.data["results"]
        assert len(data) == RunEdge.objects.count() - 2
        assert data == self.serializer_class(self.query, many=True).data

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_get_filter(self):  # pylint:disable=too-many-statements
        # Status
        resp = self.client.get(
            self.url + "?query=statuses:{}".format(V1Statuses.WARNING.value)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        resp = self.client.get(
            self.url + "?query=statuses:~{}".format(V1Statuses.WARNING.value)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 3

        resp = self.client.get(self.url + "?query=statuses:foo200")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 0

        # Values
        resp = self.client.get(self.url + f"?query=values.foo:bar")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 4

        resp = self.client.get(self.url + f"?query=values.foo:moo")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 0

        # Kind
        resp = self.client.get(
            self.url + "?query=kind:{}".format(V1RunEdgeKind.HOOK.value)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 2

        resp = self.client.get(
            self.url + "?query=kind:~{}".format(V1RunEdgeKind.HOOK.value)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 2

        resp = self.client.get(
            self.url + "?query=kind:{}".format(V1RunEdgeKind.ACTION.value)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 0

        resp = self.client.get(
            self.url + "?query=kind:{}".format(V1RunEdgeKind.DAG.value)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        resp = self.client.get(
            self.url + "?query=kind:{}".format(V1RunEdgeKind.EVENT.value)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1


@pytest.mark.lineages_mark
class TestRunUpstreamListViewV1(BaseRunEdgeListViewV1):
    serializer_class = UpstreamRunEdgeSerializer

    def set_url(self):
        return "/{}/{}/{}/runs/{}/lineage/upstream/".format(
            API_V1, self.user.username, self.project.name, self.run.uuid.hex
        )

    def set_edges(self):
        kinds = [
            V1RunEdgeKind.EVENT,
            V1RunEdgeKind.HOOK,
            V1RunEdgeKind.HOOK,
            V1RunEdgeKind.DAG,
        ]

        status = [
            V1Statuses.RUNNING,
            V1Statuses.RUNNING,
            V1Statuses.RUNNING,
            V1Statuses.WARNING,
        ]
        for i, run in enumerate(self.runs):
            RunEdge.objects.create(
                upstream=run,
                downstream=self.run,
                values={"foo": "bar"},
                statuses=self._get_status(status[i]),
                kind=kinds[i],
            )

    def set_query(self):
        return self.run.upstream_edges.all()


@pytest.mark.lineages_mark
class TestRunDownstreamListViewV1(BaseRunEdgeListViewV1):
    serializer_class = DownstreamRunEdgeSerializer

    def set_url(self):
        return "/{}/{}/{}/runs/{}/lineage/downstream/".format(
            API_V1, self.user.username, self.project.name, self.run.uuid.hex
        )

    def set_edges(self):
        kinds = [
            V1RunEdgeKind.EVENT,
            V1RunEdgeKind.HOOK,
            V1RunEdgeKind.HOOK,
            V1RunEdgeKind.DAG,
        ]
        status = [
            V1Statuses.RUNNING,
            V1Statuses.RUNNING,
            V1Statuses.RUNNING,
            V1Statuses.WARNING,
        ]
        for i, run in enumerate(self.runs):
            RunEdge.objects.create(
                downstream=run,
                upstream=self.run,
                values={"foo": "bar"},
                statuses=self._get_status(status[i]),
                kind=kinds[i],
            )

    def set_query(self):
        return self.run.downstream_edges.all()


del BaseRunEdgeListViewV1
