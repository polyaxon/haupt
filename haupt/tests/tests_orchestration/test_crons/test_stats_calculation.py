import pytest

from unittest.mock import patch

from haupt.common.test_cases.base import PolyaxonBaseTest
from haupt.db.factories.projects import ProjectFactory
from haupt.db.models.project_stats import ProjectStats
from haupt.orchestration.crons.stats import CronsStatsManager


@pytest.mark.crons_mark
class TestStatsCalculation(PolyaxonBaseTest):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()

    def test_stats_calculation_projects(self):
        assert self.project.latest_stats is None
        with patch("haupt.common.workers.send") as mock_send:
            CronsStatsManager.stats_calculation_projects()

        assert mock_send.call_count == 1

        # Add a new project stats
        self.project.latest_stats = ProjectStats(project=self.project)
        self.project.latest_stats.save()
        self.project.save(update_fields=["latest_stats"])

        assert self.project.updated_at < self.project.latest_stats.updated_at
        with patch("haupt.common.workers.send") as mock_send:
            CronsStatsManager.stats_calculation_projects()

        assert mock_send.call_count == 0

        # Update project updated_at
        self.project.name = "new-name"
        self.project.save()

        assert self.project.updated_at > self.project.latest_stats.updated_at

        with patch("haupt.common.workers.send") as mock_send:
            CronsStatsManager.stats_calculation_projects()

        assert mock_send.call_count == 1
