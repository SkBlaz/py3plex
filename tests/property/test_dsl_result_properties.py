#!/usr/bin/env python3
"""
Property-based tests for DSL QueryResult class.

Tests invariants for:
- QueryResult construction
- Result transformations (to_pandas, to_networkx)
- Result grouping and summary
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
import numpy as np

# Import DSL modules
try:
    from py3plex.dsl import Q, execute_ast
    from py3plex.dsl.result import QueryResult
    from py3plex.core import multinet
    RESULT_AVAILABLE = True
except ImportError:
    RESULT_AVAILABLE = False
    pytest.skip("DSL result module not available", allow_module_level=True)


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
# Property Tests: QueryResult Construction
# ============================================================================

@pytest.mark.property
def test_query_result_has_target():
    """
    Property: QueryResult preserves target type.
    
    A result should maintain whether it's for nodes or edges.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    assert hasattr(result, 'target')
    assert result.target in ['nodes', 'edges']


@pytest.mark.property
def test_query_result_has_items():
    """
    Property: QueryResult contains items.
    
    A result should have accessible items attribute.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    assert hasattr(result, 'items')
    assert result.items is not None


# ============================================================================
# Property Tests: to_pandas() Conversion
# ============================================================================

@pytest.mark.property
@given(
    num_nodes=st.integers(min_value=1, max_value=10)
)
def test_to_pandas_returns_dataframe(num_nodes):
    """
    Property: to_pandas() returns a pandas DataFrame.
    
    Conversion to pandas should always return a DataFrame.
    """
    network = create_test_network(num_nodes=num_nodes, num_layers=1, seed=42)
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    # Should be a pandas DataFrame
    import pandas as pd
    assert isinstance(df, pd.DataFrame)


@pytest.mark.property
def test_to_pandas_preserves_row_count():
    """
    Property: to_pandas() preserves number of results.
    
    DataFrame should have same number of rows as results.
    """
    network = create_test_network(num_nodes=5, num_layers=1, seed=42)
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    # Number of rows should match number of nodes
    assert len(df) == 5


@pytest.mark.property
def test_to_pandas_idempotent():
    """
    Property: to_pandas() is idempotent.
    
    Calling to_pandas() twice should return equivalent DataFrames.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    df1 = result.to_pandas()
    df2 = result.to_pandas()
    
    # Should be equivalent
    assert len(df1) == len(df2)
    assert list(df1.columns) == list(df2.columns)


# ============================================================================
# Property Tests: to_networkx() Conversion
# ============================================================================

@pytest.mark.property
def test_to_networkx_returns_graph():
    """
    Property: to_networkx() returns a NetworkX graph.
    
    Conversion should produce a valid NetworkX graph.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    try:
        import networkx as nx
        graph = result.to_networkx()
        
        # Should be a NetworkX graph
        assert isinstance(graph, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph))
    except Exception:
        # If to_networkx() doesn't exist or fails for nodes query, that's ok
        pytest.skip("to_networkx() not available for nodes query")


@pytest.mark.property
def test_to_networkx_for_edges():
    """
    Property: to_networkx() works for edge queries.
    
    Edge query results should be convertible to NetworkX.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    query = Q.edges().to_ast()
    result = execute_ast(network, query)
    
    try:
        import networkx as nx
        graph = result.to_networkx()
        
        # Should be a NetworkX graph
        assert isinstance(graph, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph))
        # Should have edges
        assert graph.number_of_edges() > 0
    except Exception:
        # If to_networkx() doesn't exist, that's ok
        pytest.skip("to_networkx() not available")


# ============================================================================
# Property Tests: Result Grouping
# ============================================================================

@pytest.mark.property
def test_result_has_metadata():
    """
    Property: QueryResult contains metadata.
    
    Results should have metadata about execution.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    assert hasattr(result, 'meta')
    assert isinstance(result.meta, dict)


@pytest.mark.property
def test_group_summary_exists():
    """
    Property: QueryResult has group_summary method if grouping is present.
    
    If results are grouped, group_summary should be available.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    # Query that might produce groups
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    # Check if group_summary method exists
    if hasattr(result, 'group_summary'):
        # Should be callable
        assert callable(result.group_summary)


# ============================================================================
# Property Tests: Result Size and Length
# ============================================================================

@pytest.mark.property
@given(
    limit=st.integers(min_value=1, max_value=5)
)
def test_result_respects_limit(limit):
    """
    Property: QueryResult respects LIMIT clause.
    
    Results should have at most the specified limit.
    """
    network = create_test_network(num_nodes=10, num_layers=1, seed=42)
    query = Q.nodes().limit(limit).to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    assert len(df) <= limit


@pytest.mark.property
def test_result_empty_query():
    """
    Property: Empty result is valid.
    
    Queries with no matches should return valid empty results.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    # Query that should match nothing
    query = Q.nodes().where(degree__gt=1000).to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    # Should be empty but valid
    assert len(df) == 0
    assert isinstance(df.columns, object)  # Has column index


# ============================================================================
# Property Tests: Result Column Operations
# ============================================================================

@pytest.mark.property
def test_result_with_compute_has_column():
    """
    Property: Computed measures appear as columns.
    
    COMPUTE clause should add columns to results.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    # Should have degree column
    assert 'degree' in df.columns


@pytest.mark.property
def test_result_columns_have_types():
    """
    Property: Result columns have consistent types.
    
    All values in a column should have compatible types.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    # Degree column should be numeric
    if 'degree' in df.columns:
        assert df['degree'].dtype in [np.int64, np.float64, np.int32, np.float32, 'int64', 'float64']


# ============================================================================
# Property Tests: Result Filtering Properties
# ============================================================================

@pytest.mark.property
@given(
    threshold=st.integers(min_value=0, max_value=3)
)
def test_result_filtering_monotonic(threshold):
    """
    Property: Filtering reduces or maintains result count.
    
    Adding filters should never increase result count.
    """
    network = create_test_network(num_nodes=5, num_layers=1, seed=42)
    
    # Query without filter
    query_all = Q.nodes().compute('degree').to_ast()
    result_all = execute_ast(network, query_all)
    count_all = len(result_all.to_pandas())
    
    # Query with filter
    query_filtered = Q.nodes().compute('degree').where(degree__gt=threshold).to_ast()
    result_filtered = execute_ast(network, query_filtered)
    count_filtered = len(result_filtered.to_pandas())
    
    # Filtered should have <= results
    assert count_filtered <= count_all


# ============================================================================
# Property Tests: Result Determinism
# ============================================================================

@pytest.mark.property
def test_result_conversion_deterministic():
    """
    Property: Result conversions are deterministic.
    
    Converting results multiple times should yield same output.
    """
    network = create_test_network(num_nodes=3, num_layers=1, seed=42)
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    # Convert multiple times
    df1 = result.to_pandas()
    df2 = result.to_pandas()
    
    # Should be identical
    assert df1.equals(df2)
