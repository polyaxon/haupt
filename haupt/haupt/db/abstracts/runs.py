from django.conf import settings
from django.core.validators import validate_slug
from django.db import models

from haupt.db.abstracts.contributors import ContributorsModel
from haupt.db.abstracts.describable import DescribableModel
from haupt.db.abstracts.diff import DiffModel
from haupt.db.abstracts.duration import DurationModel
from haupt.db.abstracts.live_state import LiveStateModel
from haupt.db.abstracts.nameable import NameableModel
from haupt.db.abstracts.readme import ReadmeModel
from haupt.db.abstracts.run_pipelines import RunPipelines
from haupt.db.abstracts.run_resources import RunResources
from haupt.db.abstracts.spec import SpecModel
from haupt.db.abstracts.state import OptionalStateModel
from haupt.db.abstracts.status import StatusModel
from haupt.db.abstracts.tag import TagModel
from haupt.db.abstracts.uid import UuidModel
from haupt.db.defs import Models
from polyaxon.schemas import (
    ManagedBy,
    V1CloningKind,
    V1RunKind,
    V1RunPending,
    V1Statuses,
)


class BaseRun(
    UuidModel,
    DiffModel,
    DurationModel,
    SpecModel,
    NameableModel,
    DescribableModel,
    ReadmeModel,
    StatusModel,
    TagModel,
    LiveStateModel,
    OptionalStateModel,
    RunPipelines,
    RunResources,
    ContributorsModel,
):
    name = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        default=None,
        validators=[validate_slug],
    )
    kind = models.CharField(
        max_length=12,
        db_index=True,
        choices=V1RunKind.to_choices(),
    )
    runtime = models.CharField(max_length=12, db_index=True, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Models.get_db_model_name("Project"),
        on_delete=models.CASCADE,
        related_name="runs",
    )
    managed_by = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        default=ManagedBy.AGENT,
        choices=ManagedBy.to_choices(),
        db_index=True,
    )
    pending = models.CharField(
        max_length=8,
        null=True,
        blank=True,
        db_index=True,
        choices=V1RunPending.to_choices(),
        help_text="If this entity requires approval before it should run.",
    )
    meta_info = models.JSONField(null=True, blank=True, default=dict)
    params = models.JSONField(null=True, blank=True)
    inputs = models.JSONField(null=True, blank=True)
    outputs = models.JSONField(null=True, blank=True)
    component_state = models.UUIDField(null=True, blank=True, db_index=True)
    original = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clones",
    )
    cloning_kind = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        choices=V1CloningKind.to_choices(),
    )
    artifacts = models.ManyToManyField(
        Models.get_db_model_name("Artifact"),
        blank=True,
        through=Models.get_db_model_name("ArtifactLineage"),
        related_name="runs",
    )

    class Meta:
        abstract = True
        app_label = "db"
        db_table = "db_run"
        indexes = [models.Index(fields=["name"])]

    @property
    def subpath(self):
        return self.uuid.hex

    @property
    def is_managed(self) -> bool:
        return ManagedBy.is_managed(self.managed_by)

    @property
    def is_clone(self) -> bool:
        return self.original_id is not None

    @property
    def is_restart(self) -> bool:
        return self.is_clone and self.cloning_kind == V1CloningKind.RESTART

    @property
    def is_resume(self) -> bool:
        if not self.status_conditions:
            return False
        return bool(
            [c for c in self.status_conditions if c.get("type") == V1Statuses.RESUMING]
        )

    @property
    def is_copy(self) -> bool:
        return self.is_clone and self.cloning_kind == V1CloningKind.COPY

    @property
    def is_job(self):
        return self.kind == V1RunKind.JOB

    @property
    def is_service(self):
        return self.kind == V1RunKind.SERVICE

    @property
    def is_dag(self):
        return self.kind == V1RunKind.DAG

    @property
    def is_matrix(self):
        return self.kind == V1RunKind.MATRIX

    @property
    def is_schedule(self):
        return self.kind == V1RunKind.SCHEDULE

    @property
    def has_pipeline(self):
        return self.is_dag or self.is_matrix or self.is_schedule

    @property
    def has_tuner_runtime(self):
        return self.runtime == V1RunKind.TUNER

    @property
    def has_notifier_runtime(self):
        return self.runtime == V1RunKind.NOTIFIER

    def get_last_condition(self):
        return (self.status_conditions or [{}])[-1]
