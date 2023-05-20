from clipped.utils.bools import to_bool

from django.conf import settings

from haupt.db.defs import Models


def get_bookmarks_filter(request, view):
    bookmarked_model = getattr(view, "bookmarked_model")
    bookmarks = request.query_params.get("bookmarks")
    return (
        bookmarked_model,
        bookmarks,
        bookmarks is not None and bookmarked_model is not None,
    )


def filter_bookmarks(queryset, request, view):
    bookmarked_model, bookmarks, has_bookmarks_filter = get_bookmarks_filter(
        request, view
    )

    if (
        not has_bookmarks_filter
        or not request.user
        or (settings.HAS_ORG_MANAGEMENT and request.user.is_anonymous)
    ):
        return queryset

    user_filters = {"user": request.user} if settings.HAS_ORG_MANAGEMENT else {}
    bookmark_ids = Models.Bookmark.objects.filter(
        **user_filters,
        content_type__model=bookmarked_model,
        enabled=True,
    ).values_list("object_id", flat=True)

    if to_bool(bookmarks):
        return queryset.filter(id__in=bookmark_ids)
    else:
        return queryset.exclude(id__in=bookmark_ids)
