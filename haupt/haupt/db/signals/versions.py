from clipped.decorators.signals import ignore_raw, ignore_updates_pre
from clipped.utils.enums import get_enum_value

from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from haupt.db.defs import Models
from polyaxon._constants.metadata import META_IS_PROMOTED
from polyaxon.schemas import V1StageCondition, V1Stages


@receiver(
    pre_save, sender=Models.ProjectVersion, dispatch_uid="artifact_version_created"
)
@ignore_updates_pre
@ignore_raw
def artifact_version_created(sender, instance=None, created=False, **kwargs):
    instance.stage_conditions = [
        V1StageCondition.get_condition(
            type=V1Stages.TESTING,
            status="True",
            reason="{}VersionCreated".format(instance.kind.capitalize()),
            message="A new {} version is created".format(get_enum_value(instance.kind)),
        ).to_dict()
    ]


@receiver(
    pre_delete,
    sender=Models.ProjectVersion,
    dispatch_uid="check_related_run_to_artifact",
)
@ignore_raw
def check_related_run_to_artifact(sender, instance=None, created=False, **kwargs):
    if instance.run_id:
        run = instance.run
        if (
            META_IS_PROMOTED in run.meta_info
            and run.versions.exclude(id=instance.id).count() == 0
        ):
            run.meta_info.pop(META_IS_PROMOTED, None)
            run.save(update_fields=["meta_info", "updated_at"])
