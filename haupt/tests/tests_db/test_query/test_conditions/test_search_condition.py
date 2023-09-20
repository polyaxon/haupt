from django.conf import settings
from django.db.models import Q

from haupt.db.factories.runs import RunFactory
from haupt.db.models.runs import Run
from polyaxon._pql.builder import SearchCondition
from tests.tests_db.test_query.base import BaseTestQuery

# pylint:disable=protected-access


class TestSearchCondition(BaseTestQuery):
    def test_contains_operators(self):
        op = SearchCondition._contains_operator(
            "field", "v1", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__icontains="v1")
        op = SearchCondition._ncontains_operator(
            "field", "v1", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == ~Q(field__icontains="v1")

    def test_startswith_operators(self):
        op = SearchCondition._startswith_operator(
            "field", "v1", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__istartswith="v1")
        op = SearchCondition._nstartswith_operator(
            "field", "v1", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == ~Q(field__istartswith="v1")

    def test_endswith_operators(self):
        op = SearchCondition._endswith_operator(
            "field", "v1", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__iendswith="v1")
        op = SearchCondition._nendswith_operator(
            "field", "v1", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == ~Q(field__iendswith="v1")

    def test_range_apply(self):
        RunFactory(project=self.project, name="foo_bar")
        RunFactory(project=self.project, name="foo_moo")
        self.run.name = "moo_boo"
        self.run.save()

        contains_cond = SearchCondition(op="icontains")
        ncontains_cond = SearchCondition(op="icontains", negation=True)
        startswith_cond = SearchCondition(op="istartswith")
        nstartswith_cond = SearchCondition(op="istartswith", negation=True)
        endswith_cond = SearchCondition(op="iendswith")
        nendswith_cond = SearchCondition(op="iendswith", negation=True)

        # contains
        queryset = contains_cond.apply(
            queryset=Run.objects,
            name="name",
            params="foo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = contains_cond.apply(
            queryset=Run.objects,
            name="name",
            params="bar",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = contains_cond.apply(
            queryset=Run.objects,
            name="name",
            params="boo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = contains_cond.apply(
            queryset=Run.objects,
            name="name",
            params="none",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        # ncontains
        queryset = ncontains_cond.apply(
            queryset=Run.objects,
            name="name",
            params="foo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = ncontains_cond.apply(
            queryset=Run.objects,
            name="name",
            params="bar",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = ncontains_cond.apply(
            queryset=Run.objects,
            name="name",
            params="boo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = ncontains_cond.apply(
            queryset=Run.objects,
            name="name",
            params="none",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 3

        # startswith
        queryset = startswith_cond.apply(
            queryset=Run.objects,
            name="name",
            params="foo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = startswith_cond.apply(
            queryset=Run.objects,
            name="name",
            params="bar",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = startswith_cond.apply(
            queryset=Run.objects,
            name="name",
            params="moo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        # nstartswith
        queryset = nstartswith_cond.apply(
            queryset=Run.objects,
            name="name",
            params="foo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = nstartswith_cond.apply(
            queryset=Run.objects,
            name="name",
            params="bar",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 3

        queryset = nstartswith_cond.apply(
            queryset=Run.objects,
            name="name",
            params="moo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        # endswith
        queryset = endswith_cond.apply(
            queryset=Run.objects,
            name="name",
            params="foo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = endswith_cond.apply(
            queryset=Run.objects,
            name="name",
            params="bar",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = endswith_cond.apply(
            queryset=Run.objects,
            name="name",
            params="moo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        # nendswith
        queryset = nendswith_cond.apply(
            queryset=Run.objects,
            name="name",
            params="foo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 3

        queryset = nendswith_cond.apply(
            queryset=Run.objects,
            name="name",
            params="bar",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = nendswith_cond.apply(
            queryset=Run.objects,
            name="name",
            params="moo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2


del BaseTestQuery
