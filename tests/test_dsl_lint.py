"""Tests for DSL linting functionality."""

import pytest
from py3plex.core import multinet
from py3plex.dsl import (
    # AST
    Query,
    SelectStmt,
    Target,
    LayerExpr,
    LayerTerm,
    ConditionExpr,
    ConditionAtom,
    Comparison,
    ComputeItem,
    # Builder API
    Q,
    L,
    # Linting
    lint,
    explain,
    ExplainResult,
    Diagnostic,
    NetworkSchemaProvider,
    AttrType,
)


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes in multiple layers
    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Carol', 'type': 'social'},
        {'source': 'Dave', 'type': 'work'},
        {'source': 'Eve', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    # Add edges
    edges = [
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Dave', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},
    ]
    network.add_edges(edges)
    
    return network


class TestSchemaProvider:
    """Test schema provider functionality."""
    
    def test_network_schema_provider(self, sample_network):
        """Test NetworkSchemaProvider extracts schema correctly."""
        schema = NetworkSchemaProvider(sample_network)
        
        # Check layers
        layers = schema.list_layers()
        assert 'social' in layers
        assert 'work' in layers
        assert len(layers) == 2
        
        # Check counts
        node_count = schema.get_node_count()
        assert node_count == 5
        
        edge_count = schema.get_edge_count()
        assert edge_count == 4


class TestBasicLinting:
    """Test basic linting functionality."""
    
    def test_lint_valid_query(self, sample_network):
        """Test linting a valid query returns no errors."""
        query = Q.nodes().from_layers(L["social"]).where(degree__gt=1).to_ast()
        
        diagnostics = lint(query, graph=sample_network)
        
        # Should have no errors
        errors = [d for d in diagnostics if d.severity == "error"]
        assert len(errors) == 0
    
    def test_lint_without_graph(self):
        """Test linting without graph still runs syntactic checks."""
        query = Q.nodes().from_layers(L["social"]).to_ast()
        
        # Should not raise, but won't do schema checks
        diagnostics = lint(query, graph=None, schema=None)
        
        # No errors expected without schema
        assert isinstance(diagnostics, list)


class TestUnknownLayerRule:
    """Test DSL001 - Unknown Layer rule."""
    
    def test_unknown_layer_detected(self, sample_network):
        """Test that unknown layers are detected."""
        # Build query with unknown layer
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                layer_expr=LayerExpr(
                    terms=[LayerTerm(name="unknown_layer")],
                    ops=[]
                )
            )
        )
        
        diagnostics = lint(query, graph=sample_network)
        
        # Should have DSL001 error
        dsl001_errors = [d for d in diagnostics if d.code == "DSL001"]
        assert len(dsl001_errors) > 0
        
        error = dsl001_errors[0]
        assert error.severity == "error"
        assert "unknown_layer" in error.message.lower()
    
    def test_known_layer_passes(self, sample_network):
        """Test that known layers don't trigger errors."""
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                layer_expr=LayerExpr(
                    terms=[LayerTerm(name="social")],
                    ops=[]
                )
            )
        )
        
        diagnostics = lint(query, graph=sample_network)
        
        # Should have no DSL001 errors
        dsl001_errors = [d for d in diagnostics if d.code == "DSL001"]
        assert len(dsl001_errors) == 0


class TestUnknownAttributeRule:
    """Test DSL002 - Unknown Attribute rule."""
    
    def test_builtin_attributes_pass(self, sample_network):
        """Test that built-in attributes like 'degree' don't trigger errors."""
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                where=ConditionExpr(
                    atoms=[ConditionAtom(comparison=Comparison(left="degree", op=">", right=1))],
                    ops=[]
                )
            )
        )
        
        diagnostics = lint(query, graph=sample_network)
        
        # Should have no DSL002 errors for built-in attributes
        dsl002_errors = [d for d in diagnostics if d.code == "DSL002"]
        assert len(dsl002_errors) == 0


class TestTypeMismatchRule:
    """Test DSL101 - Type Mismatch rule."""
    
    def test_numeric_comparison_with_string(self, sample_network):
        """Test type mismatch when comparing numeric to string."""
        # Create query: degree > "hello" (type mismatch)
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                where=ConditionExpr(
                    atoms=[ConditionAtom(comparison=Comparison(left="degree", op=">", right="hello"))],
                    ops=[]
                )
            )
        )
        
        diagnostics = lint(query, graph=sample_network)
        
        # Should have DSL101 error
        dsl101_errors = [d for d in diagnostics if d.code == "DSL101"]
        assert len(dsl101_errors) > 0


class TestUnsatisfiablePredicateRule:
    """Test DSL201 - Unsatisfiable Predicate rule."""
    
    def test_contradictory_conditions(self, sample_network):
        """Test detection of contradictory conditions."""
        # Create query: degree > 5 AND degree < 1 (contradiction)
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                where=ConditionExpr(
                    atoms=[
                        ConditionAtom(comparison=Comparison(left="degree", op=">", right=5)),
                        ConditionAtom(comparison=Comparison(left="degree", op="<", right=1)),
                    ],
                    ops=["AND"]
                )
            )
        )
        
        diagnostics = lint(query, graph=sample_network)
        
        # Should have DSL201 warning
        dsl201_warnings = [d for d in diagnostics if d.code == "DSL201"]
        assert len(dsl201_warnings) > 0


class TestRedundantPredicateRule:
    """Test DSL202 - Redundant Predicate rule."""
    
    def test_redundant_conditions(self, sample_network):
        """Test detection of redundant conditions."""
        # Create query: degree > 5 AND degree > 3 (degree > 3 is redundant)
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                where=ConditionExpr(
                    atoms=[
                        ConditionAtom(comparison=Comparison(left="degree", op=">", right=5)),
                        ConditionAtom(comparison=Comparison(left="degree", op=">", right=3)),
                    ],
                    ops=["AND"]
                )
            )
        )
        
        diagnostics = lint(query, graph=sample_network)
        
        # Should have DSL202 info
        dsl202_info = [d for d in diagnostics if d.code == "DSL202"]
        assert len(dsl202_info) > 0


class TestPerformanceRules:
    """Test performance warning rules."""
    
    def test_full_scan_not_triggered_small_network(self, sample_network):
        """Test that full scan warning is not triggered for small networks."""
        query = Q.nodes().to_ast()
        
        diagnostics = lint(query, graph=sample_network)
        
        # Small network should not trigger PERF301
        perf301_warnings = [d for d in diagnostics if d.code == "PERF301"]
        assert len(perf301_warnings) == 0
    
    def test_cross_layer_join_edges(self, sample_network):
        """Test cross-layer join detection."""
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.EDGES,
                layer_expr=LayerExpr(
                    terms=[LayerTerm(name="social"), LayerTerm(name="work")],
                    ops=["+"]
                )
            )
        )
        
        diagnostics = lint(query, graph=sample_network)
        
        # Small network won't trigger, but we can check the rule exists
        # (would trigger on larger networks)
        perf302_hints = [d for d in diagnostics if d.code == "PERF302"]
        # May or may not trigger depending on threshold


class TestExplainFunction:
    """Test explain functionality."""
    
    def test_explain_basic(self, sample_network):
        """Test basic explain functionality."""
        query = Q.nodes().from_layers(L["social"]).where(degree__gt=1).compute("degree").to_ast()
        
        result = explain(query, graph=sample_network)
        
        # Check result structure
        assert isinstance(result, ExplainResult)
        assert isinstance(result.ast_summary, str)
        assert isinstance(result.type_info, dict)
        assert isinstance(result.cost_estimate, str)
        assert isinstance(result.diagnostics, list)
        assert isinstance(result.plan_steps, list)
        
        # Check AST summary contains expected info
        assert "nodes" in result.ast_summary.lower()
        
        # Check type info
        assert len(result.type_info) > 0
        
        # Check plan steps
        assert len(result.plan_steps) > 0
    
    def test_explain_with_diagnostics(self, sample_network):
        """Test that explain includes diagnostics."""
        # Create query with unknown layer
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                layer_expr=LayerExpr(
                    terms=[LayerTerm(name="unknown")],
                    ops=[]
                )
            )
        )
        
        result = explain(query, graph=sample_network)
        
        # Should have diagnostics
        assert len(result.diagnostics) > 0
        
        # Should have DSL001 error
        dsl001_errors = [d for d in result.diagnostics if d.code == "DSL001"]
        assert len(dsl001_errors) > 0


class TestDiagnosticFormatting:
    """Test diagnostic formatting."""
    
    def test_diagnostic_str(self):
        """Test Diagnostic __str__ method."""
        diag = Diagnostic(
            code="DSL001",
            severity="error",
            message="Test message",
            span=(0, 10)
        )
        
        s = str(diag)
        assert "ERROR" in s
        assert "DSL001" in s
        assert "Test message" in s


class TestBuilderAPILinting:
    """Test linting with builder API."""
    
    def test_lint_builder_query(self, sample_network):
        """Test linting a query built with the builder API."""
        query = (
            Q.nodes()
             .from_layers(L["social"])
             .where(degree__gt=1)
             .compute("betweenness_centrality", alias="bc")
             .order_by("bc", desc=True)
             .limit(10)
             .to_ast()
        )
        
        diagnostics = lint(query, graph=sample_network)
        
        # Should have no errors for valid query
        errors = [d for d in diagnostics if d.severity == "error"]
        assert len(errors) == 0
