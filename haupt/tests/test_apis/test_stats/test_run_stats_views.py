import pytest

from datetime import timedelta
from django.utils import timezone
from rest_framework import status

from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.factories.users import UserFactory
from haupt.db.models.project_stats import ProjectStats
from haupt.db.models.runs import Run
from polyaxon._services.values import PolyaxonServices
from polyaxon.api import API_V1
from polyaxon.schemas import V1ProjectVersionKind
from polyaxon._schemas.lifecycle import V1Statuses
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
            "wait_time": None,
            "resource_usage": None,
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
            wait_time={"1": 100, "0": 50},
            resource_usage={
                "cpu": {"1": 0.5, "0": 0.2},
                "memory": {"1": 1024, "0": 512},
            },
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
            "wait_time": {"1": 100, "0": 50},
            "resource_usage": {
                "cpu": {"1": 0.5, "0": 0.2},
                "memory": {"1": 1024, "0": 512},
            },
        }

    def test_get_series_mode_basic(self):
        """Test series mode returns multiple snapshots"""
        # Create multiple stats snapshots
        base_time = timezone.now()
        stats_list = []
        for i in range(5):
            stats = ProjectStats.objects.create(
                project=self.project,
                user={"count": 40 + i, "ids": [self.user.id]},
                run={"total": 1200 + i * 5},
                status={"running": i % 3, "succeeded": 1000 + i * 4},
                tracking_time={"total": 86400 + i * 3600},
                wait_time={"total": 3600 + i * 60},
                resource_usage={
                    "cpu": {"1": 1 * (1 + i * 0.1), "0": 2 * (1 + i * 0.1)},
                    "memory": {"1": 512 + i * 10, "0": 1024 + i * 20},
                    "gpu": {"1": 0.1 + i * 0.01, "0": 0.2 + i * 0.02},
                },
            )
            # Manually update created_at to ensure different timestamps
            stats.created_at = base_time - timedelta(hours=5 - i)
            stats.save()
            stats_list.append(stats)

        # Test series mode with hour interval
        end_date = base_time.strftime("%Y-%m-%d %H:%M:%S")
        start_date = (base_time - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        resp = self.client.get(
            self.url
            + "?mode=series&start_date={}&end_date={}".format(start_date, end_date)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "count" in resp.data
        assert "results" in resp.data
        assert "next" in resp.data
        assert "previous" in resp.data
        assert resp.data["count"] == 1
        assert len(resp.data["results"]) == 1

        start_date = (base_time - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
        resp = self.client.get(
            self.url
            + "?mode=series&start_date={}&end_date={}".format(start_date, end_date)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "count" in resp.data
        assert "results" in resp.data
        assert "next" in resp.data
        assert "previous" in resp.data
        assert resp.data["count"] == 5
        assert len(resp.data["results"]) == 5

        # Verify data is present
        for result in resp.data["results"]:
            assert "created_at" in result
            assert "user" in result
            assert "run" in result
            assert "status" in result

    def test_get_series_mode_with_intervals(self):
        """Test series mode with different intervals"""
        # Create some stats snapshots
        for i in range(10):
            ProjectStats.objects.create(
                project=self.project,
                user={"count": i},
                run={"total": i * 100},
                status={"succeeded": i * 10},
                tracking_time={"total": i * 1000},
                wait_time={"total": i * 100},
                resource_usage={
                    "cpu": {"1": 1 * (1 + i * 0.1), "0": 2 * (1 + i * 0.1)},
                    "memory": {"1": 512 + i * 10, "0": 1024 + i * 20},
                    "gpu": {"1": 0.1 + i * 0.01, "0": 0.2 + i * 0.02},
                },
            )

        # Test with hour interval (should return all)
        end_date = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        start_date = (timezone.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        resp = self.client.get(
            self.url
            + "?mode=series&interval=hour&start_date={}&end_date={}".format(
                start_date, end_date
            )
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 10
        assert len(resp.data["results"]) == 10

        # Test with day interval (should return all for small dataset)
        start_date = (timezone.now() - timedelta(hours=24)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        resp = self.client.get(
            self.url
            + "?mode=series&interval=day&start_date={}&end_date={}".format(
                start_date, end_date
            )
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 10
        assert len(resp.data["results"]) == 10

    def test_series_mode_without_data(self):
        """Test series mode when no stats data exists"""
        end_date = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        start_date = (timezone.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        resp = self.client.get(
            self.url
            + "?mode=series&start_date={}&end_date={}".format(start_date, end_date)
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 0
        assert resp.data["results"] == []

    def test_series_mode_with_boundary(self):
        """Test series mode with boundary parameter returns only first and last"""
        base_time = timezone.now()
        stats_list = []

        # Create 10 stats snapshots with different values
        for i in range(10):
            stats = ProjectStats.objects.create(
                project=self.project,
                user={"count": 100 + i},
                run={"total": 500 + i * 10},
                status={"succeeded": 400 + i * 5},
                tracking_time={"total": 1000 + i * 100},
                wait_time={"total": 200 + i * 20},
                resource_usage={
                    "cpu": {"1": 1 * (1 + i * 0.1), "0": 2 * (1 + i * 0.1)},
                    "memory": {"1": 512 + i * 10, "0": 1024 + i * 20},
                    "gpu": {"1": 0.1 + i * 0.01, "0": 0.2 + i * 0.02},
                },
            )
            # Manually update created_at to ensure different timestamps
            stats.created_at = base_time - timedelta(hours=9 - i, minutes=1)
            stats.save()
            stats_list.append(stats)

        # Test with boundary=true
        end_date = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        start_date = (timezone.now() - timedelta(hours=10)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        resp = self.client.get(
            self.url
            + "?mode=series&&boundary=true&start_date={}&end_date={}".format(
                start_date, end_date
            )
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 2  # Only first and last
        assert len(resp.data["results"]) == 2

        # Verify we got the first and last snapshots
        results = resp.data["results"]
        assert results[0]["user"]["count"] == 100  # First snapshot
        assert results[1]["user"]["count"] == 109  # Last snapshot

    def test_get_realtime_mode(self):
        """Test realtime mode returns current run stats for project"""

        # Create runs with different statuses
        self.factory_class(
            project=self.project,
            status=V1Statuses.QUEUED,
            user=self.user,
        )
        self.factory_class(
            project=self.project,
            status=V1Statuses.RUNNING,
            user=self.user,
        )
        self.factory_class(
            project=self.project,
            status=V1Statuses.WARNING,
            user=self.user,
        )
        self.factory_class(
            project=self.project,
            status=V1Statuses.SUCCEEDED,
            user=self.user,
        )

        resp = self.client.get(self.url + "?mode=realtime")
        assert resp.status_code == status.HTTP_200_OK
        stats = resp.data

        # Verify we get realtime stats
        assert stats["pending"] == 5  # 4 initial + 1 QUEUED
        assert stats["running"] == 1
        assert stats["warning"] == 1

    def test_series_mode_with_boundary_single_snapshot(self):
        """Test boundary parameter with only one snapshot"""
        ProjectStats.objects.create(
            project=self.project,
            user={"count": 42},
            run={"total": 100},
            status={"succeeded": 80},
            tracking_time={"total": 500},
            wait_time={"total": 100},
            resource_usage={
                "cpu": {"1": 0.5, "0": 1.0},
                "memory": {"1": 1024, "0": 2048},
                "gpu": {"1": 0.1, "0": 0.2},
            },
        )

        end_date = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        start_date = (timezone.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        resp = self.client.get(
            self.url
            + "?mode=series&boundary=true&start_date={}&end_date={}".format(
                start_date, end_date
            )
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1  # Only one snapshot
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["user"]["count"] == 42

    def test_series_mode_with_boundary_and_date_range(self):
        """Test boundary parameter with date range filtering"""
        base_time = timezone.now()

        # Create stats across 10 days
        for i in range(10):
            stats = ProjectStats.objects.create(
                project=self.project,
                user={"count": 200 + i},
                run={"total": 1000 + i * 20},
                status={"succeeded": 800 + i * 10},
                tracking_time={"total": 5000 + i * 200},
                wait_time={"total": 300 + i * 30},
                resource_usage={
                    "cpu": {"1": 1 * (1 + i * 0.1), "0": 2 * (1 + i * 0.1)},
                    "memory": {"1": 512 + i * 10, "0": 1024 + i * 20},
                    "gpu": {"1": 0.1 + i * 0.01, "0": 0.2 + i * 0.02},
                },
            )
            stats.created_at = base_time - timedelta(days=9 - i)
            stats.save()

        # Filter to middle 5 days
        start_date = (base_time - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        end_date = (base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")

        resp = self.client.get(
            f"{self.url}?mode=series&boundary=true"
            f"&start_date={start_date}&end_date={end_date}"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 2  # First and last within range
        assert len(resp.data["results"]) == 2

        # Verify we got the correct boundary values from the filtered range
        results = resp.data["results"]
        assert results[0]["user"]["count"] == 202  # Day 7 (index 2)
        assert (
            results[1]["user"]["count"] == 205
        )  # Day 3 (index 5) - adjusted for correct filtering


del BaseTestStatsViewV1
