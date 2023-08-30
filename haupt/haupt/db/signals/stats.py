from clipped.decorators.signals import ignore_raw, ignore_updates_pre

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now

from haupt.db.defs import Models


@receiver(pre_save, sender=Models.ProjectStats)
@ignore_updates_pre
@ignore_raw
def round_to_hour(sender, instance, **kwargs):
    instance.created_at = now().replace(minute=0, second=0, microsecond=0)
