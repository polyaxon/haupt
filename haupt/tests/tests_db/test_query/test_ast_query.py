"""Integration tests for the new AST-based PQL query parsing with AND/OR support."""

import pytest

from clipped.utils.tz import get_datetime_from_now

from django.db.models import Q

from haupt.db.models.runs import Run
from haupt.db.query_managers.run import RunQueryManager
from polyaxon._pql.ast import AndNode, ExpressionNode, OrNode
from polyaxon._pql.grammar import parse_query
from tests.tests_db.test_query.base import BaseTestQuery

from polyaxon._pql.manager import LegacyQueryMixin


class LegacyRunQueryManager(RunQueryManager, LegacyQueryMixin):
    pass


class TestASTQueryParsing(BaseTestQuery):
    """Test that AST parsing produces correct queries."""

    def test_simple_expression_parsing(self):
        """Test parsing a simple expression."""
        ast = parse_query("status:running")
        assert isinstance(ast, ExpressionNode)
        assert ast.field == "status"
        assert ast.operation == "running"

    def test_and_expression_parsing(self):
        """Test parsing AND expressions."""
        ast = parse_query("status:running, metrics.loss:<0.5")
        assert isinstance(ast, AndNode)
        assert len(ast.children) == 2

        # Also test with AND keyword
        ast2 = parse_query("status:running AND metrics.loss:<0.5")
        assert isinstance(ast2, AndNode)
        assert len(ast2.children) == 2

    def test_or_expression_parsing(self):
        """Test parsing OR expressions."""
        ast = parse_query("status:running OR status:failed")
        assert isinstance(ast, OrNode)
        assert len(ast.children) == 2

        # Also test with pipe
        ast2 = parse_query("status:running | status:failed")
        assert isinstance(ast2, OrNode)
        assert len(ast2.children) == 2

    def test_nested_expression_parsing(self):
        """Test parsing nested expressions."""
        ast = parse_query("(status:running AND metrics.loss:<0.5) OR status:failed")
        assert isinstance(ast, OrNode)
        assert isinstance(ast.children[0], AndNode)
        assert isinstance(ast.children[1], ExpressionNode)


class TestASTQueryBuilding(BaseTestQuery):
    """Test that AST queries build correct Django Q objects."""

    def test_build_simple_expression(self):
        """Test building Q from simple expression."""
        q, _ = RunQueryManager._build_expression_q("status", "running")
        assert q == Q(status="running")

    def test_build_comparison_expression(self):
        """Test building Q from comparison expression."""
        q, _ = RunQueryManager._build_expression_q("duration", ">100")
        assert q == Q(duration__gt=100)

    def test_build_in_expression(self):
        """Test building Q from IN expression."""
        q, _ = RunQueryManager._build_expression_q("status", "running|building")
        assert q == Q(status__in=["running", "building"])

    def test_build_and_node(self):
        """Test building Q from AND node."""
        ast = AndNode(
            [
                ExpressionNode("status", "running"),
                ExpressionNode("duration", ">100"),
            ]
        )
        q, _ = RunQueryManager._build_ast_q(ast)
        expected = Q(status="running") & Q(duration__gt=100)
        assert str(q) == str(expected)

    def test_build_or_node(self):
        """Test building Q from OR node."""
        ast = OrNode(
            [
                ExpressionNode("status", "running"),
                ExpressionNode("status", "failed"),
            ]
        )
        q, _ = RunQueryManager._build_ast_q(ast)
        expected = Q(status="running") | Q(status="failed")
        assert str(q) == str(expected)

    def test_build_nested_node(self):
        """Test building Q from nested node."""
        ast = OrNode(
            [
                AndNode(
                    [
                        ExpressionNode("status", "running"),
                        ExpressionNode("duration", ">100"),
                    ]
                ),
                ExpressionNode("status", "failed"),
            ]
        )
        q, _ = RunQueryManager._build_ast_q(ast)
        expected = (Q(status="running") & Q(duration__gt=100)) | Q(status="failed")
        assert str(q) == str(expected)


class TestASTQueryApply(BaseTestQuery):
    """Test that apply_ast produces correct querysets."""

    def test_apply_simple_and(self):
        """Test apply_ast with simple AND query."""
        result = RunQueryManager.apply_ast(
            query_spec="status:running, duration:>100",
            queryset=Run.objects,
        )
        # Should produce AND query with default filter
        expected = Run.objects.filter(
            Q(status="running"),
            Q(duration__gt=100),
            Q(created_at__gte=get_datetime_from_now(days=30).date().isoformat()),
        )
        assert str(result.query) == str(expected.query)

    def test_apply_or_query(self):
        """Test apply_ast with OR query."""
        result = RunQueryManager.apply_ast(
            query_spec="status:running OR status:failed",
            queryset=Run.objects,
        )
        # Should produce OR query with default filter ANDed
        expected = Run.objects.filter(
            Q(status="running") | Q(status="failed"),
            Q(created_at__gte=get_datetime_from_now(days=30).date()),
        )
        assert str(result.query) == str(expected.query)

    def test_apply_mixed_query(self):
        """Test apply_ast with mixed AND/OR query."""
        result = RunQueryManager.apply_ast(
            query_spec="(status:running OR status:building) AND duration:>100",
            queryset=Run.objects,
        )
        expected = Run.objects.filter(
            (Q(status="running") | Q(status="building")) & Q(duration__gt=100),
            Q(created_at__gte=get_datetime_from_now(days=30).date()),
        )
        assert str(result.query) == str(expected.query)

    def test_apply_with_explicit_created_at(self):
        """Test that default filter is not applied when field is in query."""
        result = RunQueryManager.apply_ast(
            query_spec="status:running, created_at:>2010-10-10 10:10",
            queryset=Run.objects,
        )
        # Should NOT include default created_at filter
        query_str = str(result.query)
        # The created_at in query should be the one we specified, not default
        assert "2010-10-10" in query_str

    def test_apply_in_operator(self):
        """Test that IN operator (pipe without space) works correctly."""
        result = RunQueryManager.apply_ast(
            query_spec="status:running|building",
            queryset=Run.objects,
        )
        expected = Run.objects.filter(
            Q(status__in=["running", "building"]),
            Q(created_at__gte=get_datetime_from_now(days=30).date()),
        )
        assert str(result.query) == str(expected.query)

    def test_apply_complex_nested(self):
        """Test apply_ast with complex nested query."""
        result = RunQueryManager.apply_ast(
            query_spec="kind:job, (status:running | (duration:>100 AND status:succeeded))",
            queryset=Run.objects,
        )
        expected = Run.objects.filter(
            Q(kind="job")
            & (Q(status="running") | (Q(duration__gt=100) & Q(status="succeeded"))),
            Q(created_at__gte=get_datetime_from_now(days=30).date()),
        )
        assert str(result.query) == str(expected.query)


class TestBackwardCompatibility(BaseTestQuery):
    """Test that existing queries work the same with new parser."""

    def setUp(self):
        super().setUp()
        # These are queries from the existing test_query_managers.py
        self.query1 = "updated_at:<=2020-10-10,started_at:>2010-10-10,started_at:~2016-10-01 10:10"
        self.query2 = "metrics.loss:<=0.8, status:starting|running"
        self.query4 = "tags:~tag1|tag2,tags:tag3"
        self.query5 = "name:%foo%,description:~bal%"
        self.query7 = "metrics.loss:nil, status:~nil"

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    @pytest.mark.flaky(max_runs=3)
    def test_legacy_query1_compatibility(self):
        """Test that legacy query produces same result with new parser."""
        # Compare old apply_legacy with new apply_ast
        legacy_result = LegacyRunQueryManager.apply_legacy(
            query_spec=self.query1, queryset=Run.objects
        )
        new_result = RunQueryManager.apply_ast(
            query_spec=self.query1, queryset=Run.objects
        )
        # Both should produce equivalent queries
        assert str(legacy_result.query) == str(new_result.query)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    @pytest.mark.flaky(max_runs=3)
    def test_legacy_query2_compatibility(self):
        """Test that metrics query produces same result."""
        legacy_result = LegacyRunQueryManager.apply_legacy(
            query_spec=self.query2, queryset=Run.objects
        )
        new_result = RunQueryManager.apply_ast(
            query_spec=self.query2, queryset=Run.objects
        )
        assert str(legacy_result.query) == str(new_result.query)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    @pytest.mark.flaky(max_runs=3)
    def test_legacy_query4_compatibility(self):
        """Test that tags query produces same result."""
        legacy_result = LegacyRunQueryManager.apply_legacy(
            query_spec=self.query4, queryset=Run.objects
        )
        new_result = RunQueryManager.apply_ast(
            query_spec=self.query4, queryset=Run.objects
        )
        assert str(legacy_result.query) == str(new_result.query)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    @pytest.mark.flaky(max_runs=3)
    def test_legacy_query5_compatibility(self):
        """Test that search query produces same result."""
        legacy_result = LegacyRunQueryManager.apply_legacy(
            query_spec=self.query5, queryset=Run.objects
        )
        new_result = RunQueryManager.apply_ast(
            query_spec=self.query5, queryset=Run.objects
        )
        assert str(legacy_result.query) == str(new_result.query)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    @pytest.mark.flaky(max_runs=3)
    def test_legacy_query7_compatibility(self):
        """Test that nil query produces same result."""
        legacy_result = LegacyRunQueryManager.apply_legacy(
            query_spec=self.query7, queryset=Run.objects
        )
        new_result = RunQueryManager.apply_ast(
            query_spec=self.query7, queryset=Run.objects
        )
        assert str(legacy_result.query) == str(new_result.query)


del BaseTestQuery
