import pytest

from rest_framework import status

from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.factories.users import UserFactory
from haupt.db.models.project_stats import ProjectStats
from haupt.db.models.runs import Run
from polyaxon.api import API_V1
from polyaxon.lifecycle import V1ProjectVersionKind
from polyaxon.services.values import PolyaxonServices
from tests.base.case import BaseTest


class BaseTestStatsViewV1(BaseTest):
    model_class = Run
    factory_class = RunFactory
    num_objects = 3

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()
        self.run = self.factory_class(project=self.project, user=self.user)
        self.url = self.set_url()
        self.objects = [
            self.factory_class(project=self.project, user=self.user, pipeline=self.run)
            for _ in range(self.num_objects)
        ]
        self.client.polyaxon_service = PolyaxonServices.UI

    def set_url(self):
        raise NotImplementedError()

    def test_get_without_spec_raises(self):
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        resp = self.client.get(self.url + "?mode=analytics&kind=foo")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        resp = self.client.get(self.url + "?mode=analytics&kind=foo")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        resp = self.client.get(self.url + "?mode=analytics&kind=series")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        resp = self.client.get(self.url + "?mode=analytics&kind=series&aggregate=test")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        resp = self.client.get(
            self.url + "?mode=foo&kind=annotations&aggregate=progress"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.stats_mark
class TestRunStatsViewV1(BaseTestStatsViewV1):
    def set_url(self):
        return "/{}/{}/{}/runs/{}/stats/".format(
            API_V1, "default", self.project.name, self.run.uuid.hex
        )

    def _get_expected_data(self):
        return {"done": 0, "count": 3}


@pytest.mark.stats_mark
class TestProjectStatsViewV1(BaseTestStatsViewV1):
    def set_url(self):
        return "/{}/{}/{}/stats/".format(
            API_V1,
            "default",
            self.project.name,
        )

    def _get_expected_data(self):
        return {"done": 0, "count": 4}

    def test_get_stats(self):
        resp = self.client.get(self.url + "?mode=stats")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data == {
            "created_at": None,
            "run": None,
            "status": None,
            "version": None,
            "tracking_time": None,
        }

        self.project.latest_stats = ProjectStats(
            project=self.project,
            user={"count": 1, "ids": [self.user.id]},
            run={"1": 1, "0": 2},
            status={"running": 1, "succeeded": 2},
            version={
                V1ProjectVersionKind.COMPONENT: 1,
                V1ProjectVersionKind.MODEL: 2,
                V1ProjectVersionKind.ARTIFACT: 3,
            },
            tracking_time={"1": 1111, "0": 200},
        )
        self.project.latest_stats.save()
        self.project.save()

        resp = self.client.get(self.url + "?mode=stats")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data != {}
        assert resp.data.pop("created_at") is not None
        assert resp.data.pop("updated_at") is not None
        assert resp.data == {
            "user": {"count": 1},
            "run": {"1": 1, "0": 2},
            "status": {"running": 1, "succeeded": 2},
            "version": {
                V1ProjectVersionKind.COMPONENT: 1,
                V1ProjectVersionKind.MODEL: 2,
                V1ProjectVersionKind.ARTIFACT: 3,
            },
            "tracking_time": {"1": 1111, "0": 200},
        }


del BaseTestStatsViewV1
