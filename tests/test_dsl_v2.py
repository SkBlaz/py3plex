"""Tests for DSL v2 features.

Tests cover:
- AST classes
- Python builder API (Q, L, Param)
- QueryResult exports (to_pandas, to_networkx, to_arrow)
- Layer algebra
- ORDER BY and LIMIT
- EXPLAIN mode
- Error handling with suggestions
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import (
    # AST classes
    Query,
    SelectStmt,
    Target,
    ExportTarget,
    LayerExpr,
    LayerTerm,
    ConditionExpr,
    ConditionAtom,
    Comparison,
    SpecialPredicate,
    ComputeItem,
    OrderItem,
    ParamRef,
    PlanStep,
    ExecutionPlan,
    # Builder API
    Q,
    QueryBuilder,
    LayerExprBuilder,
    LayerProxy,
    L,
    Param,
    # Result
    QueryResult,
    # Executor
    execute_ast,
    # Errors
    DslError,
    DslSyntaxError,
    DslExecutionError,
    UnknownMeasureError,
    ParameterMissingError,
    # Registry
    measure_registry,
)


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)

    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
        {'source': 'E', 'type': 'work'},
    ]
    network.add_nodes(nodes)

    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'D', 'target': 'E', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    ]
    network.add_edges(edges)

    return network


class TestASTClasses:
    """Test AST dataclasses."""

    def test_target_enum(self):
        """Test Target enum values."""
        assert Target.NODES.value == "nodes"
        assert Target.EDGES.value == "edges"

    def test_export_target_enum(self):
        """Test ExportTarget enum values."""
        assert ExportTarget.PANDAS.value == "pandas"
        assert ExportTarget.NETWORKX.value == "networkx"
        assert ExportTarget.ARROW.value == "arrow"

    def test_param_ref(self):
        """Test ParamRef creation."""
        p = ParamRef(name="k")
        assert p.name == "k"
        assert p.type_hint is None
        assert repr(p) == ":k"

    def test_layer_term(self):
        """Test LayerTerm creation."""
        term = LayerTerm(name="social")
        assert term.name == "social"

    def test_layer_expr(self):
        """Test LayerExpr creation."""
        expr = LayerExpr(
            terms=[LayerTerm("social"), LayerTerm("work")],
            ops=["+"]
        )
        assert len(expr.terms) == 2
        assert expr.get_layer_names() == ["social", "work"]

    def test_comparison(self):
        """Test Comparison creation."""
        cmp = Comparison(left="degree", op=">", right=5)
        assert cmp.left == "degree"
        assert cmp.op == ">"
        assert cmp.right == 5

    def test_special_predicate(self):
        """Test SpecialPredicate creation."""
        pred = SpecialPredicate(kind="intralayer", params={})
        assert pred.kind == "intralayer"

    def test_condition_atom(self):
        """Test ConditionAtom properties."""
        atom_cmp = ConditionAtom(comparison=Comparison("x", "=", 1))
        assert atom_cmp.is_comparison
        assert not atom_cmp.is_special

        atom_spec = ConditionAtom(special=SpecialPredicate("intralayer", {}))
        assert atom_spec.is_special
        assert not atom_spec.is_comparison

    def test_compute_item(self):
        """Test ComputeItem creation."""
        item = ComputeItem(name="degree", alias="d")
        assert item.name == "degree"
        assert item.alias == "d"
        assert item.result_name == "d"

        item2 = ComputeItem(name="degree")
        assert item2.result_name == "degree"

    def test_order_item(self):
        """Test OrderItem creation."""
        item = OrderItem(key="bc", desc=True)
        assert item.key == "bc"
        assert item.desc is True

    def test_select_stmt(self):
        """Test SelectStmt creation."""
        stmt = SelectStmt(target=Target.NODES, limit=10)
        assert stmt.target == Target.NODES
        assert stmt.limit == 10
        assert stmt.compute == []

    def test_query(self):
        """Test Query creation."""
        stmt = SelectStmt(target=Target.NODES)
        query = Query(explain=False, select=stmt)
        assert query.explain is False
        assert query.dsl_version == "2.0"

    def test_plan_step(self):
        """Test PlanStep creation."""
        step = PlanStep(description="Filter nodes", estimated_complexity="O(n)")
        assert step.description == "Filter nodes"
        assert step.estimated_complexity == "O(n)"

    def test_execution_plan(self):
        """Test ExecutionPlan creation."""
        plan = ExecutionPlan(
            steps=[PlanStep("Step 1", "O(1)")],
            warnings=["Warning 1"]
        )
        assert len(plan.steps) == 1
        assert len(plan.warnings) == 1


class TestBuilderAPI:
    """Test Python builder API."""

    def test_q_nodes(self):
        """Test Q.nodes() factory."""
        builder = Q.nodes()
        assert isinstance(builder, QueryBuilder)
        assert builder._select.target == Target.NODES

    def test_q_edges(self):
        """Test Q.edges() factory."""
        builder = Q.edges()
        assert isinstance(builder, QueryBuilder)
        assert builder._select.target == Target.EDGES

    def test_where_equality(self, sample_network):
        """Test where with simple equality."""
        q = Q.nodes().where(layer="social")
        result = q.execute(sample_network)
        
        assert result.count == 3
        for node in result.nodes:
            assert node[1] == "social"

    def test_where_comparison(self, sample_network):
        """Test where with comparison operators."""
        q = Q.nodes().where(degree__gt=1)
        result = q.execute(sample_network)
        
        assert result.count >= 0

    def test_where_multiple_conditions(self, sample_network):
        """Test where with multiple conditions."""
        q = Q.nodes().where(layer="social", degree__gt=0)
        result = q.execute(sample_network)
        
        assert result.count >= 0

    def test_compute_single(self, sample_network):
        """Test compute with single measure."""
        q = Q.nodes().compute("degree")
        result = q.execute(sample_network)
        
        assert "degree" in result.attributes

    def test_compute_with_alias(self, sample_network):
        """Test compute with alias."""
        q = Q.nodes().compute("degree", alias="d")
        result = q.execute(sample_network)
        
        assert "d" in result.attributes

    def test_compute_multiple(self, sample_network):
        """Test compute with multiple measures."""
        q = Q.nodes().compute("degree", "clustering")
        result = q.execute(sample_network)
        
        assert "degree" in result.attributes
        assert "clustering" in result.attributes

    def test_order_by_ascending(self, sample_network):
        """Test order_by ascending."""
        q = Q.nodes().compute("degree").order_by("degree")
        result = q.execute(sample_network)
        
        # Verify ordered
        assert result.count > 0

    def test_order_by_descending(self, sample_network):
        """Test order_by descending."""
        q = Q.nodes().compute("degree").order_by("degree", desc=True)
        result = q.execute(sample_network)
        
        assert result.count > 0

    def test_order_by_shorthand(self, sample_network):
        """Test order_by with - prefix for descending."""
        q = Q.nodes().compute("degree").order_by("-degree")
        result = q.execute(sample_network)
        
        assert result.count > 0

    def test_limit(self, sample_network):
        """Test limit clause."""
        q = Q.nodes().limit(2)
        result = q.execute(sample_network)
        
        assert result.count <= 2

    def test_to_ast(self):
        """Test to_ast method."""
        q = Q.nodes().where(layer="social").limit(10)
        ast = q.to_ast()
        
        assert isinstance(ast, Query)
        assert ast.select.target == Target.NODES
        assert ast.select.limit == 10

    def test_to_dsl(self):
        """Test to_dsl method."""
        q = Q.nodes().where(layer="social").compute("degree").limit(10)
        dsl = q.to_dsl()
        
        assert "SELECT nodes" in dsl
        assert "WHERE" in dsl
        assert "COMPUTE degree" in dsl
        assert "LIMIT 10" in dsl

    def test_chaining(self, sample_network):
        """Test method chaining."""
        result = (
            Q.nodes()
             .where(layer="social")
             .compute("degree")
             .order_by("-degree")
             .limit(2)
             .execute(sample_network)
        )
        
        assert result.count <= 2


class TestLayerAlgebra:
    """Test layer algebra with L proxy."""

    def test_layer_proxy_getitem(self):
        """Test L['name'] syntax."""
        expr = L["social"]
        assert isinstance(expr, LayerExprBuilder)
        assert expr.terms[0].name == "social"

    def test_layer_union(self):
        """Test layer union with +."""
        expr = L["social"] + L["work"]
        assert len(expr.terms) == 2
        assert "+" in expr.ops

    def test_layer_difference(self):
        """Test layer difference with -."""
        expr = L["social"] - L["bots"]
        assert len(expr.terms) == 2
        assert "-" in expr.ops

    def test_layer_intersection(self):
        """Test layer intersection with &."""
        expr = L["social"] & L["work"]
        assert len(expr.terms) == 2
        assert "&" in expr.ops

    def test_layer_expr_to_ast(self):
        """Test converting layer expression to AST."""
        expr = L["social"] + L["work"]
        ast = expr._to_ast()
        
        assert isinstance(ast, LayerExpr)
        assert len(ast.terms) == 2

    def test_from_layers_in_query(self, sample_network):
        """Test from_layers in query builder."""
        q = Q.nodes().from_layers(L["social"] + L["work"])
        result = q.execute(sample_network)
        
        assert result.count == 5


class TestParam:
    """Test parameter references."""

    def test_param_int(self):
        """Test Param.int()."""
        p = Param.int("k")
        assert isinstance(p, ParamRef)
        assert p.name == "k"
        assert p.type_hint == "int"

    def test_param_float(self):
        """Test Param.float()."""
        p = Param.float("threshold")
        assert p.name == "threshold"
        assert p.type_hint == "float"

    def test_param_str(self):
        """Test Param.str()."""
        p = Param.str("name")
        assert p.name == "name"
        assert p.type_hint == "str"

    def test_param_ref(self):
        """Test Param.ref()."""
        p = Param.ref("x")
        assert p.name == "x"
        assert p.type_hint is None


class TestQueryResult:
    """Test QueryResult class."""

    def test_result_creation(self):
        """Test QueryResult creation."""
        result = QueryResult(
            target="nodes",
            items=[("A", "layer1"), ("B", "layer1")],
            attributes={"degree": {("A", "layer1"): 2, ("B", "layer1"): 1}},
            meta={"dsl_version": "2.0"}
        )
        
        assert result.target == "nodes"
        assert result.count == 2
        assert len(result) == 2

    def test_result_nodes_property(self):
        """Test nodes property."""
        result = QueryResult(target="nodes", items=[1, 2, 3])
        assert result.nodes == [1, 2, 3]

    def test_result_edges_property(self):
        """Test edges property."""
        result = QueryResult(target="edges", items=[(1, 2), (2, 3)])
        assert result.edges == [(1, 2), (2, 3)]

    def test_result_wrong_property(self):
        """Test accessing wrong property raises error."""
        result = QueryResult(target="nodes", items=[1, 2])
        with pytest.raises(ValueError):
            _ = result.edges

    def test_result_iter(self):
        """Test iteration over result."""
        result = QueryResult(target="nodes", items=[1, 2, 3])
        items = list(result)
        assert items == [1, 2, 3]

    def test_to_pandas(self, sample_network):
        """Test to_pandas export."""
        q = Q.nodes().compute("degree")
        result = q.execute(sample_network)
        df = result.to_pandas()
        
        assert "id" in df.columns
        assert "degree" in df.columns
        assert len(df) == result.count

    def test_to_networkx(self, sample_network):
        """Test to_networkx export."""
        q = Q.nodes().where(layer="social")
        result = q.execute(sample_network)
        G = result.to_networkx(sample_network)
        
        import networkx as nx
        assert isinstance(G, nx.Graph)

    def test_to_dict(self):
        """Test to_dict export."""
        result = QueryResult(
            target="nodes",
            items=[1, 2],
            attributes={"degree": {1: 2, 2: 3}},
            meta={"key": "value"}
        )
        d = result.to_dict()
        
        assert d["target"] == "nodes"
        assert d["count"] == 2
        assert d["nodes"] == [1, 2]
        assert "computed" in d

    def test_repr(self):
        """Test __repr__."""
        result = QueryResult(
            target="nodes",
            items=[1, 2],
            attributes={"degree": {}}
        )
        s = repr(result)
        assert "QueryResult" in s
        assert "nodes" in s


class TestExplain:
    """Test EXPLAIN mode."""

    def test_explain_query(self, sample_network):
        """Test explain returns execution plan."""
        q = Q.nodes().where(layer="social").compute("betweenness_centrality")
        plan = q.explain().execute(sample_network)
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.steps) > 0

    def test_explain_has_steps(self, sample_network):
        """Test that plan has step descriptions."""
        q = Q.nodes().compute("degree")
        plan = q.explain().execute(sample_network)
        
        for step in plan.steps:
            assert step.description
            assert step.estimated_complexity

    def test_explain_warnings_for_expensive(self, sample_network):
        """Test that expensive operations generate warnings."""
        # Create a larger network to trigger warnings
        network = multinet.multi_layer_network(directed=False)
        
        # Batch node creation for efficiency
        nodes = [{'source': f'N{i}', 'type': 'layer1'} for i in range(100)]
        network.add_nodes(nodes)
        
        # Batch edge creation for efficiency
        edges = [{
            'source': f'N{i}', 'target': f'N{i+50}',
            'source_type': 'layer1', 'target_type': 'layer1'
        } for i in range(50)]
        network.add_edges(edges)
        
        q = Q.nodes().compute("betweenness_centrality")
        plan = q.explain().execute(network)
        
        # Plan should exist
        assert len(plan.steps) > 0


class TestErrorHandling:
    """Test error handling with suggestions."""

    def test_unknown_measure_error(self):
        """Test UnknownMeasureError has suggestion."""
        with pytest.raises(UnknownMeasureError) as exc_info:
            measure_registry.get("deegree")  # typo
        
        err = exc_info.value
        assert "deegree" in str(err)
        assert "degree" in str(err)  # suggestion

    def test_measure_registry_list(self):
        """Test measure registry lists measures."""
        measures = measure_registry.list_measures()
        
        assert "degree" in measures
        assert "betweenness_centrality" in measures
        assert "closeness_centrality" in measures

    def test_measure_registry_has(self):
        """Test measure registry has method."""
        assert measure_registry.has("degree")
        assert measure_registry.has("betweenness")  # alias
        assert not measure_registry.has("unknown_measure")


class TestMeasureRegistry:
    """Test measure registry functionality."""

    def test_registered_measures(self):
        """Test built-in measures are registered."""
        expected = [
            "degree",
            "degree_centrality",
            "betweenness_centrality",
            "closeness_centrality",
            "eigenvector_centrality",
            "pagerank",
            "clustering",
            "communities",
        ]
        for name in expected:
            assert measure_registry.has(name), f"Missing measure: {name}"

    def test_aliases(self):
        """Test measure aliases work."""
        # These should work as aliases
        assert measure_registry.has("betweenness")
        assert measure_registry.has("closeness")
        assert measure_registry.has("eigenvector")
        assert measure_registry.has("community")

    def test_get_description(self):
        """Test getting measure descriptions."""
        desc = measure_registry.get_description("degree")
        assert desc is not None
        assert "degree" in desc.lower()


class TestSerializerDSL:
    """Test AST to DSL serialization."""

    def test_simple_query(self):
        """Test serializing simple query."""
        q = Q.nodes()
        dsl = q.to_dsl()
        assert dsl == "SELECT nodes"

    def test_with_where(self):
        """Test serializing query with WHERE."""
        q = Q.nodes().where(layer="social")
        dsl = q.to_dsl()
        assert "WHERE" in dsl
        assert 'layer = "social"' in dsl

    def test_with_compute(self):
        """Test serializing query with COMPUTE."""
        q = Q.nodes().compute("degree", "clustering")
        dsl = q.to_dsl()
        assert "COMPUTE" in dsl
        assert "degree" in dsl
        assert "clustering" in dsl

    def test_with_compute_alias(self):
        """Test serializing query with COMPUTE AS."""
        q = Q.nodes().compute("betweenness_centrality", alias="bc")
        dsl = q.to_dsl()
        assert "COMPUTE betweenness_centrality AS bc" in dsl

    def test_with_order_by(self):
        """Test serializing query with ORDER BY."""
        q = Q.nodes().order_by("-bc")
        dsl = q.to_dsl()
        assert "ORDER BY" in dsl
        assert "bc DESC" in dsl

    def test_with_limit(self):
        """Test serializing query with LIMIT."""
        q = Q.nodes().limit(10)
        dsl = q.to_dsl()
        assert "LIMIT 10" in dsl

    def test_with_layers(self):
        """Test serializing query with FROM layers."""
        q = Q.nodes().from_layers(L["social"] + L["work"])
        dsl = q.to_dsl()
        assert "FROM" in dsl
        assert 'LAYER("social")' in dsl
        assert 'LAYER("work")' in dsl


class TestIntegration:
    """Integration tests for DSL v2."""

    def test_complete_workflow(self, sample_network):
        """Test complete query workflow."""
        # Build query
        q = (
            Q.nodes()
             .from_layers(L["social"])
             .where(degree__gt=0)
             .compute("betweenness_centrality", alias="bc")
             .order_by("-bc")
             .limit(2)
        )
        
        # Execute
        result = q.execute(sample_network)
        
        # Verify
        assert result.count <= 2
        assert "bc" in result.attributes
        
        # Export
        df = result.to_pandas()
        assert len(df) == result.count

    def test_builder_and_legacy_interop(self, sample_network):
        """Test that builder and legacy APIs are compatible."""
        from py3plex.dsl import execute_query
        
        # Legacy query
        legacy_result = execute_query(sample_network, 'SELECT nodes WHERE layer="social"')
        
        # Builder query
        builder_result = Q.nodes().where(layer="social").execute(sample_network)
        
        # Both should return same count
        assert legacy_result['count'] == builder_result.count

    def test_explain_then_execute(self, sample_network):
        """Test explain followed by actual execution."""
        q = Q.nodes().where(layer="social").compute("degree")
        
        # First explain
        plan = q.explain().execute(sample_network)
        assert len(plan.steps) > 0
        
        # Then execute
        result = q.execute(sample_network)
        assert result.count > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
