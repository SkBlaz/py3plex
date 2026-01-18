"""
Determinism and Reproducibility Tests.

Tests that stochastic algorithms produce identical results with the same seed,
and that provenance hashes are stable across runs.
"""

import pytest
import numpy as np
from py3plex.core import multinet
from py3plex.dsl import Q, L, execute_ast


def get_node_id_column(df):
    """Get the node ID column name (may be 'id' or 'node')."""
    if 'id' in df.columns:
        return 'id'
    elif 'node' in df.columns:
        return 'node'
    else:
        raise KeyError("No node ID column found in DataFrame")


def create_simple_network(seed=42):
    """Create a simple deterministic test network."""
    np.random.seed(seed)
    network = multinet.multi_layer_network(directed=False)
    
    nodes = []
    for i in range(10):
        nodes.append({'source': f'n{i}', 'type': 'layer1'})
        nodes.append({'source': f'n{i}', 'type': 'layer2'})
    network.add_nodes(nodes)
    
    edges = []
    for i in range(9):
        edges.append({
            'source': f'n{i}',
            'target': f'n{i+1}',
            'source_type': 'layer1',
            'target_type': 'layer1',
        })
        edges.append({
            'source': f'n{i}',
            'target': f'n{i+1}',
            'source_type': 'layer2',
            'target_type': 'layer2',
        })
    network.add_edges(edges)
    
    return network


@pytest.mark.verification
@pytest.mark.fast
def test_deterministic_query_same_results():
    """
    Test that deterministic queries produce identical results across runs.
    
    Invariant: No randomness → identical results
    """
    network = create_simple_network(seed=42)
    
    query = Q.nodes().compute('degree').to_ast()
    
    # Run query twice
    result1 = execute_ast(network, query)
    result2 = execute_ast(network, query)
    
    # Results should be identical
    df1 = result1.to_pandas()
    df2 = result2.to_pandas()
    
    assert len(df1) == len(df2), "Result length should be identical"
    
    # Get node ID column (may be 'id' or 'node')
    id_col = get_node_id_column(df1)
    
    assert list(df1[id_col]) == list(df2[id_col]), "Node order should be identical"
    assert list(df1['layer']) == list(df2['layer']), "Layer order should be identical"
    
    # Degree values should be exactly equal (no floating point issues for degree)
    np.testing.assert_array_equal(
        df1['degree'].values,
        df2['degree'].values,
        err_msg="Degree values should be identical across runs"
    )


@pytest.mark.verification
@pytest.mark.fast
def test_provenance_hash_stable():
    """
    Test that AST is stable across multiple query constructions.
    
    Invariant: Same query → same AST
    """
    # Build identical queries using L[] syntax
    from py3plex.dsl import L
    query1 = Q.nodes().from_layers(L['layer1']).compute('degree').to_ast()
    query2 = Q.nodes().from_layers(L['layer1']).compute('degree').to_ast()
    
    # ASTs should be equal
    assert query1 == query2, "AST should be stable for identical queries"
    
    # String representations should also be identical
    assert repr(query1) == repr(query2), "AST repr should be stable"


@pytest.mark.verification
@pytest.mark.fast
def test_seed_controlled_execution():
    """
    Test that seed parameter controls randomness in execution.
    
    This is a placeholder for when stochastic algorithms support seeds.
    Currently tests that deterministic algorithms remain deterministic.
    """
    network = create_simple_network(seed=42)
    
    # Use a deterministic measure
    query = Q.nodes().compute('betweenness_centrality').to_ast()
    
    result1 = execute_ast(network, query)
    result2 = execute_ast(network, query)
    
    df1 = result1.to_pandas()
    df2 = result2.to_pandas()
    
    # Betweenness should be deterministic for this network
    np.testing.assert_allclose(
        df1['betweenness_centrality'].values,
        df2['betweenness_centrality'].values,
        rtol=1e-10,
        err_msg="Deterministic measures should produce identical results"
    )


@pytest.mark.verification
@pytest.mark.fast
def test_empty_network_determinism():
    """
    Test that queries on empty networks are deterministic.
    
    Edge case: Empty input
    """
    network = multinet.multi_layer_network(directed=False)
    
    query = Q.nodes().to_ast()
    
    result1 = execute_ast(network, query)
    result2 = execute_ast(network, query)
    
    assert result1.count == 0, "Empty network should have 0 nodes"
    assert result2.count == 0, "Results should be consistent"
    assert result1.count == result2.count, "Count should be identical"


@pytest.mark.verification  
@pytest.mark.fast
def test_single_node_network_determinism():
    """
    Test determinism on minimal single-node network.
    
    Edge case: Single node
    """
    network = multinet.multi_layer_network(directed=False)
    network.add_nodes([{'source': 'A', 'type': 'layer1'}])
    
    query = Q.nodes().compute('degree').to_ast()
    
    result1 = execute_ast(network, query)
    result2 = execute_ast(network, query)
    
    df1 = result1.to_pandas()
    df2 = result2.to_pandas()
    
    assert len(df1) == 1, "Should have exactly one node"
    assert len(df2) == 1, "Should have exactly one node"
    
    # Single isolated node has degree 0
    assert df1['degree'].iloc[0] == 0, "Isolated node has degree 0"
    assert df2['degree'].iloc[0] == 0, "Result should be consistent"
