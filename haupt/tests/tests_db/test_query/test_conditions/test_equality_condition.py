from django.conf import settings
from django.db.models import Q

from haupt.db.managers.statuses import new_run_status
from haupt.db.models.runs import Run
from polyaxon._pql.builder import EqualityCondition
from polyaxon.schemas import V1StatusCondition, V1Statuses
from tests.tests_db.test_query.base import BaseTestQuery

# pylint:disable=protected-access


class TestEqualityCondition(BaseTestQuery):
    def test_equality_operators(self):
        op = EqualityCondition._eq_operator(
            "field", "value", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field="value")
        op = EqualityCondition._neq_operator(
            "field", "value", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == ~Q(field="value")

    def test_equality_condition_init_with_correct_operator(self):
        eq_cond = EqualityCondition(op="eq")
        assert eq_cond.operator == EqualityCondition._eq_operator
        neq_cond = EqualityCondition(op="eq", negation=True)
        assert neq_cond.operator == EqualityCondition._neq_operator

    def test_equality_apply(self):
        eq_cond = EqualityCondition(op="eq")
        neq_cond = EqualityCondition(op="eq", negation=True)

        new_run_status(
            run=self.run,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.SCHEDULED, status=True
            ),
        )

        # eq
        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="status",
            params=V1Statuses.SCHEDULED,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="status",
            params=V1Statuses.SUCCEEDED,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        # neq
        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="status",
            params=V1Statuses.SCHEDULED,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="status",
            params=V1Statuses.SUCCEEDED,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1


del BaseTestQuery
