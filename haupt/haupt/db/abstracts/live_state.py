import random

from django.db import models

from haupt.db.managers.deleted import ArchivedManager, LiveManager, RestorableManager
from polyaxon.lifecycle import LiveState


class LiveStateModel(models.Model):
    live_state = models.IntegerField(
        null=True,
        blank=True,
        default=LiveState.LIVE,
        choices=LiveState.to_choices(),
        db_index=True,
    )

    objects = LiveManager()
    restorable = RestorableManager()
    all = models.Manager()
    archived = ArchivedManager()

    class Meta:
        abstract = True

    def delete_in_progress(self, update_name=False, commit=True) -> bool:
        if self.live_state == LiveState.DELETION_PROGRESSING:
            return False

        if update_name:
            self.name = "del_{}_{}".format(
                self.name, getattr(self, "uuid", random.randint(-90, 100))
            )
        self.live_state = LiveState.DELETION_PROGRESSING
        if commit:
            self.save(update_fields=["name", "live_state"])
        return True

    def archive(self, commit=True) -> bool:
        if (
            self.live_state == LiveState.ARCHIVED
            or self.live_state == LiveState.DELETION_PROGRESSING
        ):
            return False

        self.live_state = LiveState.ARCHIVED
        if commit:
            self.save(update_fields=["live_state"])
        return True

    def restore(self) -> bool:
        if self.live_state != LiveState.ARCHIVED:
            return False

        self.live_state = LiveState.LIVE
        self.save(update_fields=["live_state"])
        return True
