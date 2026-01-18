"""
DSL Semantics Equivalence Tests (Legacy DSL vs DSL v2).

Tests that the builder API and string DSL produce equivalent results
when expressing the same query.
"""

import pytest
import numpy as np
from py3plex.core import multinet
from py3plex.dsl import Q, L, execute_query
from py3plex.dsl.executor import execute_ast


def create_test_network():
    """Create a small test network for equivalence testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Create a simple network with 5 nodes and 2 layers
    nodes = []
    for i in range(5):
        node_id = chr(ord('A') + i)  # A, B, C, D, E
        nodes.append({'source': node_id, 'type': 'social'})
        nodes.append({'source': node_id, 'type': 'work'})
    network.add_nodes(nodes)
    
    # Add edges to create known structure
    edges = [
        # Social layer: path graph A-B-C-D-E
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'C', 'target': 'D', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'D', 'target': 'E', 'source_type': 'social', 'target_type': 'social'},
        # Work layer: star graph with C at center
        {'source': 'C', 'target': 'A', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'C', 'target': 'B', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'C', 'target': 'D', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'C', 'target': 'E', 'source_type': 'work', 'target_type': 'work'},
    ]
    network.add_edges(edges)
    
    return network


@pytest.mark.verification
@pytest.mark.fast
def test_layer_selection_equivalence():
    """
    Test that layer selection works the same in both DSLs.
    
    Query: SELECT nodes FROM layer="social"
    """
    network = create_test_network()
    
    # Legacy DSL
    legacy_result = execute_query(network, 'SELECT nodes FROM layer="social"')
    
    # DSL v2
    v2_query = Q.nodes().from_layers(L['social']).to_ast()
    v2_result = execute_ast(network, v2_query)
    
    # Both should return 5 nodes from social layer
    assert legacy_result.count == v2_result.count, \
        f"Count mismatch: legacy={legacy_result.count}, v2={v2_result.count}"
    assert legacy_result.count == 5, "Should have 5 nodes in social layer"
    
    # Extract node IDs
    legacy_nodes = set((item['node'], item['layer']) for item in legacy_result.items)
    v2_nodes = set((item['node'], item['layer']) for item in v2_result.items)
    
    assert legacy_nodes == v2_nodes, "Node sets should be identical"


@pytest.mark.verification
@pytest.mark.fast
def test_degree_filter_equivalence():
    """
    Test that degree filtering works the same in both DSLs.
    
    Query: SELECT nodes WHERE degree > 2
    """
    network = create_test_network()
    
    # Legacy DSL
    legacy_result = execute_query(network, 'SELECT nodes WHERE degree > 2')
    
    # DSL v2
    v2_query = Q.nodes().where(degree__gt=2).to_ast()
    v2_result = execute_ast(network, v2_query)
    
    # Extract node sets (ignoring order)
    legacy_nodes = set((item['node'], item['layer']) for item in legacy_result.items)
    v2_nodes = set((item['node'], item['layer']) for item in v2_result.items)
    
    assert legacy_nodes == v2_nodes, \
        f"Node sets differ: legacy={legacy_nodes}, v2={v2_nodes}"


@pytest.mark.verification
@pytest.mark.fast
def test_compute_degree_equivalence():
    """
    Test that computing degree works the same in both DSLs.
    
    Query: SELECT nodes COMPUTE degree
    """
    network = create_test_network()
    
    # Legacy DSL
    legacy_result = execute_query(network, 'SELECT nodes COMPUTE degree')
    
    # DSL v2
    v2_query = Q.nodes().compute('degree').to_ast()
    v2_result = execute_ast(network, v2_query)
    
    # Same count
    assert legacy_result.count == v2_result.count
    
    # Convert to pandas and sort for comparison
    legacy_df = legacy_result.to_pandas().sort_values(['node', 'layer']).reset_index(drop=True)
    v2_df = v2_result.to_pandas().sort_values(['node', 'layer']).reset_index(drop=True)
    
    # Check columns exist
    assert 'degree' in legacy_df.columns, "Legacy result should have degree column"
    assert 'degree' in v2_df.columns, "V2 result should have degree column"
    
    # Check degree values match
    np.testing.assert_array_equal(
        legacy_df['degree'].values,
        v2_df['degree'].values,
        err_msg="Degree values should match between DSL versions"
    )


@pytest.mark.verification
@pytest.mark.fast
def test_combined_filter_and_compute_equivalence():
    """
    Test combined WHERE + COMPUTE equivalence.
    
    Query: SELECT nodes FROM layer="work" WHERE degree > 1 COMPUTE degree
    """
    network = create_test_network()
    
    # Legacy DSL
    legacy_result = execute_query(
        network,
        'SELECT nodes FROM layer="work" WHERE degree > 1 COMPUTE degree'
    )
    
    # DSL v2
    v2_query = (
        Q.nodes()
        .from_layers(L['work'])
        .where(degree__gt=1)
        .compute('degree')
        .to_ast()
    )
    v2_result = execute_ast(network, v2_query)
    
    # Sort and compare
    legacy_df = legacy_result.to_pandas().sort_values(['node', 'layer']).reset_index(drop=True)
    v2_df = v2_result.to_pandas().sort_values(['node', 'layer']).reset_index(drop=True)
    
    assert len(legacy_df) == len(v2_df), "Should have same number of results"
    assert list(legacy_df['node']) == list(v2_df['node']), "Nodes should match"
    np.testing.assert_array_equal(legacy_df['degree'].values, v2_df['degree'].values)


@pytest.mark.verification
@pytest.mark.fast
def test_order_by_limit_equivalence():
    """
    Test that ORDER BY + LIMIT work the same in both DSLs.
    
    Query: SELECT nodes COMPUTE degree ORDER BY degree DESC LIMIT 3
    """
    network = create_test_network()
    
    # Legacy DSL
    legacy_result = execute_query(
        network,
        'SELECT nodes COMPUTE degree ORDER BY degree DESC LIMIT 3'
    )
    
    # DSL v2
    v2_query = (
        Q.nodes()
        .compute('degree')
        .order_by('degree', desc=True)
        .limit(3)
        .to_ast()
    )
    v2_result = execute_ast(network, v2_query)
    
    # Both should return exactly 3 results
    assert legacy_result.count == 3, "Legacy should return 3 results"
    assert v2_result.count == 3, "V2 should return 3 results"
    
    # Convert to DataFrames (already ordered)
    legacy_df = legacy_result.to_pandas()
    v2_df = v2_result.to_pandas()
    
    # Check degree values are in descending order
    assert all(legacy_df['degree'].iloc[i] >= legacy_df['degree'].iloc[i+1] 
               for i in range(len(legacy_df)-1)), "Legacy results should be ordered"
    assert all(v2_df['degree'].iloc[i] >= v2_df['degree'].iloc[i+1] 
               for i in range(len(v2_df)-1)), "V2 results should be ordered"
    
    # Top 3 degree values should match
    np.testing.assert_array_equal(
        legacy_df['degree'].values,
        v2_df['degree'].values,
        err_msg="Top 3 degree values should match"
    )


@pytest.mark.verification
@pytest.mark.fast
def test_edge_query_equivalence():
    """
    Test that edge queries work the same in both DSLs.
    
    Query: SELECT edges FROM layer="social"
    """
    network = create_test_network()
    
    # Legacy DSL
    legacy_result = execute_query(network, 'SELECT edges FROM layer="social"')
    
    # DSL v2
    v2_query = Q.edges().from_layers(L['social']).to_ast()
    v2_result = execute_ast(network, v2_query)
    
    # Same count
    assert legacy_result.count == v2_result.count, \
        f"Edge count mismatch: legacy={legacy_result.count}, v2={v2_result.count}"
    
    # Extract edge sets (source, target, source_layer, target_layer)
    def edge_set(result):
        return set(
            (item.get('source'), item.get('target'), 
             item.get('source_layer'), item.get('target_layer'))
            for item in result.items
        )
    
    legacy_edges = edge_set(legacy_result)
    v2_edges = edge_set(v2_result)
    
    assert legacy_edges == v2_edges, "Edge sets should be identical"


@pytest.mark.verification
@pytest.mark.fast
def test_empty_result_equivalence():
    """
    Test that queries returning no results behave identically.
    
    Query: SELECT nodes WHERE degree > 100  (impossible condition)
    """
    network = create_test_network()
    
    # Legacy DSL
    legacy_result = execute_query(network, 'SELECT nodes WHERE degree > 100')
    
    # DSL v2
    v2_query = Q.nodes().where(degree__gt=100).to_ast()
    v2_result = execute_ast(network, v2_query)
    
    # Both should be empty
    assert legacy_result.count == 0, "Legacy result should be empty"
    assert v2_result.count == 0, "V2 result should be empty"
    assert len(legacy_result.items) == 0, "Legacy items should be empty"
    assert len(v2_result.items) == 0, "V2 items should be empty"


@pytest.mark.verification
@pytest.mark.fast
def test_multiple_layers_equivalence():
    """
    Test querying multiple layers produces same results.
    
    Query: SELECT nodes FROM layer IN ("social", "work")
    """
    network = create_test_network()
    
    # DSL v2 (legacy doesn't support IN syntax easily, so test v2 behavior)
    v2_query = Q.nodes().from_layers(['social', 'work']).to_ast()
    v2_result = execute_ast(network, v2_query)
    
    # Should return all 10 nodes (5 nodes x 2 layers)
    assert v2_result.count == 10, "Should return all nodes from both layers"
    
    # Verify both layers are present
    df = v2_result.to_pandas()
    layers = set(df['layer'])
    assert layers == {'social', 'work'}, "Both layers should be present"
