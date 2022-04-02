#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.conf import settings
from django.db.models import Q

from db.models.runs import Run
from polyaxon.pql.builder import BoolCondition
from tests.tests_db.test_query.base import BaseTestQuery

# pylint:disable=protected-access


class TestBoolCondition(BaseTestQuery):
    def test_bool_operators(self):
        op = BoolCondition._eq_operator(
            "field", "false", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field=False)
        op = BoolCondition._eq_operator(
            "field", 0, query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field=False)
        op = BoolCondition._eq_operator(
            "field", False, query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field=False)
        op = BoolCondition._neq_operator(
            "field", "true", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == ~Q(field=True)
        op = BoolCondition._neq_operator(
            "field", 1, query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == ~Q(field=True)
        op = BoolCondition._neq_operator(
            "field", True, query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == ~Q(field=True)

    def test_bool_condition_init_with_correct_operator(self):
        eq_cond = BoolCondition(op="eq")
        assert eq_cond.operator == BoolCondition._eq_operator
        neq_cond = BoolCondition(op="eq", negation=True)
        assert neq_cond.operator == BoolCondition._neq_operator

    def test_bool_apply(self):
        eq_cond = BoolCondition(op="eq")
        neq_cond = BoolCondition(op="eq", negation=True)

        # eq
        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="is_managed",
            params=0,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1
        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="is_managed",
            params="false",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1
        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="is_managed",
            params=False,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="is_managed",
            params=1,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0
        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="is_managed",
            params="true",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0
        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="is_managed",
            params=True,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        # neq
        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="is_managed",
            params=0,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0
        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="is_managed",
            params="false",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0
        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="is_managed",
            params=False,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="is_managed",
            params=1,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1
        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="is_managed",
            params="true",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1
        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="is_managed",
            params=True,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1


del BaseTestQuery
