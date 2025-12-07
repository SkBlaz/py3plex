"""Tests for DSL operator plugin system.

This module tests the extensible operator registry that allows users to
define custom DSL operators via the @dsl_operator decorator.
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import (
    dsl_operator,
    DSLExecutionContext,
    list_operators,
    get_operator,
    describe_operator,
    unregister_operator,
    Q,
    L,
)


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'Alice', 'type': 'work'},
        {'source': 'Bob', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    ]
    network.add_edges(edges)
    
    return network


class TestOperatorRegistry:
    """Test operator registration and lookup."""
    
    def test_register_operator_with_decorator(self):
        """Test registering an operator with @dsl_operator decorator."""
        @dsl_operator("test_operator_1")
        def test_op(context: DSLExecutionContext):
            return 42
        
        # Check it's registered
        assert get_operator("test_operator_1") is not None
        
        # Cleanup
        unregister_operator("test_operator_1")
    
    def test_register_operator_with_default_name(self):
        """Test registering an operator without explicit name (uses function name)."""
        @dsl_operator()
        def my_custom_op(context: DSLExecutionContext):
            return 99
        
        # Should be registered with function name
        assert get_operator("my_custom_op") is not None
        
        # Cleanup
        unregister_operator("my_custom_op")
    
    def test_register_operator_with_metadata(self):
        """Test registering an operator with description and category."""
        @dsl_operator(
            "test_operator_2",
            description="A test operator",
            category="testing"
        )
        def test_op(context: DSLExecutionContext):
            return "test"
        
        op = get_operator("test_operator_2")
        assert op is not None
        assert op.description == "A test operator"
        assert op.category == "testing"
        
        # Cleanup
        unregister_operator("test_operator_2")
    
    def test_register_duplicate_operator_fails(self):
        """Test that registering duplicate operator raises error."""
        @dsl_operator("duplicate_op")
        def first_op(context: DSLExecutionContext):
            return 1
        
        # Trying to register again should fail
        with pytest.raises(ValueError, match="already registered"):
            @dsl_operator("duplicate_op")
            def second_op(context: DSLExecutionContext):
                return 2
        
        # Cleanup
        unregister_operator("duplicate_op")
    
    def test_register_duplicate_operator_with_overwrite(self):
        """Test that registering duplicate with overwrite=True succeeds."""
        @dsl_operator("overwrite_op")
        def first_op(context: DSLExecutionContext):
            return 1
        
        # Should succeed with overwrite=True
        @dsl_operator("overwrite_op", overwrite=True)
        def second_op(context: DSLExecutionContext):
            return 2
        
        op = get_operator("overwrite_op")
        assert op.func is second_op
        
        # Cleanup
        unregister_operator("overwrite_op")
    
    def test_list_operators(self):
        """Test listing all registered operators."""
        @dsl_operator("list_test_1")
        def op1(context: DSLExecutionContext):
            return 1
        
        @dsl_operator("list_test_2")
        def op2(context: DSLExecutionContext):
            return 2
        
        operators = list_operators()
        assert "list_test_1" in operators
        assert "list_test_2" in operators
        
        # Cleanup
        unregister_operator("list_test_1")
        unregister_operator("list_test_2")
    
    def test_describe_operator(self):
        """Test getting operator description."""
        @dsl_operator("describe_test", description="Test description", category="test")
        def test_op(context: DSLExecutionContext):
            """Docstring description."""
            return 1
        
        info = describe_operator("describe_test")
        assert info is not None
        assert info["name"] == "describe_test"
        assert info["description"] == "Test description"
        assert info["category"] == "test"
        
        # Cleanup
        unregister_operator("describe_test")
    
    def test_describe_nonexistent_operator(self):
        """Test describing a non-existent operator returns None."""
        info = describe_operator("nonexistent_operator_xyz")
        assert info is None


class TestOperatorExecution:
    """Test execution of custom operators in queries."""
    
    def test_custom_operator_receives_context(self, sample_network):
        """Test that custom operator receives execution context."""
        context_received = {}
        
        @dsl_operator("context_test")
        def context_test_op(context: DSLExecutionContext):
            context_received['graph'] = context.graph
            context_received['layers'] = context.current_layers
            context_received['nodes'] = context.current_nodes
            return {node: 1.0 for node in context.current_nodes or []}
        
        # Execute query using the custom operator
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("context_test", alias="test_score")
            .execute(sample_network)
        )
        
        # Verify context was received
        assert context_received['graph'] is sample_network
        assert context_received['layers'] == ['social']
        assert len(context_received['nodes']) > 0
        
        # Cleanup
        unregister_operator("context_test")
    
    def test_custom_operator_returns_scalar(self, sample_network):
        """Test that scalar return values are handled correctly."""
        @dsl_operator("scalar_op")
        def scalar_op(context: DSLExecutionContext):
            return 42.0
        
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("scalar_op", alias="score")
            .execute(sample_network)
        )
        
        # All nodes should have the scalar value
        df = result.to_pandas()
        assert 'score' in df.columns
        assert all(df['score'] == 42.0)
        
        # Cleanup
        unregister_operator("scalar_op")
    
    def test_custom_operator_returns_dict(self, sample_network):
        """Test that dict return values are handled correctly."""
        @dsl_operator("dict_op")
        def dict_op(context: DSLExecutionContext):
            # Return different values for different nodes
            return {node: i * 10 for i, node in enumerate(context.current_nodes or [])}
        
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("dict_op", alias="value")
            .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert 'value' in df.columns
        # Values should vary
        assert df['value'].nunique() > 1
        
        # Cleanup
        unregister_operator("dict_op")
    
    def test_builtin_measures_still_work(self, sample_network):
        """Test that built-in measures still work with new system."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree", alias="deg")
            .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert 'deg' in df.columns
        assert len(df) > 0


class TestBackwardCompatibility:
    """Test that existing functionality is not broken."""
    
    def test_measure_registry_unchanged(self, sample_network):
        """Test that measure registry still works as before."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree", alias="deg")
            .compute("betweenness_centrality", alias="bc")
            .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert 'deg' in df.columns
        assert 'bc' in df.columns


class TestBuiltinOperators:
    """Test built-in operators registered via operator registry."""
    
    def test_multiplex_degree_operator(self, sample_network):
        """Test the multiplex_degree operator."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("multiplex_degree", alias="mdeg")
            .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert 'mdeg' in df.columns
        assert len(df) > 0
    
    def test_layer_count_operator(self, sample_network):
        """Test the layer_count operator."""
        result = (
            Q.nodes()
            .compute("layer_count", alias="layers")
            .execute(sample_network)
        )
        
        df = result.to_pandas()
        assert 'layers' in df.columns
        # Alice and Bob should appear in multiple layers
        alice_count = df[df['id'].apply(lambda x: x[0] if isinstance(x, tuple) else x) == 'Alice']['layers'].iloc[0]
        assert alice_count >= 2


class TestOperatorNameNormalization:
    """Test that operator names are normalized consistently."""
    
    def test_name_case_insensitive(self):
        """Test that operator names are case-insensitive."""
        @dsl_operator("TestOperator")
        def test_op(context: DSLExecutionContext):
            return 1
        
        # Should find it with different casing
        assert get_operator("testoperator") is not None
        assert get_operator("TESTOPERATOR") is not None
        assert get_operator("TestOperator") is not None
        
        # Cleanup
        unregister_operator("testoperator")
    
    def test_name_whitespace_stripped(self):
        """Test that whitespace is stripped from names."""
        @dsl_operator("  spaced_op  ")
        def test_op(context: DSLExecutionContext):
            return 1
        
        # Should find it without spaces
        assert get_operator("spaced_op") is not None
        
        # Cleanup
        unregister_operator("spaced_op")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
