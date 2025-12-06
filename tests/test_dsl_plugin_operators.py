"""Tests for DSL plugin operator system.

Tests cover:
- Operator registration via @dsl_operator decorator
- Operator execution with DSLExecutionContext
- Integration with existing measure_registry
- Error handling for unknown operators
- Introspection utilities (list_operators, describe_operator)
- Backward compatibility with existing DSL features
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import (
    # Operator registry
    dsl_operator,
    register_operator,
    get_operator,
    list_operators,
    describe_operator,
    operator_registry,
    DSLOperator,
    DSLExecutionContext,
    # AST and execution
    Query,
    SelectStmt,
    Target,
    ComputeItem,
    execute_ast,
    # Builder API
    Q,
    # Errors
    UnknownMeasureError,
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


@pytest.fixture(autouse=True)
def cleanup_registry():
    """Clean up test operators after each test."""
    # Get operators before test
    before = set(operator_registry.list_operators().keys())
    
    yield
    
    # Clean up operators added during test
    after = set(operator_registry.list_operators().keys())
    added = after - before
    for op_name in added:
        success = operator_registry.unregister(op_name)
        if not success:
            # Log warning if cleanup failed (shouldn't happen in tests)
            import warnings
            warnings.warn(f"Failed to unregister test operator: {op_name}")


class TestOperatorRegistry:
    """Test operator registry functionality."""
    
    def test_register_operator_directly(self):
        """Test direct registration of an operator."""
        def my_operator(context: DSLExecutionContext) -> dict:
            return {node: 1.0 for node in context.current_nodes}
        
        register_operator("test_op", my_operator, description="Test operator")
        
        op = get_operator("test_op")
        assert op is not None
        assert op.name == "test_op"
        assert op.func == my_operator
        assert op.description == "Test operator"
    
    def test_register_operator_decorator(self):
        """Test registration via @dsl_operator decorator."""
        @dsl_operator("decorated_op", description="Decorated test")
        def my_operator(context: DSLExecutionContext) -> dict:
            return {node: 2.0 for node in context.current_nodes}
        
        op = get_operator("decorated_op")
        assert op is not None
        assert op.name == "decorated_op"
        assert op.description == "Decorated test"
    
    def test_decorator_default_name(self):
        """Test decorator with default name (function name)."""
        @dsl_operator()
        def my_custom_measure(context: DSLExecutionContext) -> dict:
            return {node: 3.0 for node in context.current_nodes}
        
        op = get_operator("my_custom_measure")
        assert op is not None
        assert op.name == "my_custom_measure"
    
    def test_decorator_category(self):
        """Test operator with category."""
        @dsl_operator("categorized_op", category="dynamics")
        def my_operator(context: DSLExecutionContext) -> dict:
            return {}
        
        op = get_operator("categorized_op")
        assert op.category == "dynamics"
    
    def test_case_insensitive_lookup(self):
        """Test that operator names are case-insensitive."""
        @dsl_operator("MixedCase")
        def my_operator(context: DSLExecutionContext) -> dict:
            return {}
        
        # All these should work
        assert get_operator("mixedcase") is not None
        assert get_operator("MixedCase") is not None
        assert get_operator("MIXEDCASE") is not None
    
    def test_duplicate_registration_error(self):
        """Test that duplicate registration raises error."""
        @dsl_operator("duplicate_op")
        def op1(context: DSLExecutionContext) -> dict:
            return {}
        
        with pytest.raises(ValueError, match="already registered"):
            @dsl_operator("duplicate_op")
            def op2(context: DSLExecutionContext) -> dict:
                return {}
    
    def test_overwrite_operator(self):
        """Test overwriting an existing operator."""
        @dsl_operator("overwrite_test")
        def op1(context: DSLExecutionContext) -> dict:
            return {"result": 1}
        
        @dsl_operator("overwrite_test", overwrite=True)
        def op2(context: DSLExecutionContext) -> dict:
            return {"result": 2}
        
        op = get_operator("overwrite_test")
        assert op.func == op2
    
    def test_unregister_operator(self):
        """Test unregistering an operator."""
        @dsl_operator("temp_op")
        def my_operator(context: DSLExecutionContext) -> dict:
            return {}
        
        assert get_operator("temp_op") is not None
        
        success = operator_registry.unregister("temp_op")
        assert success is True
        assert get_operator("temp_op") is None
    
    def test_list_all_operators(self):
        """Test listing all operators."""
        @dsl_operator("list_test_1")
        def op1(context: DSLExecutionContext) -> dict:
            return {}
        
        @dsl_operator("list_test_2", category="test")
        def op2(context: DSLExecutionContext) -> dict:
            return {}
        
        ops = list_operators()
        assert "list_test_1" in ops
        assert "list_test_2" in ops
    
    def test_list_operators_by_category(self):
        """Test filtering operators by category."""
        @dsl_operator("cat_op_1", category="dynamics")
        def op1(context: DSLExecutionContext) -> dict:
            return {}
        
        @dsl_operator("cat_op_2", category="centrality")
        def op2(context: DSLExecutionContext) -> dict:
            return {}
        
        dynamics_ops = list_operators(category="dynamics")
        assert "cat_op_1" in dynamics_ops
        assert "cat_op_2" not in dynamics_ops


class TestOperatorExecution:
    """Test operator execution through DSL."""
    
    def test_simple_operator_execution(self, sample_network):
        """Test executing a simple custom operator."""
        @dsl_operator("constant_score")
        def constant_score(context: DSLExecutionContext, value: float = 5.0) -> dict:
            """Return constant score for all nodes."""
            return {node: value for node in context.current_nodes}
        
        # Build query using AST
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                compute=[ComputeItem(name="constant_score", alias="score")]
            )
        )
        
        result = execute_ast(sample_network, query)
        
        # Check that all nodes have the score
        assert "score" in result.attributes
        for node in result.items:
            assert result.attributes["score"][node] == 5.0
    
    def test_operator_with_context_access(self, sample_network):
        """Test operator that uses execution context."""
        @dsl_operator("node_counter")
        def node_counter(context: DSLExecutionContext) -> dict:
            """Count nodes and return as score."""
            count = len(context.current_nodes or [])
            return {node: count for node in context.current_nodes}
        
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                compute=[ComputeItem(name="node_counter", alias="count")]
            )
        )
        
        result = execute_ast(sample_network, query)
        
        # All nodes should have count equal to total nodes
        node_count = len(result.items)
        for node in result.items:
            assert result.attributes["count"][node] == node_count
    
    def test_operator_builder_api(self, sample_network):
        """Test operator execution via builder API."""
        @dsl_operator("builder_test")
        def builder_test(context: DSLExecutionContext) -> dict:
            return {node: 42.0 for node in context.current_nodes}
        
        # Use builder API
        query = Q.nodes().compute("builder_test", alias="test_score")
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        assert "test_score" in df.columns
        assert all(df["test_score"] == 42.0)
    
    def test_backward_compatibility_with_measures(self, sample_network):
        """Test that existing measures still work alongside operators."""
        @dsl_operator("custom_measure")
        def custom_measure(context: DSLExecutionContext) -> dict:
            return {node: 10.0 for node in context.current_nodes}
        
        # Query with both custom operator and built-in measure
        query = (
            Q.nodes()
            .compute("degree", alias="deg")
            .compute("custom_measure", alias="custom")
        )
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        assert "deg" in df.columns
        assert "custom" in df.columns
        assert all(df["custom"] == 10.0)
    
    def test_unknown_operator_error(self, sample_network):
        """Test error message for unknown operator."""
        query = Query(
            explain=False,
            select=SelectStmt(
                target=Target.NODES,
                compute=[ComputeItem(name="nonexistent_operator", alias="x")]
            )
        )
        
        with pytest.raises(UnknownMeasureError) as exc_info:
            execute_ast(sample_network, query)
        
        # Error should mention the unknown operator
        assert "nonexistent_operator" in str(exc_info.value)


class TestIntrospection:
    """Test introspection utilities."""
    
    def test_describe_operator(self):
        """Test describing an operator."""
        @dsl_operator("introspect_test", description="A test operator", category="test")
        def my_operator(context: DSLExecutionContext) -> dict:
            """This is a docstring."""
            return {}
        
        info = describe_operator("introspect_test")
        
        assert info is not None
        assert info["name"] == "introspect_test"
        assert info["description"] == "A test operator"
        assert info["category"] == "test"
        assert "my_operator" in info["function"]
    
    def test_describe_nonexistent_operator(self):
        """Test describing a nonexistent operator returns None."""
        info = describe_operator("does_not_exist")
        assert info is None
    
    def test_list_operators_returns_dict(self):
        """Test that list_operators returns a dict of DSLOperator objects."""
        @dsl_operator("list_dict_test")
        def my_operator(context: DSLExecutionContext) -> dict:
            return {}
        
        ops = list_operators()
        
        assert isinstance(ops, dict)
        assert "list_dict_test" in ops
        assert isinstance(ops["list_dict_test"], DSLOperator)


class TestContextFields:
    """Test DSLExecutionContext fields."""
    
    def test_context_has_graph(self, sample_network):
        """Test that context provides access to the graph."""
        captured_context = {}
        
        @dsl_operator("context_test")
        def capture_context(context: DSLExecutionContext) -> dict:
            captured_context["graph"] = context.graph
            captured_context["layers"] = context.current_layers
            captured_context["nodes"] = context.current_nodes
            captured_context["target"] = context.target
            return {}
        
        query = Q.nodes().compute("context_test", alias="x")
        query.execute(sample_network)
        
        assert captured_context["graph"] is sample_network
        assert captured_context["target"] == "nodes"
        assert captured_context["nodes"] is not None


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_operator_returns_non_dict(self, sample_network):
        """Test operator that returns a non-dict value."""
        @dsl_operator("scalar_result")
        def scalar_result(context: DSLExecutionContext) -> float:
            return 99.0
        
        query = Q.nodes().compute("scalar_result", alias="score")
        result = query.execute(sample_network)
        
        # Should apply scalar to all nodes
        df = result.to_pandas()
        assert all(df["score"] == 99.0)
    
    def test_empty_network(self):
        """Test operator on empty network."""
        empty_net = multinet.multi_layer_network(directed=False)
        
        @dsl_operator("empty_test")
        def empty_test(context: DSLExecutionContext) -> dict:
            return {}
        
        query = Q.nodes().compute("empty_test", alias="x")
        result = query.execute(empty_net)
        
        assert len(result.items) == 0
    
    def test_operator_with_exception(self, sample_network):
        """Test that operator exceptions are handled gracefully."""
        @dsl_operator("failing_op")
        def failing_op(context: DSLExecutionContext) -> dict:
            raise RuntimeError("Intentional failure")
        
        query = Q.nodes().compute("failing_op", alias="x")
        
        # Should not crash the entire query, but log warning
        result = query.execute(sample_network)
        
        # Result should exist but attributes may be empty
        assert "x" in result.attributes
