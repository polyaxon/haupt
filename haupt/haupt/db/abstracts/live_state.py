import random

from django.db import models
from django.utils.timezone import now

from haupt.db.managers.deleted import ArchivedManager, LiveManager, RestorableManager
from polyaxon.schemas import LiveState


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

    def delete_in_progress(
        self,
        update_name: bool = False,
        set_deleted_at: bool = True,
        commit: bool = True,
    ) -> bool:
        if self.live_state == LiveState.DELETION_PROGRESSING:
            return False

        self.live_state = LiveState.DELETION_PROGRESSING
        update_fields = ["live_state", "updated_at"]
        if update_name:
            self.name = "del_{}_{}".format(
                self.name, getattr(self, "uuid", random.randint(-90, 100))
            )
            update_fields.append("name")
        if set_deleted_at:
            self.deleted_at = now()
            update_fields.append("deleted_at")
        if commit:
            self.save(update_fields=update_fields)
        return True

    def confirm_delete(self) -> bool:
        if self.deleted_at:
            return False

        update_fields = ["deleted_at", "updated_at"]
        self.deleted_at = now()
        if self.live_state != LiveState.DELETION_PROGRESSING:
            self.live_state = LiveState.DELETION_PROGRESSING
            update_fields.append("live_state")
        self.save(update_fields=update_fields)
        return True

    def archive(self, commit: bool = True) -> bool:
        if self.live_state in {
            LiveState.ARCHIVED,
            LiveState.DELETION_PROGRESSING,
        }:
            return False

        self.archived_at = now()
        self.live_state = LiveState.ARCHIVED
        if commit:
            self.save(update_fields=["live_state", "archived_at", "updated_at"])
        return True

    def restore(self) -> bool:
        if self.live_state != LiveState.ARCHIVED:
            return False

        self.live_state = LiveState.LIVE
        update_fields = ["live_state", "updated_at"]
        if self.archived_at:
            self.archived_at = None
            update_fields.append("archived_at")
        if self.deleted_at:
            self.deleted_at = None
            update_fields.append("deleted_at")
        self.save(update_fields=update_fields)
        return True
