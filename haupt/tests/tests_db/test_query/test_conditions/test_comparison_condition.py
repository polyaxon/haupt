from django.conf import settings
from django.db.models import Q

from haupt.db.factories.runs import RunFactory
from haupt.db.models.runs import Run
from polyaxon._pql.builder import ComparisonCondition
from polyaxon.schemas import ManagedBy
from tests.tests_db.test_query.base import BaseTestQuery

# pylint:disable=protected-access


class TestComparisonCondition(BaseTestQuery):
    def test_comparison_operators(self):
        op = ComparisonCondition._lt_operator(
            "field", "value", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__lt="value")
        op = ComparisonCondition._gt_operator(
            "field", "value", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__gt="value")
        op = ComparisonCondition._lte_operator(
            "field", "value", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__lte="value")
        op = ComparisonCondition._gte_operator(
            "field", "value", query_backend=Q, timezone=settings.TIME_ZONE
        )
        assert op == Q(field__gte="value")

    def test_comparison_condition_init_with_correct_operator(self):
        lt_cond = ComparisonCondition(op="lt")
        assert lt_cond.operator == ComparisonCondition._lt_operator
        nlt_cond = ComparisonCondition(op="lt", negation=True)
        assert nlt_cond.operator == ComparisonCondition._gte_operator

        gt_cond = ComparisonCondition(op="gt")
        assert gt_cond.operator == ComparisonCondition._gt_operator
        ngt_cond = ComparisonCondition(op="gt", negation=True)
        assert ngt_cond.operator == ComparisonCondition._lte_operator

        lte_cond = ComparisonCondition(op="lte")
        assert lte_cond.operator == ComparisonCondition._lte_operator
        nlte_cond = ComparisonCondition(op="lte", negation=True)
        assert nlte_cond.operator == ComparisonCondition._gt_operator

        gte_cond = ComparisonCondition(op="gte")
        assert gte_cond.operator == ComparisonCondition._gte_operator
        ngte_cond = ComparisonCondition(op="gte", negation=True)
        assert ngte_cond.operator == ComparisonCondition._lt_operator

    def test_comparison_apply(self):
        self.run.inputs = {"rate": 1, "loss": "foo"}
        self.run.save()
        RunFactory(
            project=self.project,
            managed_by=ManagedBy.USER,
            outputs={"loss": 0.1, "step": 1},
        )
        RunFactory(
            project=self.project,
            managed_by=ManagedBy.USER,
            outputs={"loss": 0.3, "step": 10},
        )
        RunFactory(
            project=self.project,
            managed_by=ManagedBy.USER,
            inputs={"rate": -1, "loss": "bar"},
        )

        RunFactory(
            project=self.project,
            managed_by=ManagedBy.USER,
            outputs={"loss": 0.9, "step": 100},
        )

        eq_cond = ComparisonCondition(op="eq")
        neq_cond = ComparisonCondition(op="eq", negation=True)
        lt_cond = ComparisonCondition(op="lt")
        lte_cond = ComparisonCondition(op="lte")
        gt_cond = ComparisonCondition(op="gt")
        gte_cond = ComparisonCondition(op="gte")

        # eq
        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.1,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.2,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = eq_cond.apply(
            queryset=Run.objects,
            name="outputs__step",
            params=10,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        # neq must use the table directly
        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="inputs__rate",
            params=1,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 4

        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="inputs__rate",
            params=-1,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 4

        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="inputs__rate",
            params=-12,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 5

        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="inputs__loss",
            params="foo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 4

        queryset = neq_cond.apply(
            queryset=Run.objects,
            name="inputs__loss",
            params="moo",
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 5

        # lt
        queryset = lt_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.1,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        queryset = lt_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.2,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = lt_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.9,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        # lte
        queryset = lte_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.1,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = lte_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.2,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1

        queryset = lte_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.9,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 3

        # gt
        queryset = gt_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.1,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = gt_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.2,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = gt_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.9,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 0

        # gte
        queryset = gte_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.1,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 3

        queryset = gte_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.2,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 2

        queryset = gte_cond.apply(
            queryset=Run.objects,
            name="outputs__loss",
            params=0.9,
            query_backend=Q,
            timezone=settings.TIME_ZONE,
        )
        assert queryset.count() == 1


# class TestComparisonCondition(BaseTestQuery):
#     def test_comparison_operators(self):
#         op = ComparisonCondition._lt_operator("field", "value")
#         assert op == Q(field__lt="value")
#         op = ComparisonCondition._gt_operator("field", "value")
#         assert op == Q(field__gt="value")
#         op = ComparisonCondition._lte_operator("field", "value")
#         assert op == Q(field__lte="value")
#         op = ComparisonCondition._gte_operator("field", "value")
#         assert op == Q(field__gte="value")
#
#     def test_comparison_condition_init_with_correct_operator(self):
#         lt_cond = ComparisonCondition(op="lt")
#         assert lt_cond.operator == ComparisonCondition._lt_operator
#         nlt_cond = ComparisonCondition(op="lt", negation=True)
#         assert nlt_cond.operator == ComparisonCondition._gte_operator
#
#         gt_cond = ComparisonCondition(op="gt")
#         assert gt_cond.operator == ComparisonCondition._gt_operator
#         ngt_cond = ComparisonCondition(op="gt", negation=True)
#         assert ngt_cond.operator == ComparisonCondition._lte_operator
#
#         lte_cond = ComparisonCondition(op="lte")
#         assert lte_cond.operator == ComparisonCondition._lte_operator
#         nlte_cond = ComparisonCondition(op="lte", negation=True)
#         assert nlte_cond.operator == ComparisonCondition._gt_operator
#
#         gte_cond = ComparisonCondition(op="gte")
#         assert gte_cond.operator == ComparisonCondition._gte_operator
#         ngte_cond = ComparisonCondition(op="gte", negation=True)
#         assert ngte_cond.operator == ComparisonCondition._lt_operator

# def test_comparison_apply(self):
#     self.run.label_annotations.set(
#         [
#             LabelAnnotation.objects.create(
#                 project=self.project, value=0.1, name="loss"
#             ),
#             LabelAnnotation.objects.create(
#                 project=self.project, name="step", value=1
#             ),
#         ]
#     )
#     self.run.metric_annotations.set(
#         [
#             MetricAnnotation.objects.create(
#                 project=self.project, value=0.1, name="loss"
#             ),
#             MetricAnnotation.objects.create(
#                 project=self.project, name="step", value=1
#             ),
#         ]
#     )
#     run = RunFactory(project=self.project, operation=self.operation)
#     run.label_annotations.set(
#         [
#             LabelAnnotation.objects.create(
#                 project=self.project, value=0.3, name="loss"
#             ),
#             LabelAnnotation.objects.create(
#                 project=self.project, name="step", value=10
#             ),
#         ]
#     )
#     run.metric_annotations.set(
#         [
#             MetricAnnotation.objects.create(
#                 project=self.project, value=0.3, name="loss"
#             ),
#             MetricAnnotation.objects.create(
#                 project=self.project, name="step", value=10
#             ),
#         ]
#     )
#     run = RunFactory(project=self.project, operation=self.operation)
#     run.label_annotations.set(
#         [
#             LabelAnnotation.objects.create(
#                 project=self.project, value=0.9, name="loss"
#             ),
#             LabelAnnotation.objects.create(
#                 project=self.project, name="step", value=100
#             ),
#         ]
#     )
#     run.metric_annotations.set(
#         [
#             MetricAnnotation.objects.create(
#                 project=self.project, value=0.9, name="loss"
#             ),
#             MetricAnnotation.objects.create(
#                 project=self.project, name="step", value=100
#             ),
#         ]
#     )
#     run = RunFactory(project=self.project, operation=self.operation)
#     run.label_annotations.set(
#         [
#             LabelAnnotation.objects.create(
#                 project=self.project, name="rate", value=-1
#             ),
#             LabelAnnotation.objects.create(
#                 project=self.project, name="loss", value="bar"
#             ),
#         ]
#     )
#
#     eq_cond = ComparisonCondition(op="eq")
#     neq_cond = ComparisonCondition(op="eq", negation=True)
#     lt_cond = ComparisonCondition(op="lt")
#     lte_cond = ComparisonCondition(op="lte")
#     gt_cond = ComparisonCondition(op="gt")
#     gte_cond = ComparisonCondition(op="gte")
#
#     # eq
#     queryset = Run.objects.filter(
#         eq_cond.apply_operator(name="label_annotations__value", params=0.1),
#         eq_cond.apply_operator(name="label_annotations__name", params="loss"),
#     )
#     assert queryset.count() == 1
#
#     queryset = Run.objects.filter(
#         eq_cond.apply_operator(name="label_annotations__value", params=0.2),
#         eq_cond.apply_operator(name="label_annotations__name", params="loss"),
#     )
#     assert queryset.count() == 0
#
#     queryset = Run.objects.filter(
#         eq_cond.apply_operator(name="label_annotations__value", params=100),
#         eq_cond.apply_operator(name="label_annotations__name", params="step"),
#     )
#     assert queryset.count() == 1
#
#     # neq must use the table directly
#     queryset = Run.objects.filter(
#         neq_cond.apply_operator(name="label_annotations__value", params=1),
#         eq_cond.apply_operator(name="label_annotations__name", params="rate"),
#     )
#     assert queryset.count() == 1
#
#     queryset = Run.objects.filter(
#         neq_cond.apply_operator(name="label_annotations__value", params=-1)
#     )
#     assert queryset.count() == 3
#
#     # lt
#     queryset = lt_cond.apply(
#         queryset=Run.objects, name="metric_annotations__value", params=0.1
#     )
#     queryset = eq_cond.apply(
#         queryset=queryset, name="metric_annotations__name", params="loss"
#     )
#     assert queryset.count() == 0
#
#     queryset = lt_cond.apply(
#         queryset=Run.objects, name="metric_annotations__value", params=0.2
#     )
#     queryset = eq_cond.apply(
#         queryset=queryset, name="metric_annotations__name", params="loss"
#     )
#     assert queryset.count() == 1
#
#     queryset = lt_cond.apply(
#         queryset=Run.objects, name="metric_annotations__value", params=0.9
#     )
#     queryset = eq_cond.apply(
#         queryset=queryset, name="metric_annotations__name", params="loss"
#     )
#     assert queryset.count() == 2
#
#     # lte
#     queryset = lte_cond.apply(
#         queryset=Run.objects, name="metric_annotations__value", params=0.1
#     )
#     queryset = eq_cond.apply(
#         queryset=queryset, name="metric_annotations__name", params="loss"
#     )
#     assert queryset.count() == 1
#
#     queryset = lte_cond.apply(
#         queryset=Run.objects, name="metric_annotations__value", params=0.2
#     )
#     queryset = eq_cond.apply(
#         queryset=queryset, name="metric_annotations__name", params="loss"
#     )
#     assert queryset.count() == 1
#
#     queryset = lte_cond.apply(
#         queryset=Run.objects, name="metric_annotations__value", params=0.9
#     )
#     queryset = eq_cond.apply(
#         queryset=queryset, name="metric_annotations__name", params="loss"
#     )
#     assert queryset.count() == 3
#
#     # gt
#     queryset = Run.objects.filter(
#         gt_cond.apply_operator(name="metric_annotations__value", params=0.1),
#         eq_cond.apply_operator(name="metric_annotations__name", params="loss"),
#     )
#     assert queryset.count() == 2
#
#     queryset = Run.objects.filter(
#         gt_cond.apply_operator(name="metric_annotations__value", params=0.2),
#         eq_cond.apply_operator(name="metric_annotations__name", params="loss"),
#     )
#     assert queryset.count() == 2
#
#     queryset = Run.objects.filter(
#         gt_cond.apply_operator(name="metric_annotations__value", params=0.9),
#         eq_cond.apply_operator(name="metric_annotations__name", params="loss"),
#     )
#     assert queryset.count() == 0
#
#     # gte
#     queryset = Run.objects.filter(
#         gte_cond.apply_operator(name="metric_annotations__value", params=0.1),
#         eq_cond.apply_operator(name="metric_annotations__name", params="loss"),
#     )
#     assert queryset.count() == 3
#
#     queryset = Run.objects.filter(
#         gte_cond.apply_operator(name="metric_annotations__value", params=0.2),
#         eq_cond.apply_operator(name="metric_annotations__name", params="loss"),
#     )
#     assert queryset.count() == 2
#
#     queryset = Run.objects.filter(
#         gte_cond.apply_operator(name="metric_annotations__value", params=0.9),
#         eq_cond.apply_operator(name="metric_annotations__name", params="loss"),
#     )
#     assert queryset.count() == 1


del BaseTestQuery
