from haupt.db.defs import Models


def remove_bookmarks(object_id: int, content_type: str):
    # Remove any bookmark
    Models.Bookmark.objects.filter(
        content_type__model=content_type, object_id=object_id
    ).delete()


def bookmark_obj(user, obj, content_type: str):
    user_filter = {"user": user} if user else {}
    try:
        bookmark = Models.Bookmark.objects.get(
            content_type__model=content_type, object_id=obj.id, **user_filter
        )
        bookmark.enabled = True
        bookmark.save(update_fields=["enabled"])
    except Models.Bookmark.DoesNotExist:
        Models.Bookmark.objects.create(content_object=obj, **user_filter)
