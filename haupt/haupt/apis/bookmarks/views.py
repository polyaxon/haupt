from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from django.conf import settings

from haupt.common.endpoints.base import BaseEndpoint, DestroyEndpoint, PostEndpoint
from haupt.db.defs import Models
from haupt.db.managers.bookmarks import bookmark_obj


class BookmarkCreateView(BaseEndpoint, PostEndpoint):
    """Base Bookmark create view."""

    queryset = None
    content_type = None

    def create(self, request, *args, **kwargs):
        obj = self.get_object()
        user_filter = {
            "user": self.request.user if settings.HAS_ORG_MANAGEMENT else None
        }
        bookmark_obj(**user_filter, obj=obj, content_type=self.content_type)
        self.audit(request, *args, **kwargs)
        return Response(status=status.HTTP_201_CREATED, data={})


class BookmarkDeleteView(BaseEndpoint, DestroyEndpoint):
    """Base Bookmark delete view."""

    queryset = None
    content_type = None

    def destroy(self, request, *args, **kwargs):
        user_filter = {"user": self.request.user} if settings.HAS_ORG_MANAGEMENT else {}
        obj = self.get_object()
        bookmark = get_object_or_404(
            Models.Bookmark,
            **user_filter,
            content_type__model=self.content_type,
            object_id=obj.id
        )
        bookmark.enabled = False
        bookmark.save(update_fields=["enabled"])
        self.audit(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)
