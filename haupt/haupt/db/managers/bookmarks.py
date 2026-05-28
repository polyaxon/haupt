from django.contrib.contenttypes.models import ContentType

from haupt.common.content_types import ContentTypes
from haupt.db.defs import Models


def get_bookmark_content_type_id(content_type: str):
    if content_type == ContentTypes.RUN.value:
        return ContentType.objects.get_for_model(Models.Run).id
    if content_type == ContentTypes.PROJECT.value:
        return ContentType.objects.get_for_model(Models.Project).id
    raise ValueError("Unsupported bookmark content type: {}".format(content_type))


def remove_bookmarks(object_id: int, content_type: str):
    # Intentionally broad: object deletion should also purge stale historical
    # content type rows, and this path never dereferences content_object.
    Models.Bookmark.objects.filter(
        content_type__model=content_type, object_id=object_id
    ).delete()


def bookmark_obj(user, obj, content_type: str):
    user_filter = {"user": user} if user else {}
    bookmark_content_type_id = get_bookmark_content_type_id(content_type)
    try:
        bookmark = Models.Bookmark.objects.get(
            content_type_id=bookmark_content_type_id, object_id=obj.id, **user_filter
        )
        bookmark.enabled = True
        bookmark.save(update_fields=["enabled"])
    except Models.Bookmark.DoesNotExist:
        Models.Bookmark.objects.create(
            content_type_id=bookmark_content_type_id, object_id=obj.id, **user_filter
        )
