from unittest.mock import patch

from django.db import connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.factories.users import UserFactory
from haupt.db.managers.artifacts import atomic_set_artifacts, set_artifacts
from haupt.db.models.artifacts import Artifact, ArtifactLineage
from traceml.artifacts import V1ArtifactKind, V1RunArtifact


class TestArtifacts(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()
        self.run = RunFactory(project=self.project)

    def test_set_metric_artifacts(self):
        state = self.run.uuid
        assert Artifact.objects.count() == 0
        metric1 = V1RunArtifact(
            name="accuracy",
            kind=V1ArtifactKind.METRIC,
            path="accuracy",
            summary=dict(last_value=0.9, max_value=0.9, min_value=0.1),
        )
        metric2 = V1RunArtifact(
            name="precision",
            kind=V1ArtifactKind.METRIC,
            path="precision",
            state=state,
            summary=dict(last_value=0.8, max_value=0.9, min_value=0.1),
        )
        set_artifacts(run=self.run, artifacts=[metric1, metric2])
        assert Artifact.objects.count() == 2
        results = {r.name: V1RunArtifact.from_model(r) for r in Artifact.objects.all()}
        result1 = results["accuracy"].to_dict()
        # State is generated
        assert result1.pop("state") is not None
        assert result1 == metric1.to_dict()
        result2 = results["precision"].to_dict()
        assert result2 == metric2.to_dict()

        metric1 = V1RunArtifact(
            name="accuracy",
            kind=V1ArtifactKind.METRIC,
            path="accuracy",
            state=state,
            summary=dict(last_value=0.9, max_value=0.99, min_value=0.1, max_step=100),
        )
        metric2 = V1RunArtifact(
            name="precision",
            kind=V1ArtifactKind.METRIC,
            path="precision",
            state=state,
            summary=dict(last_value=0.8, max_value=0.99, min_value=0.1, max_step=100),
        )
        set_artifacts(run=self.run, artifacts=[metric1, metric2])
        assert Artifact.objects.count() == 2
        results = {r.name: V1RunArtifact.from_model(r) for r in Artifact.objects.all()}
        assert results["accuracy"].to_dict() == metric1.to_dict()
        assert results["precision"].to_dict() == metric2.to_dict()

        metric1 = V1RunArtifact(
            name="accuracy",
            kind=V1ArtifactKind.METRIC,
            path="accuracy",
            state=state,
            summary=dict(last_value=0.77, max_value=0.99, min_value=0.1, max_step=100),
        )
        metric3 = V1RunArtifact(
            name="new",
            kind=V1ArtifactKind.METRIC,
            path="new",
            state=state,
            summary=dict(last_value=0.8, max_value=0.99, min_value=0.11, max_step=100),
        )
        set_artifacts(run=self.run, artifacts=[metric1, metric3])
        assert Artifact.objects.count() == 3
        results = {r.name: V1RunArtifact.from_model(r) for r in Artifact.objects.all()}
        assert results["accuracy"].to_dict() == metric1.to_dict()
        assert results["precision"].to_dict() == metric2.to_dict()
        assert results["new"].to_dict() == metric3.to_dict()

    def test_set_artifacts(self):
        state = self.run.uuid
        assert Artifact.objects.count() == 0
        artifact1 = V1RunArtifact(
            name="histo",
            path="histo",
            state=state,
            kind=V1ArtifactKind.HISTOGRAM,
            summary=dict(max_step=9, min_step=1),
        )
        artifact2 = V1RunArtifact(
            name="dataframe",
            path="df",
            state=state,
            kind=V1ArtifactKind.DATAFRAME,
            summary=dict(max_step=9, min_step=1),
        )
        set_artifacts(run=self.run, artifacts=[artifact1, artifact2])
        assert Artifact.objects.count() == 2
        results = {r.name: V1RunArtifact.from_model(r) for r in Artifact.objects.all()}
        assert (results["histo"]).to_dict() == artifact1.to_dict()
        assert results["dataframe"].to_dict() == artifact2.to_dict()

        artifact1 = V1RunArtifact(
            name="histo",
            path="histo",
            state=state,
            kind=V1ArtifactKind.HISTOGRAM,
            summary=dict(max_step=90, min_step=1),
        )
        artifact2 = V1RunArtifact(
            name="dataframe",
            path="df",
            state=state,
            kind=V1ArtifactKind.DATAFRAME,
            summary=dict(max_step=90, min_step=1),
        )
        set_artifacts(run=self.run, artifacts=[artifact1, artifact2])
        assert Artifact.objects.count() == 2
        results = {r.name: V1RunArtifact.from_model(r) for r in Artifact.objects.all()}
        assert results["histo"].to_dict() == artifact1.to_dict()
        assert results["dataframe"].to_dict() == artifact2.to_dict()

        artifact1 = V1RunArtifact(
            name="histo",
            path="histo",
            state=state,
            kind=V1ArtifactKind.HISTOGRAM,
            summary=dict(max_step=900, min_step=1),
        )
        artifact3 = V1RunArtifact(
            name="audio",
            path="audio",
            state=state,
            kind=V1ArtifactKind.AUDIO,
            summary=dict(max_step=900, min_step=1),
        )
        set_artifacts(run=self.run, artifacts=[artifact1, artifact3])
        assert Artifact.objects.count() == 3
        results = {r.name: V1RunArtifact.from_model(r) for r in Artifact.objects.all()}
        assert results["histo"].to_dict() == artifact1.to_dict()
        assert results["dataframe"].to_dict() == artifact2.to_dict()
        assert results["audio"].to_dict() == artifact3.to_dict()

    def test_atomic_set_artifacts_retries_after_concurrent_create(self):
        state = self.run.uuid
        Artifact.objects.create(
            name="accuracy",
            kind=V1ArtifactKind.METRIC,
            path="accuracy",
            state=state,
            summary={},
        )
        metric = V1RunArtifact(
            name="accuracy",
            kind=V1ArtifactKind.METRIC,
            path="accuracy",
            state=state,
            summary=dict(last_value=0.9, max_value=0.9, min_value=0.1),
        )

        real_filter = Artifact.objects.filter
        real_bulk_create = Artifact.objects.bulk_create
        calls = {"filter": 0, "bulk_create": 0}

        def filter_misses_first(*args, **kwargs):
            # Attempt 1 doesn't see the artifact, as if another writer created it
            # after the lookup, so it inserts a duplicate.
            calls["filter"] += 1
            if calls["filter"] == 1:
                return Artifact.objects.none()
            return real_filter(*args, **kwargs)

        def bulk_create_aborts_first(*args, **kwargs):
            # Leave the transaction unusable after the IntegrityError, as on
            # PostgreSQL, whatever the test database.
            calls["bulk_create"] += 1
            if calls["bulk_create"] == 1:
                with transaction.atomic(savepoint=False):
                    return real_bulk_create(*args, **kwargs)
            return real_bulk_create(*args, **kwargs)

        with (
            patch.object(Artifact.objects, "filter", side_effect=filter_misses_first),
            patch.object(
                Artifact.objects, "bulk_create", side_effect=bulk_create_aborts_first
            ),
        ):
            atomic_set_artifacts(run=self.run, artifacts=[metric])

        assert calls["bulk_create"] == 1
        artifact = Artifact.objects.get(name="accuracy", state=state)
        assert V1RunArtifact.from_model(artifact).to_dict() == metric.to_dict()
        assert ArtifactLineage.objects.filter(run=self.run, artifact=artifact).exists()

    @staticmethod
    def get_metrics(prefix, count, is_input=None):
        return [
            V1RunArtifact(
                name=f"{prefix}{i}",
                kind=V1ArtifactKind.METRIC,
                path=f"{prefix}{i}",
                is_input=is_input,
                summary=dict(last_value=i),
            )
            for i in range(count)
        ]

    def count_queries(self, artifacts):
        with CaptureQueriesContext(connection) as queries:
            set_artifacts(run=self.run, artifacts=artifacts)
        return len(queries.captured_queries)

    def test_set_artifacts_has_no_per_artifact_queries(self):
        # Load the run's project and owner first so they don't count.
        set_artifacts(run=self.run, artifacts=self.get_metrics("warmup", 1))
        small = self.get_metrics("small", 2)
        large = self.get_metrics("large", 10)

        # First send creates the artifacts and the links.
        assert self.count_queries(small) == self.count_queries(large)
        # Re-send updates the artifacts and keeps the links.
        assert self.count_queries(small) == self.count_queries(large)

    def test_set_artifacts_resend_keeps_one_link_per_artifact(self):
        artifacts = self.get_metrics("metric", 3)
        set_artifacts(run=self.run, artifacts=artifacts)
        set_artifacts(run=self.run, artifacts=artifacts)

        links = ArtifactLineage.objects.filter(run=self.run)
        assert links.count() == 3
        assert set(links.values_list("is_input", flat=True)) == {None}

    def test_set_artifacts_links_is_input_none_and_false_separately(self):
        set_artifacts(run=self.run, artifacts=self.get_metrics("metric", 1))
        set_artifacts(
            run=self.run, artifacts=self.get_metrics("metric", 1, is_input=False)
        )

        assert Artifact.objects.count() == 1
        links = ArtifactLineage.objects.filter(run=self.run)
        assert set(links.values_list("is_input", flat=True)) == {None, False}
