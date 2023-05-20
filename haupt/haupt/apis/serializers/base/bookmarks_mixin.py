from clipped.utils.bools import to_bool
from rest_framework import serializers

from django.conf import settings

from haupt.common.apis.filters import OrderingFilter, QueryFilter
from haupt.common.authentication.base import is_user
from haupt.db.defs import Models
from haupt.db.query_managers.bookmarks import filter_bookmarks, get_bookmarks_filter


class BookmarkedSerializerMixin(serializers.Serializer):
    bookmarked_model = None

    bookmarked = serializers.SerializerMethodField()

    def get_bookmarked(self, obj):
        bookmarks = self.context.get("bookmarks", None)

        if bookmarks is not None:
            return obj.id in bookmarks
        else:
            # Get the requesting user if set in the context
            request = self.context.get("request", None)
            if not request:
                return False
            user = request.user
            if settings.HAS_ORG_MANAGEMENT and not is_user(user):
                return False
            user_filters = {"user": user} if settings.HAS_ORG_MANAGEMENT else {}
            if request:
                return Models.Bookmark.objects.filter(
                    **user_filters,
                    content_type__model=self.bookmarked_model,
                    object_id=obj.id,
                    enabled=True,
                ).exists()
        return False


class BookmarksQueryFilter(QueryFilter):
    def filter_queryset(self, request, queryset, view):
        queryset = filter_bookmarks(queryset, request, view)
        return super().filter_queryset(request, queryset, view)


class BookmarkedListMixinView:
    bookmarked_model = None
    filter_backends = (BookmarksQueryFilter, OrderingFilter)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        if not issubclass(serializer_class, BookmarkedSerializerMixin):
            return super().get_serializer(*args, **kwargs)

        queryset = args[0]

        if not queryset or (
            settings.HAS_ORG_MANAGEMENT and not is_user(self.request.user)
        ):
            return super().get_serializer(*args, **kwargs)

        object_ids = [o.id for o in queryset]

        bookmarked_model, bookmarks_filter, has_bookmarks_filter = get_bookmarks_filter(
            self.request, self
        )
        if has_bookmarks_filter:
            # The queryset will be already filtered/excluded all bookmarks
            bookmarks = object_ids if to_bool(bookmarks_filter) else []
        else:
            # Batch-get all the bookmarks for the objects in the queryset
            # and pass them on to the serializer
            user_filters = (
                {"user": self.request.user} if settings.HAS_ORG_MANAGEMENT else {}
            )
            bookmarks = Models.Bookmark.objects.filter(
                **user_filters,
                content_type__model=serializer_class.bookmarked_model,
                object_id__in=object_ids,
                enabled=True,
            ).values_list("object_id", flat=True)

        context = self.get_serializer_context()
        context["bookmarks"] = list(bookmarks)
        kwargs["context"] = context
        return serializer_class(*args, **kwargs)
