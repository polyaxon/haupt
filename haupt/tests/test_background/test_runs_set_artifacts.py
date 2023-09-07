import pytest

from haupt.db.factories.runs import RunFactory
from haupt.db.models.artifacts import Artifact
from haupt.orchestration.scheduler.manager import SchedulingManager
from tests.test_background.case import BaseTest
from traceml.artifacts import V1ArtifactKind, V1RunArtifact


@pytest.mark.background_mark
class TestSetArtifacts(BaseTest):
    def test_runs_set_artifacts(self):
        experiment = RunFactory(project=self.project, user=self.user)
        state = experiment.uuid
        assert experiment.artifacts.count() == 0

        metric1 = V1RunArtifact(
            name="accuracy",
            kind=V1ArtifactKind.METRIC,
            path="accuracy",
            summary=dict(last_value=0.77, max_value=0.99, min_value=0.1, max_step=100),
        )
        metric2 = V1RunArtifact(
            name="precision",
            kind=V1ArtifactKind.METRIC,
            path="precision",
            state=state,
            summary=dict(last_value=0.8, max_value=0.99, min_value=0.11, max_step=100),
        )
        SchedulingManager.runs_set_artifacts(
            run_id=experiment.id, artifacts=[metric1.to_dict(), metric2.to_dict()]
        )

        assert experiment.artifacts.count() == 2
        results = {r.name: V1RunArtifact.from_model(r) for r in Artifact.objects.all()}
        result1 = results["accuracy"].to_dict()
        # State is generated
        assert result1.pop("state") is not None
        assert result1 == metric1.to_dict()
        result2 = results["precision"].to_dict()
        # State is the same
        assert result2 == metric2.to_dict()

        metric1 = V1RunArtifact(
            name="accuracy",
            kind=V1ArtifactKind.METRIC,
            path="accuracy",
            state=state,
            summary=dict(last_value=0.8, max_value=0.99, min_value=0.1, max_step=100),
        )
        metric3 = V1RunArtifact(
            name="recall",
            kind=V1ArtifactKind.METRIC,
            path="recall",
            state=state,
            summary=dict(last_value=0.1, max_value=0.2, min_value=0.1, max_step=100),
        )
        SchedulingManager.runs_set_artifacts(
            run_id=experiment.id, artifacts=[metric1.to_dict(), metric3.to_dict()]
        )

        assert experiment.artifacts.count() == 3
        results = {r.name: V1RunArtifact.from_model(r) for r in Artifact.objects.all()}
        assert results["accuracy"].to_dict() == metric1.to_dict()
        assert results["precision"].to_dict() == metric2.to_dict()
        assert results["recall"].to_dict() == metric3.to_dict()
