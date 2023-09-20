from django.conf import settings
from django.db.models import Q

from haupt.db.models.runs import Run
from polyaxon._pql.builder import ArrayCondition, KeysCondition
from tests.tests_db.test_query.base import BaseTestQuery

# pylint:disable=protected-access


class TestArrayOrKeysCondition(BaseTestQuery):
    def test_equality_operators(self):
        # Array
        op = ArrayCondition._eq_operator(
            "field", "value", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__contains=["value"])
        op = ArrayCondition._neq_operator(
            "field", "value", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == ~Q(field__contains=["value"])

        # Keys
        op = KeysCondition._eq_operator(
            "field", "value", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__has_key=["value"])
        op = KeysCondition._neq_operator(
            "field", "value", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == ~Q(field__has_key=["value"])

    def test_equality_condition_init_with_correct_operator(self):
        # Array
        eq_cond = ArrayCondition(op="eq")
        assert eq_cond.operator == ArrayCondition._eq_operator
        neq_cond = ArrayCondition(op="eq", negation=True)
        assert neq_cond.operator == ArrayCondition._neq_operator

        # Keys
        eq_cond = KeysCondition(op="eq")
        assert eq_cond.operator == KeysCondition._eq_operator
        neq_cond = KeysCondition(op="eq", negation=True)
        assert neq_cond.operator == KeysCondition._neq_operator

    def test_in_operators(self):
        # Array
        op = ArrayCondition._in_operator(
            "field", ["value"], query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__overlap=["value"])
        op = ArrayCondition._nin_operator(
            "field", ["value"], query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == ~Q(field__overlap=["value"])

        # Keys
        op = KeysCondition._in_operator(
            "field", ["value"], query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__has_any_keys=["value"])
        op = KeysCondition._nin_operator(
            "field", ["value"], query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == ~Q(field__has_any_keys=["value"])

    def test_in_condition_init_with_correct_operator(self):
        # Array
        eq_cond = ArrayCondition(op="in")
        assert eq_cond.operator == ArrayCondition._in_operator
        neq_cond = ArrayCondition(op="in", negation=True)
        assert neq_cond.operator == ArrayCondition._nin_operator

        # Keys
        eq_cond = KeysCondition(op="in")
        assert eq_cond.operator == KeysCondition._in_operator
        neq_cond = KeysCondition(op="in", negation=True)
        assert neq_cond.operator == KeysCondition._nin_operator

    def test_equality_apply(self):
        if settings.DB_ENGINE_NAME == "sqlite":
            eq_cond = KeysCondition(op="eq")
            neq_cond = KeysCondition(op="eq", negation=True)
            self.run.tags = {"foo": ""}
            self.run.save(update_fields=["tags"])
        else:
            eq_cond = ArrayCondition(op="eq")
            neq_cond = ArrayCondition(op="eq", negation=True)
            self.run.tags = ["foo"]
            self.run.save(update_fields=["tags"])

        # eq
        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="tags",
            params="foo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="tags",
            params="baz",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        # neq
        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="tags",
            params="foo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="tags",
            params="baz",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

    def test_in_apply(self):
        if settings.DB_ENGINE_NAME == "sqlite":
            eq_cond = KeysCondition(op="eq")
            neq_cond = KeysCondition(op="eq", negation=True)
            self.run.tags = {"foo": "", "bar": "", "moo": ""}
            self.run.save(update_fields=["tags"])
        else:
            eq_cond = ArrayCondition(op="eq")
            neq_cond = ArrayCondition(op="eq", negation=True)
            self.run.tags = ["foo", "bar", "moo"]
            self.run.save(update_fields=["tags"])

        # eq
        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="tags",
            params=["foo"],
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="tags",
            params="baz",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        # neq
        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="tags",
            params=["foo"],
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="tags",
            params="baz",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1


del BaseTestQuery
