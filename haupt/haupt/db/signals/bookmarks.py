from clipped.decorators.signals import ignore_raw

from django.db.models.signals import post_delete
from django.dispatch import receiver

from haupt.common.content_types import ContentTypes
from haupt.db.defs import Models
from haupt.db.managers.bookmarks import remove_bookmarks


@receiver(post_delete, sender=Models.Run, dispatch_uid="run_bookmark_post_delete")
@ignore_raw
def run_bookmark_post_delete(sender, **kwargs):
    instance = kwargs["instance"]
    remove_bookmarks(object_id=instance.id, content_type=ContentTypes.RUN.value)


@receiver(
    post_delete, sender=Models.Project, dispatch_uid="project_bookmark_post_delete"
)
@ignore_raw
def project_bookmark_post_delete(sender, **kwargs):
    instance = kwargs["instance"]
    remove_bookmarks(object_id=instance.id, content_type=ContentTypes.PROJECT.value)
