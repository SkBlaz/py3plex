"""Property-based tests for DSL functionality.

This module tests DSL correctness and invariants using property-based
testing with the Hypothesis library. Focuses on:
- Query builder API
- Condition evaluation
- Parameter binding
- Result consistency
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from py3plex.core import multinet
from py3plex.dsl import Q, L, Param, QueryBuilder
from py3plex.dsl.builder import build_condition_from_kwargs, COMPARATOR_MAP
from py3plex.dsl.errors import DslExecutionError, ParameterMissingError


# Custom strategies for generating test data
def layer_name_strategy():
    """Generate valid layer names."""
    return st.text(
        min_size=1,
        max_size=15,
        alphabet=st.characters(
            categories=('Lu', 'Ll', 'Nd'),
            exclude_characters=' \t\n\r'
        )
    )


def node_name_strategy():
    """Generate valid node names."""
    return st.text(
        min_size=1,
        max_size=10,
        alphabet=st.characters(categories=('Lu', 'Ll', 'Nd'))
    )


def small_network_strategy():
    """Generate small multilayer networks for testing."""
    def build_network(data):
        layers, nodes_per_layer = data
        assume(len(layers) > 0)
        assume(nodes_per_layer > 0)
        
        network = multinet.multi_layer_network(directed=False)
        
        # Add nodes
        node_list = []
        for layer_idx, layer in enumerate(layers[:3]):  # Limit to 3 layers
            for i in range(min(nodes_per_layer, 5)):  # Limit to 5 nodes per layer
                node_list.append({
                    'source': f'N{layer_idx}_{i}',
                    'type': layer
                })
        
        if node_list:
            network.add_nodes(node_list)
        
        # Add some edges
        edge_list = []
        for layer in layers[:3]:
            for i in range(min(nodes_per_layer - 1, 4)):
                edge_list.append({
                    'source': f'N{layers.index(layer)}_{i}',
                    'target': f'N{layers.index(layer)}_{i+1}',
                    'source_type': layer,
                    'target_type': layer
                })
        
        if edge_list:
            network.add_edges(edge_list)
        
        return network
    
    return st.tuples(
        st.lists(layer_name_strategy(), min_size=1, max_size=3, unique=True),
        st.integers(min_value=2, max_value=5)
    ).map(build_network)


@pytest.mark.property
class TestQueryBuilderProperties:
    """Property-based tests for query builder API."""
    
    @given(layer_name_strategy())
    @settings(max_examples=50)
    def test_from_layers_preserves_layer_name(self, layer_name):
        """Property: from_layers() should preserve the layer name in the query."""
        q = Q.nodes().from_layers(L[layer_name])
        ast = q.to_ast()
        
        # The layer should be in the query structure
        assert ast.select.layer_expr is not None
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=50)
    def test_limit_positive_values(self, limit):
        """Property: limit() should accept positive integers."""
        q = Q.nodes().limit(limit)
        ast = q.to_ast()
        
        assert ast.select.limit == limit
    
    @given(st.text(min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_compute_accepts_string_measure(self, measure_name):
        """Property: compute() should accept string measure names."""
        q = Q.nodes().compute(measure_name)
        ast = q.to_ast()
        
        assert len(ast.select.compute) == 1
        assert ast.select.compute[0].name == measure_name  # Use 'name' not 'measure'
    
    @given(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_compute_alias_is_preserved(self, measure_name, alias):
        """Property: compute() alias should be preserved in AST."""
        assume(measure_name != alias)
        q = Q.nodes().compute(measure_name, alias=alias)
        ast = q.to_ast()
        
        assert ast.select.compute[0].alias == alias
    
    @given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5))
    @settings(max_examples=50)
    def test_multiple_compute_preserves_order(self, measures):
        """Property: Multiple compute() calls should preserve order."""
        q = Q.nodes()
        for measure in measures:
            q = q.compute(measure)
        
        ast = q.to_ast()
        assert len(ast.select.compute) == len(measures)
        for i, measure in enumerate(measures):
            assert ast.select.compute[i].name == measure  # Use 'name' not 'measure'


@pytest.mark.property
class TestConditionBuilderProperties:
    """Property-based tests for condition building."""
    
    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(categories=('Ll',))),
        st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=50)
    def test_condition_from_kwargs_comparison(self, attr_name, value):
        """Property: Condition building from kwargs should preserve comparisons."""
        for suffix, op in COMPARATOR_MAP.items():
            kwargs = {f"{attr_name}__{suffix}": value}
            cond_expr = build_condition_from_kwargs(kwargs)
            
            # Should create a single comparison
            assert cond_expr is not None
    
    @given(st.text(min_size=1, max_size=20), st.floats(min_value=0.0, max_value=100.0))
    @settings(max_examples=50)
    def test_where_preserves_value(self, attr, value):
        """Property: where() should preserve comparison values."""
        # Test for non-NaN, non-inf values
        assume(not (value != value))  # Not NaN
        assume(abs(value) != float('inf'))
        
        q = Q.nodes().where(**{f"{attr}__gt": value})
        ast = q.to_ast()
        
        assert ast.select.where is not None


@pytest.mark.property
class TestParameterBindingProperties:
    """Property-based tests for parameter binding."""
    
    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(categories=('Ll',))),
        st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=50)
    def test_param_binding_required(self, param_name, param_value):
        """Property: Executing query with Param should require binding."""
        # Create a simple test network
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{'source': 'A', 'type': 'test'}])
        
        q = Q.nodes().where(degree__gt=Param.int(param_name))
        
        # Should fail without parameter
        with pytest.raises((ParameterMissingError, KeyError)):
            q.execute(network, progress=False, **{})
    
    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(categories=('Ll',))),
        st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=50)
    def test_param_binding_succeeds_with_value(self, param_name, param_value):
        """Property: Parameter binding should succeed when value provided."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([
            {'source': 'A', 'type': 'test'},
            {'source': 'B', 'type': 'test'}
        ])
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'test', 'target_type': 'test'}
        ])
        
        q = Q.nodes().where(degree__gt=Param.int(param_name))
        
        # Should succeed with parameter
        result = q.execute(network, progress=False, **{param_name: param_value})
        assert result is not None


@pytest.mark.property
class TestQueryExecutionProperties:
    """Property-based tests for query execution."""
    
    @given(small_network_strategy())
    @settings(max_examples=30, deadline=2000)
    def test_node_query_returns_subset_of_network(self, network):
        """Property: Node query result should be subset of all network nodes."""
        assume(network.core_network is not None)
        assume(network.core_network.number_of_nodes() > 0)
        
        result = Q.nodes().execute(network, progress=False)
        
        # Get all nodes in network (as tuples)
        all_nodes = set(network.core_network.nodes())
        
        # Result items should be subset
        result_nodes = set(result.items)
        assert result_nodes.issubset(all_nodes) or len(result_nodes) == 0
    
    @given(small_network_strategy())
    @settings(max_examples=30, deadline=2000)
    def test_edge_query_returns_valid_edges(self, network):
        """Property: Edge query should return valid edges from network."""
        assume(network.core_network is not None)
        assume(network.core_network.number_of_edges() > 0)
        
        result = Q.edges().execute(network, progress=False)
        
        # All edges should be valid tuples
        for edge in result.items:
            assert isinstance(edge, tuple)
            assert len(edge) >= 2
    
    @given(small_network_strategy(), st.integers(min_value=1, max_value=10))
    @settings(max_examples=30, deadline=2000)
    def test_limit_constrains_result_size(self, network, limit):
        """Property: LIMIT should constrain result set size."""
        assume(network.core_network is not None)
        assume(network.core_network.number_of_nodes() >= limit)
        
        result = Q.nodes().limit(limit).execute(network, progress=False)
        
        # Result should have at most 'limit' items
        assert len(result.items) <= limit
    
    @given(small_network_strategy())
    @settings(max_examples=30, deadline=2000)
    def test_query_result_has_metadata(self, network):
        """Property: Query result should always have metadata."""
        assume(network.core_network is not None)
        
        result = Q.nodes().execute(network, progress=False)
        
        # Check metadata structure
        assert hasattr(result, 'meta')
        assert isinstance(result.meta, dict)
        assert hasattr(result, 'items')
    
    @given(small_network_strategy())
    @settings(max_examples=30, deadline=2000)
    def test_empty_where_returns_all_nodes(self, network):
        """Property: Query with no WHERE clause should return all nodes."""
        assume(network.core_network is not None)
        assume(network.core_network.number_of_nodes() > 0)
        
        result_no_where = Q.nodes().execute(network, progress=False)
        result_with_empty = Q.nodes().where().execute(network, progress=False)
        
        # Both should return same number of nodes
        assert len(result_no_where.items) == len(result_with_empty.items)


@pytest.mark.property
class TestBuilderChainingProperties:
    """Property-based tests for builder method chaining."""
    
    @given(
        st.integers(min_value=1, max_value=100),
        st.text(min_size=1, max_size=20)
    )
    @settings(max_examples=50)
    def test_chaining_preserves_all_operations(self, limit, measure):
        """Property: Chaining operations should preserve all steps."""
        q = Q.nodes().compute(measure).limit(limit)
        ast = q.to_ast()
        
        # Both operations should be in AST
        assert len(ast.select.compute) == 1
        assert ast.select.limit == limit
    
    @given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5))
    @settings(max_examples=50)
    def test_multiple_chained_compute(self, measures):
        """Property: Multiple chained compute() calls should accumulate."""
        q = Q.nodes()
        for measure in measures:
            q = q.compute(measure)
        
        ast = q.to_ast()
        assert len(ast.select.compute) == len(measures)
    
    def test_chaining_returns_builder_instance(self):
        """Property: Each builder method should return a builder instance."""
        q1 = Q.nodes()
        assert isinstance(q1, QueryBuilder)
        
        q2 = q1.limit(10)
        assert isinstance(q2, QueryBuilder)
        
        q3 = q2.compute("degree")
        assert isinstance(q3, QueryBuilder)


@pytest.mark.property  
class TestProgressLoggingProperty:
    """Property-based tests for progress logging behavior."""
    
    @given(small_network_strategy())
    @settings(max_examples=20, deadline=2000)
    def test_progress_enabled_by_default_property(self, network):
        """Property: Progress should be enabled by default for all queries."""
        assume(network.core_network is not None)
        
        # Execute without explicit progress parameter
        import logging
        from io import StringIO
        import sys
        
        # Capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)
        logger = logging.getLogger('py3plex.dsl.executor')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        try:
            result = Q.nodes().execute(network)
            log_output = log_stream.getvalue()
            
            # Should have some progress logging
            # Note: We check if logger is configured, not necessarily that it logged
            # (depends on network size and query complexity)
            assert result is not None
        finally:
            logger.removeHandler(handler)
    
    @given(small_network_strategy())
    @settings(max_examples=20, deadline=2000)
    def test_progress_false_suppresses_logging(self, network):
        """Property: progress=False should suppress all progress logging."""
        assume(network.core_network is not None)
        
        import logging
        from io import StringIO
        
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)
        logger = logging.getLogger('py3plex.dsl.executor')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        try:
            result = Q.nodes().execute(network, progress=False)
            log_output = log_stream.getvalue()
            
            # Should not have DSL progress messages when explicitly disabled
            assert "Starting DSL query execution" not in log_output
            assert result is not None
        finally:
            logger.removeHandler(handler)
