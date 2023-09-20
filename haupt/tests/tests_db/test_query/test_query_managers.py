import pytest

from flaky import flaky

from clipped.utils.tz import get_datetime_from_now

from django.conf import settings
from django.db.models import Q

from haupt.db.models.runs import Run
from haupt.db.query_managers.run import RunQueryManager
from polyaxon._pql.builder import (
    ArrayCondition,
    ComparisonCondition,
    DateTimeCondition,
    KeysCondition,
    QueryCondSpec,
    SearchCondition,
    ValueCondition,
)
from polyaxon._pql.parser import QueryOpSpec
from polyaxon.exceptions import PQLException
from tests.tests_db.test_query.base import BaseTestQuery


class TestQueryManager(BaseTestQuery):
    def setUp(self):
        super().setUp()
        self.query1 = "updated_at:<=2020-10-10,started_at:>2010-10-10,started_at:~2016-10-01 10:10"
        self.query12 = "created_at:2020-10-10"
        self.query2 = "metrics.loss:<=0.8, status:starting|running"
        self.query3 = "finished_at:2012-12-12..2042-12-12"
        self.query4 = "tags:~tag1|tag2,tags:tag3"
        self.query5 = "name:%foo%,description:~bal%"
        self.query6 = "foobar:2012-12-12..2042-12-12"
        self.query7 = "metrics.loss:nil, status:~nil"

    def test_managers(self):
        assert RunQueryManager.NAME == "run"

    def test_tokenize(self):
        tokenized_query = RunQueryManager.tokenize(self.query1)
        assert dict(tokenized_query.items()) == {
            "created_at": ["last_month"],  # Default filter
            "updated_at": ["<=2020-10-10"],
            "started_at": [">2010-10-10", "~2016-10-01 10:10"],
        }
        tokenized_query = RunQueryManager.tokenize(self.query12)
        assert dict(tokenized_query.items()) == {
            "created_at": ["2020-10-10"],
        }

        tokenized_query = RunQueryManager.tokenize(self.query2)
        assert dict(tokenized_query) == {
            "created_at": ["last_month"],  # Default filter
            "metrics.loss": ["<=0.8"],
            "status": ["starting|running"],
        }

        tokenized_query = RunQueryManager.tokenize(self.query3)
        assert tokenized_query == {
            "created_at": ["last_month"],  # Default filter
            "finished_at": ["2012-12-12..2042-12-12"],
        }

        tokenized_query = RunQueryManager.tokenize(self.query4)
        assert tokenized_query == {
            "created_at": ["last_month"],  # Default filter
            "tags": ["~tag1|tag2", "tag3"],
        }

        tokenized_query = RunQueryManager.tokenize(self.query5)
        assert tokenized_query == {
            "created_at": ["last_month"],  # Default filter
            "name": ["%foo%"],
            "description": ["~bal%"],
        }

        with self.assertRaises(PQLException):
            RunQueryManager.tokenize(self.query6)

        tokenized_query = RunQueryManager.tokenize(self.query7)
        assert dict(tokenized_query) == {
            "created_at": ["last_month"],  # Default filter
            "metrics.loss": ["nil"],
            "status": ["~nil"],
        }

    def test_parse(self):
        tokenized_query = RunQueryManager.tokenize(self.query1)
        parsed_query = RunQueryManager.parse(tokenized_query)
        assert parsed_query == {
            "updated_at": [QueryOpSpec(op="<=", negation=False, params="2020-10-10")],
            "started_at": [
                QueryOpSpec(op=">", negation=False, params="2010-10-10"),
                QueryOpSpec(op="=", negation=True, params="2016-10-01 10:10"),
            ],
            # Default filter
            "created_at": [QueryOpSpec(op="=", negation=False, params="last_month")],
        }
        tokenized_query = RunQueryManager.tokenize(self.query12)
        parsed_query = RunQueryManager.parse(tokenized_query)
        assert parsed_query == {
            "created_at": [QueryOpSpec(op="=", negation=False, params="2020-10-10")],
        }

        tokenized_query = RunQueryManager.tokenize(self.query2)
        parsed_query = RunQueryManager.parse(tokenized_query)
        assert parsed_query == {
            "metrics.loss": [QueryOpSpec(op="<=", negation=False, params=0.8)],
            "status": [
                QueryOpSpec(op="|", negation=False, params=["starting", "running"])
            ],
            # Default filter
            "created_at": [QueryOpSpec(op="=", negation=False, params="last_month")],
        }

        tokenized_query = RunQueryManager.tokenize(self.query3)
        parsed_query = RunQueryManager.parse(tokenized_query)
        assert parsed_query == {
            "finished_at": [
                QueryOpSpec("..", False, params=["2012-12-12", "2042-12-12"])
            ],
            # Default filter
            "created_at": [QueryOpSpec(op="=", negation=False, params="last_month")],
        }

        tokenized_query = RunQueryManager.tokenize(self.query4)
        parsed_query = RunQueryManager.parse(tokenized_query)
        assert parsed_query == {
            "tags": [
                QueryOpSpec("|", True, params=["tag1", "tag2"]),
                QueryOpSpec("=", False, params="tag3"),
            ],
            # Default filter
            "created_at": [QueryOpSpec(op="=", negation=False, params="last_month")],
        }

        tokenized_query = RunQueryManager.tokenize(self.query5)
        parsed_query = RunQueryManager.parse(tokenized_query)
        assert parsed_query == {
            "name": [QueryOpSpec("%%", False, params="foo")],
            "description": [QueryOpSpec("_%", True, params="bal")],
            # Default filter
            "created_at": [QueryOpSpec(op="=", negation=False, params="last_month")],
        }

    def test_build(self):
        tokenized_query = RunQueryManager.tokenize(self.query1)
        parsed_query = RunQueryManager.parse(tokenized_query)
        built_query = RunQueryManager.build(parsed_query)
        assert built_query == {
            "updated_at": [
                QueryCondSpec(
                    DateTimeCondition(op="<=", negation=False), params="2020-10-10"
                )
            ],
            "started_at": [
                QueryCondSpec(
                    DateTimeCondition(op=">", negation=False), params="2010-10-10"
                ),
                QueryCondSpec(
                    DateTimeCondition(op="=", negation=True), params="2016-10-01 10:10"
                ),
            ],
            # Default filter
            "created_at": [
                QueryCondSpec(
                    DateTimeCondition(op="=", negation=False), params="last_month"
                )
            ],
        }

        tokenized_query = RunQueryManager.tokenize(self.query12)
        parsed_query = RunQueryManager.parse(tokenized_query)
        built_query = RunQueryManager.build(parsed_query)
        assert built_query == {
            "created_at": [
                QueryCondSpec(
                    DateTimeCondition(op="=", negation=False), params="2020-10-10"
                )
            ],
        }

        tokenized_query = RunQueryManager.tokenize(self.query2)
        parsed_query = RunQueryManager.parse(tokenized_query)
        built_query = RunQueryManager.build(parsed_query)
        assert built_query == {
            "metrics.loss": [
                QueryCondSpec(ComparisonCondition(op="<=", negation=False), params=0.8)
            ],
            "status": [
                QueryCondSpec(
                    ValueCondition(op="|", negation=False),
                    params=["starting", "running"],
                )
            ],
            # Default filter
            "created_at": [
                QueryCondSpec(
                    DateTimeCondition(op="=", negation=False), params="last_month"
                )
            ],
        }

        tokenized_query = RunQueryManager.tokenize(self.query3)
        parsed_query = RunQueryManager.parse(tokenized_query)
        built_query = RunQueryManager.build(parsed_query)
        assert built_query == {
            "finished_at": [
                QueryCondSpec(
                    DateTimeCondition(op="..", negation=False),
                    params=["2012-12-12", "2042-12-12"],
                )
            ],
            # Default filter
            "created_at": [
                QueryCondSpec(
                    DateTimeCondition(op="=", negation=False), params="last_month"
                )
            ],
        }

        # Current tags condition
        original_condition = RunQueryManager.CONDITIONS_BY_FIELD["tags"]

        # Set to array condition
        if settings.DB_ENGINE_NAME != "sqlite":
            RunQueryManager.CONDITIONS_BY_FIELD["tags"] = ArrayCondition
            tokenized_query = RunQueryManager.tokenize(self.query4)
            parsed_query = RunQueryManager.parse(tokenized_query)
            built_query = RunQueryManager.build(parsed_query)
            assert built_query == {
                "tags": [
                    QueryCondSpec(
                        ArrayCondition(op="|", negation=True), params=["tag1", "tag2"]
                    ),
                    QueryCondSpec(
                        ArrayCondition(op="=", negation=False), params="tag3"
                    ),
                ],
                # Default filter
                "created_at": [
                    QueryCondSpec(
                        DateTimeCondition(op="=", negation=False),
                        params="last_month",
                    )
                ],
            }

        # Set to different condition
        RunQueryManager.CONDITIONS_BY_FIELD["tags"] = KeysCondition
        tokenized_query = RunQueryManager.tokenize(self.query4)
        parsed_query = RunQueryManager.parse(tokenized_query)
        built_query = RunQueryManager.build(parsed_query)
        assert built_query == {
            "tags": [
                QueryCondSpec(
                    KeysCondition(op="|", negation=True), params=["tag1", "tag2"]
                ),
                QueryCondSpec(KeysCondition(op="=", negation=False), params="tag3"),
            ],
            # Default filter
            "created_at": [
                QueryCondSpec(
                    DateTimeCondition(op="=", negation=False), params="last_month"
                )
            ],
        }

        # Reset to original condition
        RunQueryManager.CONDITIONS_BY_FIELD["tags"] = original_condition

        tokenized_query = RunQueryManager.tokenize(self.query5)
        parsed_query = RunQueryManager.parse(tokenized_query)
        built_query = RunQueryManager.build(parsed_query)
        assert built_query == {
            "name": [
                QueryCondSpec(SearchCondition(op="%%", negation=False), params="foo")
            ],
            "description": [
                QueryCondSpec(SearchCondition(op="_%", negation=True), params="bal")
            ],
            # Default filter
            "created_at": [
                QueryCondSpec(
                    DateTimeCondition(op="=", negation=False), params="last_month"
                )
            ],
        }

        tokenized_query = RunQueryManager.tokenize(self.query7)
        parsed_query = RunQueryManager.parse(tokenized_query)
        built_query = RunQueryManager.build(parsed_query)
        assert built_query == {
            "metrics.loss": [
                QueryCondSpec(SearchCondition(op="nil", negation=False), params=None)
            ],
            "status": [
                QueryCondSpec(SearchCondition(op="nil", negation=True), params=None)
            ],
            # Default filter
            "created_at": [
                QueryCondSpec(
                    DateTimeCondition(op="=", negation=False), params="last_month"
                )
            ],
        }

    def test_handle(self):
        tokenized_query = RunQueryManager.tokenize(self.query1)
        parsed_query = RunQueryManager.parse(tokenized_query)
        built_query = RunQueryManager.build(parsed_query)
        assert built_query == RunQueryManager.handle_query(self.query1)

        tokenized_query = RunQueryManager.tokenize(self.query12)
        parsed_query = RunQueryManager.parse(tokenized_query)
        built_query = RunQueryManager.build(parsed_query)
        assert built_query == RunQueryManager.handle_query(self.query12)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    @flaky(max_runs=3)
    def test_apply(self):
        result_queryset = RunQueryManager.apply(
            query_spec=self.query1, queryset=Run.objects
        )
        expected_query = Run.objects.filter(
            Q(updated_at__lte="2020-10-10"),
            Q(started_at__gt="2010-10-10"),
            ~Q(
                Q(started_at__date="2016-10-01"),
                Q(started_at__hour="10"),
                Q(started_at__minute="10"),
            ),
            # Default filter
            Q(created_at__gte=get_datetime_from_now(days=30).date().isoformat()),
        )
        assert str(result_queryset.query) == str(expected_query.query)

        result_queryset = RunQueryManager.apply(
            query_spec=self.query12, queryset=Run.objects
        )
        expected_query = Run.objects.filter(
            Q(created_at__date="2020-10-10"),
        )
        assert str(result_queryset.query) == str(expected_query.query)

        result_queryset = RunQueryManager.apply(
            query_spec=self.query2, queryset=Run.objects
        )
        expected_query = Run.objects.filter(
            Q(outputs__loss__lte=0.8),
            Q(status__in=["starting", "running"]),
            # Default filter
            Q(created_at__gte=get_datetime_from_now(days=30).date().isoformat()),
        )
        assert str(result_queryset.query) == str(expected_query.query)

        result_queryset = RunQueryManager.apply(
            query_spec=self.query4, queryset=Run.objects
        )

        if settings.DB_ENGINE_NAME == "sqlite":
            expected_query = Run.objects.filter(
                ~Q(tags__has_any_keys=["tag1", "tag2"]),
                Q(tags__has_key=["tag3"]),
                # Default filter
                Q(created_at__gte=get_datetime_from_now(days=30).date().isoformat()),
            )
        else:
            expected_query = Run.objects.filter(
                ~Q(tags__overlap=["tag1", "tag2"]),
                Q(tags__contains=["tag3"]),
                # Default filter
                Q(created_at__gte=get_datetime_from_now(days=30).date().isoformat()),
            )
        assert str(result_queryset.query) == str(expected_query.query)

        result_queryset = RunQueryManager.apply(
            query_spec=self.query5, queryset=Run.objects
        )
        expected_query = Run.objects.filter(
            Q(name__icontains="foo"),
            ~Q(description__istartswith="bal"),
            # Default filter
            Q(created_at__gte=get_datetime_from_now(days=30).date().isoformat()),
        )

        assert str(result_queryset.query) == str(expected_query.query)

        result_queryset = RunQueryManager.apply(
            query_spec=self.query7, queryset=Run.objects
        )
        expected_query = Run.objects.filter(
            Q(outputs__loss__isnull=True),
            Q(status__isnull=False),
            # Default filter
            Q(created_at__gte=get_datetime_from_now(days=30).date().isoformat()),
        )
        assert str(result_queryset.query) == str(expected_query.query)


del BaseTestQuery
