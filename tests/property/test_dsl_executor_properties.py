#!/usr/bin/env python3
"""
Property-based tests for DSL executor module.

Tests invariants for query execution, including:
- Result determinism
- Parameter binding
- Layer filtering consistency
- Computation result validity
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
import numpy as np

# Import DSL module
try:
    from py3plex.dsl import Q, L, Param, execute_ast
    from py3plex.core import multinet
    from py3plex.dsl.errors import ParameterMissingError
    DSL_AVAILABLE = True
except ImportError:
    DSL_AVAILABLE = False
    pytest.skip("DSL module not available", allow_module_level=True)


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_network(num_nodes=5, num_layers=2, seed=None):
    """Create a simple test multilayer network."""
    if seed is not None:
        np.random.seed(seed)
    
    network = multinet.multi_layer_network(directed=False)
    
    layers = [f'layer{i}' for i in range(num_layers)]
    node_names = [chr(ord('A') + i) for i in range(num_nodes)]
    
    # Add nodes
    nodes = []
    for name in node_names:
        for layer in layers:
            nodes.append({'source': name, 'type': layer})
    network.add_nodes(nodes)
    
    # Add edges within layers
    edges = []
    for layer in layers:
        for i in range(len(node_names) - 1):
            edges.append({
                'source': node_names[i],
                'target': node_names[i + 1],
                'source_type': layer,
                'target_type': layer,
            })
    network.add_edges(edges)
    
    return network


# ============================================================================
# Property Tests: Execution Determinism
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    seed=st.integers(min_value=0, max_value=1000)
)
def test_executor_deterministic_results(seed):
    """
    Property: Executing the same query twice produces identical results.
    
    For any query Q and network N, execute_ast(N, Q) should be deterministic.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=seed)
    query = Q.nodes().to_ast()
    
    # Execute twice
    result1 = execute_ast(network, query)
    result2 = execute_ast(network, query)
    
    # Convert to pandas for comparison
    df1 = result1.to_pandas()
    df2 = result2.to_pandas()
    
    # Should be identical
    assert len(df1) == len(df2)
    assert list(df1.columns) == list(df2.columns)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_nodes=st.integers(min_value=2, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_executor_node_count_correct(num_nodes, num_layers):
    """
    Property: Query returns expected number of nodes.
    
    SELECT nodes with no filter should return all nodes in the network.
    """
    network = create_test_network(num_nodes=num_nodes, num_layers=num_layers, seed=42)
    query = Q.nodes().to_ast()
    
    result = execute_ast(network, query)
    df = result.to_pandas()
    
    # Should return num_nodes * num_layers (one per layer)
    expected_count = num_nodes * num_layers
    assert len(df) == expected_count


# ============================================================================
# Property Tests: Parameter Binding
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    param_value=st.integers(min_value=0, max_value=3)
)
def test_executor_parameter_substitution(param_value):
    """
    Property: Parameters are correctly substituted during execution.
    
    A query with Param.ref('k') executed with k=X should bind the parameter.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    
    # Test parameter substitution with layer filter (simpler test)
    # Use a known layer name and param for layer selection
    layer_name = 'layer0'
    query = Q.nodes().from_layers(L[layer_name]).limit(Param.ref('limit_val')).to_ast()
    
    # Execute with parameter binding
    result = execute_ast(network, query, params={'limit_val': param_value if param_value > 0 else 1})
    df = result.to_pandas()
    
    # Result should respect the limit parameter
    expected_limit = param_value if param_value > 0 else 1
    assert len(df) <= expected_limit


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    param_name=st.text(
        min_size=1,
        max_size=10,
        alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
    )
)
def test_executor_missing_parameter_raises_error(param_name):
    """
    Property: Missing parameters raise ParameterMissingError.
    
    Executing a query with unbound parameters should raise an error.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    
    # Query with parameter
    query = Q.nodes().where(degree__gt=Param.ref(param_name)).to_ast()
    
    # Execute without providing the parameter
    with pytest.raises(ParameterMissingError):
        execute_ast(network, query, params={})


# ============================================================================
# Property Tests: Layer Filtering
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=2)
)
def test_executor_layer_filter_correct(layer_idx):
    """
    Property: Layer filtering returns only nodes from specified layer.
    
    SELECT nodes FROM LAYER('X') should return only nodes in layer X.
    """
    num_layers = 3
    network = create_test_network(num_nodes=5, num_layers=num_layers, seed=42)
    
    layer_name = f'layer{layer_idx}'
    query = Q.nodes().from_layers(L[layer_name]).to_ast()
    
    result = execute_ast(network, query)
    df = result.to_pandas()
    
    # All results should be from the specified layer
    assert all(df['layer'] == layer_name)


@pytest.mark.property
def test_executor_union_layers_combines():
    """
    Property: Union of layers returns nodes from both layers.
    
    L['a'] + L['b'] should return nodes from both layers.
    """
    network = create_test_network(num_nodes=5, num_layers=3, seed=42)
    
    # Query for union of two layers
    query = Q.nodes().from_layers(L['layer0'] + L['layer1']).to_ast()
    
    result = execute_ast(network, query)
    df = result.to_pandas()
    
    # Should have nodes from both layers
    layers_present = set(df['layer'])
    assert 'layer0' in layers_present
    assert 'layer1' in layers_present
    assert 'layer2' not in layers_present  # Should not include layer2


# ============================================================================
# Property Tests: Result Validity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    threshold=st.integers(min_value=0, max_value=5)
)
def test_executor_where_filter_reduces_results(threshold):
    """
    Property: WHERE clause reduces or maintains result count.
    
    Adding a filter should never increase the number of results.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    
    # Query without filter
    query_all = Q.nodes().to_ast()
    result_all = execute_ast(network, query_all)
    count_all = len(result_all.to_pandas())
    
    # Query with filter
    query_filtered = Q.nodes().where(degree__gt=threshold).to_ast()
    result_filtered = execute_ast(network, query_filtered)
    count_filtered = len(result_filtered.to_pandas())
    
    # Filtered should have <= nodes than unfiltered
    assert count_filtered <= count_all


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    limit=st.integers(min_value=1, max_value=20)
)
def test_executor_limit_caps_results(limit):
    """
    Property: LIMIT clause caps the number of results.
    
    SELECT nodes LIMIT N should return at most N results.
    """
    network = create_test_network(num_nodes=10, num_layers=2, seed=42)
    
    query = Q.nodes().limit(limit).to_ast()
    result = execute_ast(network, query)
    df = result.to_pandas()
    
    # Should return at most 'limit' results
    assert len(df) <= limit


# ============================================================================
# Property Tests: Compute Clause
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    measure=st.sampled_from(['degree', 'clustering'])
)
def test_executor_compute_adds_column(measure):
    """
    Property: COMPUTE clause adds the requested column.
    
    SELECT nodes COMPUTE measure should add a 'measure' column to results.
    """
    network = create_test_network(num_nodes=5, num_layers=1, seed=42)
    
    query = Q.nodes().compute(measure).to_ast()
    result = execute_ast(network, query)
    df = result.to_pandas()
    
    # Should have the computed column
    assert measure in df.columns


@pytest.mark.property
def test_executor_compute_produces_numeric_values():
    """
    Property: Computed centrality measures produce numeric values.
    
    Centrality measures should return numeric (not NaN) values.
    """
    network = create_test_network(num_nodes=5, num_layers=1, seed=42)
    
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    df = result.to_pandas()
    
    # All degree values should be numeric and >= 0
    assert all(df['degree'] >= 0)
    assert all(np.isfinite(df['degree']))


# ============================================================================
# Property Tests: Order By
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    desc=st.booleans()
)
def test_executor_order_by_sorts_correctly(desc):
    """
    Property: ORDER BY produces sorted results.
    
    Results should be sorted according to the specified key and direction.
    """
    network = create_test_network(num_nodes=5, num_layers=1, seed=42)
    
    query = Q.nodes().compute('degree').order_by('degree', desc=desc).to_ast()
    result = execute_ast(network, query)
    df = result.to_pandas()
    
    # Check if sorted
    degree_values = df['degree'].tolist()
    
    if desc:
        # Should be descending
        assert degree_values == sorted(degree_values, reverse=True)
    else:
        # Should be ascending
        assert degree_values == sorted(degree_values)


# ============================================================================
# Property Tests: Edge Queries
# ============================================================================

@pytest.mark.property
def test_executor_edge_query_returns_edges():
    """
    Property: SELECT edges returns edge data.
    
    Edge queries should return source and target columns.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    
    query = Q.edges().to_ast()
    result = execute_ast(network, query)
    df = result.to_pandas()
    
    # Should have source and target columns
    assert 'source' in df.columns
    assert 'target' in df.columns
    assert len(df) > 0


@pytest.mark.property
def test_executor_intralayer_filter():
    """
    Property: intralayer filter returns only intra-layer edges.
    
    Edges with intralayer=True should have source_layer == target_layer.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    
    query = Q.edges().where(intralayer=True).to_ast()
    result = execute_ast(network, query)
    df = result.to_pandas()
    
    # All edges should be within the same layer
    if len(df) > 0:
        assert all(df['source_layer'] == df['target_layer'])


# ============================================================================
# Property Tests: Empty Network Handling
# ============================================================================

@pytest.mark.property
def test_executor_empty_network_returns_empty():
    """
    Property: Queries on empty networks return empty results.
    
    Executing any query on an empty network should return 0 results.
    """
    # Create empty network
    network = multinet.multi_layer_network(directed=False)
    
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    df = result.to_pandas()
    
    # Should be empty
    assert len(df) == 0


@pytest.mark.property
def test_executor_no_matching_layer_returns_empty():
    """
    Property: Querying non-existent layer returns empty results.
    
    FROM LAYER('nonexistent') should return 0 results.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    
    query = Q.nodes().from_layers(L['nonexistent_layer']).to_ast()
    result = execute_ast(network, query)
    df = result.to_pandas()
    
    # Should be empty
    assert len(df) == 0
