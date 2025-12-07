"""Tests for DSL operator registry and custom operators.

This module tests the pluggable operator system that allows users to
define custom DSL operators.
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import (
    dsl_operator,
    DSLExecutionContext,
    register_operator,
    get_operator,
    list_operators,
    unregister_operator,
    describe_operator,
    Q,
)


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
    ]
    network.add_nodes(nodes)
    
    # Add edges
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'C', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2'},
    ]
    network.add_edges(edges)
    
    return network


class TestOperatorRegistry:
    """Test operator registry functions."""
    
    def test_register_operator(self):
        """Test registering a basic operator."""
        def test_op(context):
            return 42
        
        register_operator("test_basic_op", test_op, overwrite=True)
        
        op = get_operator("test_basic_op")
        assert op is not None
        assert op.name == "test_basic_op"
        assert op.func == test_op
        
        # Clean up
        unregister_operator("test_basic_op")
    
    def test_register_operator_with_metadata(self):
        """Test registering an operator with description and category."""
        def test_op(context):
            return 42
        
        register_operator(
            "test_meta_op",
            test_op,
            description="Test operator",
            category="testing",
            overwrite=True
        )
        
        op = get_operator("test_meta_op")
        assert op is not None
        assert op.description == "Test operator"
        assert op.category == "testing"
        
        # Clean up
        unregister_operator("test_meta_op")
    
    def test_register_duplicate_operator_fails(self):
        """Test that registering duplicate operator fails without overwrite."""
        def test_op(context):
            return 42
        
        register_operator("test_dup_op", test_op, overwrite=True)
        
        with pytest.raises(ValueError, match="already registered"):
            register_operator("test_dup_op", test_op, overwrite=False)
        
        # Clean up
        unregister_operator("test_dup_op")
    
    def test_register_duplicate_operator_with_overwrite(self):
        """Test that overwrite=True allows replacing operators."""
        def test_op1(context):
            return 1
        
        def test_op2(context):
            return 2
        
        register_operator("test_overwrite_op", test_op1, overwrite=True)
        register_operator("test_overwrite_op", test_op2, overwrite=True)
        
        op = get_operator("test_overwrite_op")
        assert op.func == test_op2
        
        # Clean up
        unregister_operator("test_overwrite_op")
    
    def test_get_nonexistent_operator(self):
        """Test getting an operator that doesn't exist."""
        op = get_operator("nonexistent_operator_xyz")
        assert op is None
    
    def test_list_operators(self):
        """Test listing all operators."""
        def test_op1(context):
            return 1
        
        def test_op2(context):
            return 2
        
        register_operator("test_list_op1", test_op1, category="test", overwrite=True)
        register_operator("test_list_op2", test_op2, category="test", overwrite=True)
        
        all_ops = list_operators()
        assert "test_list_op1" in all_ops
        assert "test_list_op2" in all_ops
        
        # Test filtering by category
        test_ops = list_operators(category="test")
        assert "test_list_op1" in test_ops
        assert "test_list_op2" in test_ops
        
        # Clean up
        unregister_operator("test_list_op1")
        unregister_operator("test_list_op2")
    
    def test_unregister_operator(self):
        """Test unregistering an operator."""
        def test_op(context):
            return 42
        
        register_operator("test_unreg_op", test_op, overwrite=True)
        assert get_operator("test_unreg_op") is not None
        
        result = unregister_operator("test_unreg_op")
        assert result is True
        assert get_operator("test_unreg_op") is None
        
        # Unregistering again should return False
        result = unregister_operator("test_unreg_op")
        assert result is False
    
    def test_describe_operator(self):
        """Test describing an operator."""
        def test_op(context, alpha: float = 0.1, beta: int = 5):
            """Test operator with parameters."""
            return alpha * beta
        
        register_operator("test_describe_op", test_op, category="test", overwrite=True)
        
        info = describe_operator("test_describe_op")
        assert info is not None
        assert info["name"] == "test_describe_op"
        assert info["category"] == "test"
        assert "alpha" in info["parameters"]
        assert "beta" in info["parameters"]
        assert info["parameters"]["alpha"]["default"] == 0.1
        assert info["parameters"]["beta"]["default"] == 5
        
        # Clean up
        unregister_operator("test_describe_op")
    
    def test_describe_nonexistent_operator(self):
        """Test describing an operator that doesn't exist."""
        info = describe_operator("nonexistent_operator_xyz")
        assert info is None


class TestDSLOperatorDecorator:
    """Test the @dsl_operator decorator."""
    
    def test_decorator_with_name(self):
        """Test decorator with explicit name."""
        @dsl_operator("test_decorator_named", overwrite=True)
        def my_function(context):
            return 42
        
        op = get_operator("test_decorator_named")
        assert op is not None
        assert op.func == my_function
        
        # Function should be unchanged
        assert my_function.__name__ == "my_function"
        
        # Clean up
        unregister_operator("test_decorator_named")
    
    def test_decorator_without_name(self):
        """Test decorator using function name as default."""
        @dsl_operator(overwrite=True)
        def test_decorator_auto():
            return 42
        
        op = get_operator("test_decorator_auto")
        assert op is not None
        
        # Clean up
        unregister_operator("test_decorator_auto")
    
    def test_decorator_with_metadata(self):
        """Test decorator with description and category."""
        @dsl_operator(
            "test_decorator_meta",
            description="Test operator",
            category="testing",
            overwrite=True
        )
        def my_function(context):
            """Original docstring."""
            return 42
        
        op = get_operator("test_decorator_meta")
        assert op is not None
        assert op.description == "Test operator"
        assert op.category == "testing"
        
        # Clean up
        unregister_operator("test_decorator_meta")
    
    def test_decorator_uses_docstring_as_description(self):
        """Test that decorator uses function docstring if no description provided."""
        @dsl_operator("test_decorator_docstring", overwrite=True)
        def my_function(context):
            """This is the docstring."""
            return 42
        
        op = get_operator("test_decorator_docstring")
        assert op is not None
        assert "This is the docstring." in (op.description or "")
        
        # Clean up
        unregister_operator("test_decorator_docstring")


class TestDSLExecutionContext:
    """Test DSLExecutionContext class."""
    
    def test_context_creation(self, sample_network):
        """Test creating an execution context."""
        context = DSLExecutionContext(
            graph=sample_network,
            current_layers=["layer1"],
            current_nodes=[("A", "layer1"), ("B", "layer1")],
            params={"seed": 42}
        )
        
        assert context.graph == sample_network
        assert context.current_layers == ["layer1"]
        assert len(context.current_nodes) == 2
        assert context.params["seed"] == 42
    
    def test_context_with_defaults(self, sample_network):
        """Test context with default values."""
        context = DSLExecutionContext(graph=sample_network)
        
        assert context.graph == sample_network
        assert context.current_layers is None
        assert context.current_nodes is None
        assert context.params == {}


class TestOperatorExecution:
    """Test executing custom operators."""
    
    def test_simple_operator_execution(self, sample_network):
        """Test executing a simple operator."""
        @dsl_operator("test_exec_simple", overwrite=True)
        def simple_op(context):
            return 42
        
        context = DSLExecutionContext(graph=sample_network)
        op = get_operator("test_exec_simple")
        result = op.func(context)
        
        assert result == 42
        
        # Clean up
        unregister_operator("test_exec_simple")
    
    def test_operator_with_parameters(self, sample_network):
        """Test operator with parameters."""
        @dsl_operator("test_exec_params", overwrite=True)
        def param_op(context, alpha: float = 0.1, beta: int = 5):
            return alpha * beta
        
        context = DSLExecutionContext(graph=sample_network)
        op = get_operator("test_exec_params")
        result = op.func(context, alpha=2.0, beta=10)
        
        assert result == 20.0
        
        # Clean up
        unregister_operator("test_exec_params")
    
    def test_operator_accesses_context(self, sample_network):
        """Test operator that accesses context fields."""
        @dsl_operator("test_exec_context", overwrite=True)
        def context_op(context):
            if context.current_layers:
                return len(context.current_layers)
            return 0
        
        context = DSLExecutionContext(
            graph=sample_network,
            current_layers=["layer1", "layer2"]
        )
        
        op = get_operator("test_exec_context")
        result = op.func(context)
        
        assert result == 2
        
        # Clean up
        unregister_operator("test_exec_context")
    
    def test_operator_returns_dict(self, sample_network):
        """Test operator that returns a dict."""
        @dsl_operator("test_exec_dict", overwrite=True)
        def dict_op(context):
            nodes = context.current_nodes or []
            return {node: 1.0 for node in nodes}
        
        context = DSLExecutionContext(
            graph=sample_network,
            current_nodes=[("A", "layer1"), ("B", "layer1")]
        )
        
        op = get_operator("test_exec_dict")
        result = op.func(context)
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert result[("A", "layer1")] == 1.0
        
        # Clean up
        unregister_operator("test_exec_dict")


class TestBuiltInOperators:
    """Test built-in operators registered with the new system."""
    
    def test_node_count_operator(self, sample_network):
        """Test the built-in node_count operator."""
        op = get_operator("node_count")
        assert op is not None
        
        context = DSLExecutionContext(
            graph=sample_network,
            current_nodes=[("A", "layer1"), ("B", "layer1"), ("C", "layer1")]
        )
        
        result = op.func(context)
        assert result == 3
    
    def test_layer_stats_operator(self, sample_network):
        """Test the built-in layer_stats operator."""
        op = get_operator("layer_stats")
        assert op is not None
        
        context = DSLExecutionContext(
            graph=sample_network,
            current_layers=["layer1"],
            current_nodes=[("A", "layer1"), ("B", "layer1")]
        )
        
        result = op.func(context)
        assert isinstance(result, dict)
        assert result["num_layers"] == 1
        assert result["num_nodes"] == 2


class TestBackwardCompatibility:
    """Test that existing DSL functionality still works."""
    
    def test_measure_registry_still_works(self, sample_network):
        """Test that the old measure registry still functions."""
        from py3plex.dsl import measure_registry
        
        # Old measures should still be registered
        assert measure_registry.has("degree")
        assert measure_registry.has("betweenness_centrality")
        assert measure_registry.has("pagerank")
    
    def test_operator_and_measure_coexist(self, sample_network):
        """Test that operators and measures can coexist."""
        from py3plex.dsl import measure_registry
        
        # Register a custom operator
        @dsl_operator("test_coexist", overwrite=True)
        def custom_op(context):
            return 42
        
        # Both should be accessible
        assert get_operator("test_coexist") is not None
        assert measure_registry.has("degree")
        
        # Clean up
        unregister_operator("test_coexist")


def test_example_script_runs():
    """Test that the example script runs without errors."""
    import sys
    import os
    
    # Get the path to the example script
    example_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "examples",
        "dsl_custom_operators.py"
    )
    
    # Check if example exists
    if os.path.exists(example_path):
        # Import and run the example
        import importlib.util
        spec = importlib.util.spec_from_file_location("example", example_path)
        example = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(example)
            example.main()
        except Exception as e:
            pytest.fail(f"Example script failed: {e}")
