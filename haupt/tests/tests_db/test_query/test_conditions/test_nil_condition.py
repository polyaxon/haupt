from django.conf import settings
from django.db.models import Q

from haupt.db.models.runs import Run
from polyaxon._pql.builder import NilCondition
from polyaxon.schemas import V1Statuses
from tests.tests_db.test_query.base import BaseTestQuery

# pylint:disable=protected-access


class TestNilCondition(BaseTestQuery):
    def test_nil_operators(self):
        op = NilCondition._nil_operator(
            "field", "nil", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__isnull=True)
        op = NilCondition._not_nil_operator(
            "field", "nil", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__isnull=False)

    def test_nil_condition_init_with_correct_operator(self):
        nil_cond = NilCondition(op="nil")
        assert nil_cond.operator == NilCondition._nil_operator
        not_nil_cond = NilCondition(op="nil", negation=True)
        assert not_nil_cond.operator == NilCondition._not_nil_operator

    def test_nil_apply(self):
        nil_cond = NilCondition(op="nil")
        not_nil_cond = NilCondition(op="nil", negation=True)

        # eq
        queryset = nil_cond.apply(
            queryset=Run.objects,
            name="inputs",
            params="nil",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = nil_cond.apply(
            queryset=Run.objects,
            name="status",
            params="nil",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        # neq
        queryset = not_nil_cond.apply(
            queryset=Run.objects,
            name="inputs",
            params=V1Statuses.SCHEDULED,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = not_nil_cond.apply(
            queryset=Run.objects,
            name="status",
            params="nil",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1


del BaseTestQuery
