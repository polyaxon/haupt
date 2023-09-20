import datetime
import pytest

from clipped.utils.dates import DateTimeFormatter

from django.conf import settings
from django.db.models import Q

from haupt.db.factories.runs import RunFactory
from haupt.db.models.runs import Run
from polyaxon._pql.builder import DateTimeCondition
from polyaxon.exceptions import PQLException
from polyaxon.schemas import ManagedBy
from tests.tests_db.test_query.base import BaseTestQuery

# pylint:disable=protected-access


class TestDateTimeCondition(BaseTestQuery):
    def test_range_operators(self):
        with self.assertRaises(AssertionError):
            DateTimeCondition._range_operator(
                "field", "value", query_backend=Q, timezone=settings.TIME_ZONE
            )

        with self.assertRaises(AssertionError):
            DateTimeCondition._nrange_operator(
                "field", "value", query_backend=Q, timezone=settings.TIME_ZONE
            )

        with self.assertRaises(PQLException):
            DateTimeCondition._range_operator(
                "field", ("v1", "v2"), query_backend=Q, timezone=settings.TIME_ZONE
            )

        with self.assertRaises(PQLException):
            DateTimeCondition._nrange_operator(
                "field",
                ("v1", "2010-01-01"),
                query_backend=Q,
                timezone=settings.TIME_ZONE,
            )

        with self.assertRaises(PQLException):
            DateTimeCondition._nrange_operator(
                "field",
                ("2010-01-01", "v2"),
                query_backend=Q,
                timezone=settings.TIME_ZONE,
            )

        assert DateTimeCondition._range_operator(
            "field",
            ("2010-01-01", "2010-01-01"),
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        ) == Q(
            field__range=(
                DateTimeFormatter.extract("2010-01-01", settings.TIME_ZONE),
                DateTimeFormatter.extract("2010-01-01", settings.TIME_ZONE),
            )
        )
        assert DateTimeCondition._nrange_operator(
            "field",
            ("2010-01-01 10:10", "2010-01-01"),
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        ) == ~Q(
            field__range=(
                DateTimeFormatter.extract("2010-01-01 10:10", settings.TIME_ZONE),
                DateTimeFormatter.extract("2010-01-01", settings.TIME_ZONE),
            )
        )

    def test_range_condition_init_with_correct_operator(self):
        range_cond = DateTimeCondition(op="range")
        assert range_cond.operator == DateTimeCondition._range_operator
        nrange_cond = DateTimeCondition(op="range", negation=True)
        assert nrange_cond.operator == DateTimeCondition._nrange_operator

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_range_apply(self):
        # Delete current run
        self.run.delete()

        run = RunFactory(
            project=self.project,
            managed_by=ManagedBy.USER,
            outputs={"accuracy": 0.9, "precision": 0.9},
        )
        run.created_at = datetime.datetime(2018, 1, 1)
        run.save()
        run = RunFactory(
            project=self.project,
            managed_by=ManagedBy.USER,
            outputs={"accuracy": 0.9, "precision": 0.9},
        )
        run.created_at = datetime.datetime(2010, 1, 1)
        run.save()

        eq_cond = DateTimeCondition(op="eq")
        lt_cond = DateTimeCondition(op="lt")
        lte_cond = DateTimeCondition(op="lte")
        gt_cond = DateTimeCondition(op="gt")
        gte_cond = DateTimeCondition(op="gte")
        range_cond = DateTimeCondition(op="range")
        nrange_cond = DateTimeCondition(op="range", negation=True)

        # eq
        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2018-01-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2018-02-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        # lt
        queryset = lt_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2018-02-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = lt_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2018-01-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = lt_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2008-01-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        # lte
        queryset = lte_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2018-02-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = lte_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2018-01-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = lte_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2008-01-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        # gt
        queryset = gt_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2018-02-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = gt_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2018-01-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = gt_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2008-01-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        # lte
        queryset = gte_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2018-02-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = gte_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2018-01-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = gte_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params="2008-01-01",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        # range
        queryset = range_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params=(
                DateTimeFormatter.extract("2018-02-01 00:00", settings.TIME_ZONE),
                DateTimeFormatter.extract("2018-03-01 00:00", settings.TIME_ZONE),
            ),
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = range_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params=(
                DateTimeFormatter.extract("2018-02-01", settings.TIME_ZONE),
                DateTimeFormatter.extract("2008-03-01", settings.TIME_ZONE),
            ),
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = range_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params=(
                DateTimeFormatter.extract("2017-02-01", settings.TIME_ZONE),
                DateTimeFormatter.extract("2018-03-01", settings.TIME_ZONE),
            ),
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = range_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params=(
                DateTimeFormatter.extract("2008-02-01 00:00:12", settings.TIME_ZONE),
                DateTimeFormatter.extract("2018-03-01", settings.TIME_ZONE),
            ),
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = range_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params=(
                DateTimeFormatter.extract("2010-01-01", settings.TIME_ZONE),
                DateTimeFormatter.extract("2010-01-01", settings.TIME_ZONE),
            ),
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        # nrange
        queryset = nrange_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params=(
                DateTimeFormatter.extract("2018-02-01 00:00", settings.TIME_ZONE),
                DateTimeFormatter.extract("2018-03-01 00:00", settings.TIME_ZONE),
            ),
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = nrange_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params=(
                DateTimeFormatter.extract("2018-02-01", settings.TIME_ZONE),
                DateTimeFormatter.extract("2008-03-01", settings.TIME_ZONE),
            ),
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = nrange_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params=(
                DateTimeFormatter.extract("2017-02-01", settings.TIME_ZONE),
                DateTimeFormatter.extract("2018-03-01", settings.TIME_ZONE),
            ),
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = nrange_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params=(
                DateTimeFormatter.extract("2008-02-01 00:00:12", settings.TIME_ZONE),
                DateTimeFormatter.extract("2018-03-01", settings.TIME_ZONE),
            ),
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = nrange_cond.apply(
            queryset=Run.objects,
            name="created_at",
            params=(
                DateTimeFormatter.extract("2010-01-01", settings.TIME_ZONE),
                DateTimeFormatter.extract("2010-01-01", settings.TIME_ZONE),
            ),
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2


del BaseTestQuery
