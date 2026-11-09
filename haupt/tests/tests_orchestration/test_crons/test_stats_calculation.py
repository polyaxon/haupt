import pytest
from unittest.mock import patch

from haupt.common.test_cases.base import PolyaxonBaseTest
from haupt.db.factories.projects import ProjectFactory
from haupt.db.models.project_stats import ProjectStats
from haupt.orchestration.crons.stats import CronsStatsManager
from polyaxon.schemas import LiveState


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

    def test_stats_calculation_projects_includes_archived(self):
        archived = ProjectFactory()
        archived.latest_stats = ProjectStats(project=archived)
        archived.latest_stats.save()
        archived.save(update_fields=["latest_stats"])
        deleting = ProjectFactory(live_state=LiveState.DELETION_PROGRESSING)

        # `self.project` has no snapshot, so both calls dispatch something
        with patch("haupt.common.workers.send"):
            project_ids = CronsStatsManager.stats_calculation_projects()
        assert archived.id not in project_ids
        assert deleting.id not in project_ids

        archived.archive()

        with patch("haupt.common.workers.send"):
            project_ids = CronsStatsManager.stats_calculation_projects()
        assert archived.id in project_ids
        assert deleting.id not in project_ids
