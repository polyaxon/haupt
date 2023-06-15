from clipped.decorators.signals import ignore_raw, ignore_updates
from rest_framework.exceptions import ValidationError

from django.db.models.signals import post_save
from django.dispatch import receiver

from haupt.common import auditor
from haupt.common.events.registry.run import RUN_CREATED
from haupt.db.defs import Models


@receiver(post_save, sender=Models.Run, dispatch_uid="run_created")
@ignore_updates
@ignore_raw
def run_created(sender, **kwargs):
    instance = kwargs["instance"]
    if instance.is_managed:
        if (instance.is_clone and instance.content is None) or (
            not instance.is_clone and instance.raw_content is None
        ):
            raise ValidationError("A managed run should have a valid specification.")
    auditor.record(event_type=RUN_CREATED, instance=instance)
