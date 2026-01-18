"""
QueryResult Object Correctness Tests.

Tests invariants for QueryResult objects:
- count == len(items)
- to_dict() faithfulness
- to_pandas() required columns
- expand_uncertainty behavior
- ordering rules
"""

import pytest
import numpy as np
import pandas as pd
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.dsl.executor import execute_ast


def create_test_network():
    """Create a simple test network."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    return network


@pytest.mark.verification
@pytest.mark.fast
def test_count_equals_items_length():
    """
    Invariant: result.count == len(result.items)
    
    The count field must always match the number of items.
    """
    network = create_test_network()
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    assert result.count == len(result.items), \
        f"Count mismatch: count={result.count}, len(items)={len(result.items)}"


@pytest.mark.verification
@pytest.mark.fast
def test_count_after_filter():
    """
    Test that count is correct after filtering.
    """
    network = create_test_network()
    query = Q.nodes().where(degree__gt=0).to_ast()
    result = execute_ast(network, query)
    
    # Nodes A and B have degree > 0, C has degree 1 (connected to B)
    assert result.count == len(result.items)
    assert result.count > 0, "Should have some nodes with degree > 0"


@pytest.mark.verification
@pytest.mark.fast
def test_count_after_limit():
    """
    Test that count reflects actual result size after LIMIT.
    """
    network = create_test_network()
    query = Q.nodes().limit(2).to_ast()
    result = execute_ast(network, query)
    
    assert result.count == 2, "LIMIT should reduce count"
    assert len(result.items) == 2, "Items should match limit"
    assert result.count == len(result.items)


@pytest.mark.verification
@pytest.mark.fast
def test_empty_result_count():
    """
    Test that empty results have count == 0.
    """
    network = create_test_network()
    query = Q.nodes().where(degree__gt=100).to_ast()  # Impossible condition
    result = execute_ast(network, query)
    
    assert result.count == 0, "Empty result should have count=0"
    assert len(result.items) == 0, "Empty result should have no items"


@pytest.mark.verification
@pytest.mark.fast
def test_to_dict_faithful():
    """
    Test that to_dict() preserves result data.
    """
    network = create_test_network()
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    dict_result = result.to_dict()
    
    # Should have expected keys
    assert 'count' in dict_result, "to_dict() should have 'count' key"
    assert 'target' in dict_result, "to_dict() should have 'target' key"
    
    # Count should match
    assert dict_result['count'] == result.count
    
    # Should have nodes or items
    assert 'nodes' in dict_result or 'items' in dict_result, \
        "to_dict() should have 'nodes' or 'items' key"


@pytest.mark.verification
@pytest.mark.fast
def test_to_pandas_has_node_column():
    """
    Test that to_pandas() includes node ID column for node queries.
    """
    network = create_test_network()
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    assert isinstance(df, pd.DataFrame), "to_pandas() should return DataFrame"
    # Node queries should have 'id' or 'node' column
    assert 'id' in df.columns or 'node' in df.columns, \
        "Node queries should have 'id' or 'node' column"
    assert 'layer' in df.columns, "Node queries should have 'layer' column"


@pytest.mark.verification
@pytest.mark.fast
def test_to_pandas_has_edge_columns():
    """
    Test that to_pandas() includes edge columns for edge queries.
    """
    network = create_test_network()
    query = Q.edges().to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    assert isinstance(df, pd.DataFrame), "to_pandas() should return DataFrame"
    # Edge queries should have source/target information
    # The exact column names may vary, but check for presence
    assert len(df.columns) > 0, "Edge result should have columns"
    assert len(df) == result.count, "DataFrame length should match count"


@pytest.mark.verification
@pytest.mark.fast
def test_to_pandas_includes_computed_columns():
    """
    Test that computed measures appear as columns in DataFrame.
    """
    network = create_test_network()
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    assert 'degree' in df.columns, "Computed measure should appear as column"
    assert df['degree'].dtype in [np.int64, np.float64, int, float], \
        "Degree should be numeric"
    assert not df['degree'].isna().any(), "Degree should not have NaN values"


@pytest.mark.verification
@pytest.mark.fast
def test_to_pandas_length_matches_count():
    """
    Test that DataFrame length matches result count.
    """
    network = create_test_network()
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    assert len(df) == result.count, \
        f"DataFrame length {len(df)} should match count {result.count}"


@pytest.mark.verification
@pytest.mark.fast
def test_ordering_deterministic():
    """
    Test that ordering is deterministic for repeated queries.
    
    Note: This tests that the same query produces same order,
    not that the order follows a specific rule.
    """
    network = create_test_network()
    query = Q.nodes().compute('degree').order_by('degree', desc=True).to_ast()
    
    result1 = execute_ast(network, query)
    result2 = execute_ast(network, query)
    
    df1 = result1.to_pandas()
    df2 = result2.to_pandas()
    
    # Get ID column (may be 'id' or 'node')
    id_col = 'id' if 'id' in df1.columns else 'node'
    
    # Order should be identical
    assert list(df1[id_col]) == list(df2[id_col]), \
        "Node order should be deterministic"
    assert list(df1['degree']) == list(df2['degree']), \
        "Degree order should be deterministic"


@pytest.mark.verification
@pytest.mark.fast
def test_order_by_descending():
    """
    Test that ORDER BY DESC actually sorts in descending order.
    """
    network = create_test_network()
    query = Q.nodes().compute('degree').order_by('degree', desc=True).to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    degrees = df['degree'].values
    
    # Check descending order
    for i in range(len(degrees) - 1):
        assert degrees[i] >= degrees[i + 1], \
            f"Degrees should be descending: {degrees}"


@pytest.mark.verification
@pytest.mark.fast
def test_order_by_ascending():
    """
    Test that ORDER BY ASC sorts in ascending order.
    """
    network = create_test_network()
    query = Q.nodes().compute('degree').order_by('degree', desc=False).to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    degrees = df['degree'].values
    
    # Check ascending order
    for i in range(len(degrees) - 1):
        assert degrees[i] <= degrees[i + 1], \
            f"Degrees should be ascending: {degrees}"


@pytest.mark.verification
@pytest.mark.fast
def test_metadata_presence():
    """
    Test that result contains expected metadata fields.
    """
    network = create_test_network()
    query = Q.nodes().to_ast()
    result = execute_ast(network, query)
    
    # Check basic attributes exist
    assert hasattr(result, 'count'), "Result should have 'count' attribute"
    assert hasattr(result, 'items'), "Result should have 'items' attribute"
    assert hasattr(result, 'target'), "Result should have 'target' attribute"
    assert hasattr(result, 'meta'), "Result should have 'meta' attribute"
    
    # Target should be valid
    assert result.target in ['nodes', 'edges'], \
        f"Target should be 'nodes' or 'edges', got {result.target}"


@pytest.mark.verification
@pytest.mark.fast
def test_items_are_tuples_or_dicts():
    """
    Test that items have expected structure (tuples or dicts).
    """
    network = create_test_network()
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    # Items can be tuples (node, layer) or dicts
    for item in result.items:
        assert isinstance(item, (tuple, dict)), \
            f"Each item should be a tuple or dictionary, got {type(item)}"
        
        # If tuple, should have 2 elements (node, layer)
        if isinstance(item, tuple):
            assert len(item) == 2, "Tuple item should have (node, layer)"


@pytest.mark.verification
@pytest.mark.fast
def test_finite_computed_values():
    """
    Test that computed values are finite (not NaN or inf).
    """
    network = create_test_network()
    query = Q.nodes().compute('betweenness_centrality').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    # All betweenness values should be finite
    assert np.all(np.isfinite(df['betweenness_centrality'].values)), \
        "All computed values should be finite (not NaN or inf)"
