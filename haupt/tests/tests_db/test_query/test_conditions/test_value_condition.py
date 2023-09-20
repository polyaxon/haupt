from django.conf import settings
from django.db.models import Q

from haupt.db.factories.runs import RunFactory
from haupt.db.managers.statuses import new_run_status
from haupt.db.models.runs import Run
from polyaxon._pql.builder import ValueCondition
from polyaxon.schemas import V1StatusCondition, V1Statuses
from tests.tests_db.test_query.base import BaseTestQuery

# pylint:disable=protected-access


class TestValueCondition(BaseTestQuery):
    def test_value_operators(self):
        op = ValueCondition._in_operator(
            "field", ["v1", "v2"], query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__in=["v1", "v2"])
        op = ValueCondition._nin_operator(
            "field", ["v1", "v2"], query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == ~Q(field__in=["v1", "v2"])

    def test_range_apply(self):
        new_run_status(
            self.run,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.FAILED, status=True
            ),
        )
        run2 = RunFactory(project=self.project)
        new_run_status(
            run2,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.STOPPED, status=True
            ),
        )
        run3 = RunFactory(project=self.project)
        new_run_status(
            run3,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.RUNNING, status=True
            ),
        )

        eq_cond = ValueCondition(op="eq")
        neq_cond = ValueCondition(op="eq", negation=True)
        in_cond = ValueCondition(op="in")
        nin_cond = ValueCondition(op="in", negation=True)

        # eq
        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="status",
            params=V1Statuses.STOPPED,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="status",
            params="foo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        # neq
        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="status",
            params=V1Statuses.STOPPED,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="status",
            params="doo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 3

        # in
        queryset = in_cond.apply(
            queryset=Run.objects,
            name="status",
            params=[V1Statuses.STOPPED, V1Statuses.RUNNING],
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = in_cond.apply(
            queryset=Run.objects,
            name="status",
            params=[V1Statuses.STOPPED, V1Statuses.RESUMING],
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = in_cond.apply(
            queryset=Run.objects,
            name="status",
            params=[V1Statuses.RESUMING, V1Statuses.SKIPPED],
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = in_cond.apply(
            queryset=Run.objects,
            name="status",
            params=[V1Statuses.FAILED, V1Statuses.STOPPED, V1Statuses.RUNNING],
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 3

        # nin
        queryset = nin_cond.apply(
            queryset=Run.objects,
            name="status",
            params=[V1Statuses.STOPPED, V1Statuses.RUNNING],
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = nin_cond.apply(
            queryset=Run.objects,
            name="status",
            params=[V1Statuses.STOPPED, V1Statuses.RESUMING],
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = nin_cond.apply(
            queryset=Run.objects,
            name="status",
            params=[V1Statuses.RESUMING, V1Statuses.SKIPPED],
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 3

        queryset = nin_cond.apply(
            queryset=Run.objects,
            name="status",
            params=[V1Statuses.FAILED, V1Statuses.STOPPED, V1Statuses.RUNNING],
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0


del BaseTestQuery
