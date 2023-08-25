import random

from django.db import models
from django.utils.timezone import now

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
    deleted_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

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

    def pre_delete(self, commit=True) -> bool:
        if self.live_state == LiveState.DELETED:
            return False

        self.deleted_at = now()
        self.live_state = LiveState.DELETED
        if commit:
            self.save(update_fields=["live_state", "deleted_at"])
        return True

    def archive(self, commit=True) -> bool:
        if self.live_state in {
            LiveState.ARCHIVED,
            LiveState.DELETION_PROGRESSING,
            LiveState.DELETED,
        }:
            return False

        self.archived_at = now()
        self.live_state = LiveState.ARCHIVED
        if commit:
            self.save(update_fields=["live_state", "archived_at"])
        return True

    def restore(self) -> bool:
        if self.live_state != LiveState.ARCHIVED:
            return False

        self.live_state = LiveState.LIVE
        update_fields = ["live_state"]
        if self.archived_at:
            self.archived_at = None
            update_fields.append("archived_at")
        if self.deleted_at:
            self.deleted_at = None
            update_fields.append("deleted_at")
        self.save(update_fields=update_fields)
        return True
