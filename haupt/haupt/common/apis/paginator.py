from clipped.utils.bools import to_bool
from rest_framework.pagination import LimitOffsetPagination


class PolyaxonBasePagination(LimitOffsetPagination):
    no_page_query_param = "no_page"

    def get_no_page(self, request):
        try:
            return to_bool(
                request.query_params.get(self.no_page_query_param),
                handle_none=True,
            )
        except (KeyError, ValueError):
            return False

    def get_count(self, queryset):
        if self.no_page:
            return None
        return super().get_count(queryset)

    def paginate_queryset(self, queryset, request, view=None):
        self.no_page = self.get_no_page(request)
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.count = self.get_count(queryset)
        self.offset = self.get_offset(request)
        self.request = request

        if self.no_page:
            return queryset[self.offset : self.offset + self.limit]

        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []
        return queryset[self.offset : self.offset + self.limit]

    def get_next_link(self):
        if self.no_page:
            return None
        return super().get_next_link()

    def get_previous_link(self):
        if self.no_page:
            return None
        return super().get_previous_link()


class LargeLimitOffsetPagination(PolyaxonBasePagination):
    max_limit = None
    default_limit = 100


class PolyaxonPagination(PolyaxonBasePagination):
    max_limit = 100
    default_limit = 20
