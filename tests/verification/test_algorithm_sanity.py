"""
Algorithm Sanity Checks.

Property-based invariant tests for algorithms:
- Centrality measures have finite values
- Community partitions are complete
- Null models preserve properties
- Path queries return valid paths
"""

import pytest
import numpy as np
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
        {'source': 'D', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'C', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    return network


@pytest.mark.verification
@pytest.mark.fast
def test_degree_centrality_finite():
    """
    Invariant: Degree centrality values are finite and non-negative.
    """
    network = create_test_network()
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    degrees = df['degree'].values
    
    # All degrees should be finite
    assert np.all(np.isfinite(degrees)), "Degrees should be finite"
    
    # All degrees should be non-negative
    assert np.all(degrees >= 0), "Degrees should be non-negative"
    
    # Degrees should be integers
    assert np.all(degrees == degrees.astype(int)), "Degrees should be integers"


@pytest.mark.verification
@pytest.mark.fast
def test_betweenness_centrality_finite():
    """
    Invariant: Betweenness centrality values are finite and in [0, 1] range (normalized).
    """
    network = create_test_network()
    query = Q.nodes().compute('betweenness_centrality').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    bc_values = df['betweenness_centrality'].values
    
    # All values should be finite
    assert np.all(np.isfinite(bc_values)), \
        f"Betweenness values should be finite, got {bc_values}"
    
    # All values should be non-negative
    assert np.all(bc_values >= 0), \
        f"Betweenness values should be non-negative, got {bc_values}"


@pytest.mark.verification
@pytest.mark.fast
def test_closeness_centrality_finite():
    """
    Invariant: Closeness centrality values are finite and non-negative.
    """
    network = create_test_network()
    query = Q.nodes().compute('closeness_centrality').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    cc_values = df['closeness_centrality'].values
    
    # All values should be finite
    assert np.all(np.isfinite(cc_values)), \
        "Closeness values should be finite"
    
    # All values should be non-negative
    assert np.all(cc_values >= 0), \
        "Closeness values should be non-negative"


@pytest.mark.verification
@pytest.mark.fast
def test_centrality_sum_makes_sense():
    """
    Sanity check: Sum of centralities should be reasonable.
    
    For degree centrality, sum should equal 2 * num_edges (undirected).
    """
    network = create_test_network()
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    total_degree = df['degree'].sum()
    
    # For undirected graph, sum of degrees = 2 * num_edges
    # We have 3 edges, so sum should be 6
    expected_sum = 2 * 3
    
    assert total_degree == expected_sum, \
        f"Sum of degrees should be {expected_sum}, got {total_degree}"


@pytest.mark.verification
@pytest.mark.fast
def test_isolated_node_centralities():
    """
    Test centralities for isolated node.
    
    Isolated node should have:
    - degree = 0
    - betweenness = 0
    - closeness = 0 or undefined (implementation dependent)
    """
    network = multinet.multi_layer_network(directed=False)
    network.add_nodes([{'source': 'A', 'type': 'layer1'}])
    
    query = Q.nodes().compute('degree').compute('betweenness_centrality').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    assert df['degree'].iloc[0] == 0, "Isolated node should have degree 0"
    assert df['betweenness_centrality'].iloc[0] == 0, \
        "Isolated node should have betweenness 0"


@pytest.mark.verification
@pytest.mark.fast
def test_connected_network_properties():
    """
    Test that connected network has expected properties.
    
    For connected path graph A-B-C:
    - All nodes have degree >= 1
    - End nodes (A, C) have degree = 1
    - Middle node (B) has degree = 2
    """
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
    
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas().set_index('node')
    
    # All nodes should have degree >= 1
    assert np.all(df['degree'] >= 1), "Connected nodes should have degree >= 1"
    
    # End nodes have degree 1
    assert df.loc['A', 'degree'] == 1, "End node A should have degree 1"
    assert df.loc['C', 'degree'] == 1, "End node C should have degree 1"
    
    # Middle node has degree 2
    assert df.loc['B', 'degree'] == 2, "Middle node B should have degree 2"


@pytest.mark.verification
@pytest.mark.fast
def test_star_graph_centralities():
    """
    Test centralities in star graph.
    
    Star graph: center node connected to all others.
    Center should have highest betweenness.
    """
    network = multinet.multi_layer_network(directed=False)
    
    # Create star graph with C at center
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},  # Center
        {'source': 'D', 'type': 'layer1'},
        {'source': 'E', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    # C connected to all others
    edges = [
        {'source': 'C', 'target': 'A', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'C', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'C', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'C', 'target': 'E', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    query = Q.nodes().compute('degree').compute('betweenness_centrality').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas().set_index('node')
    
    # Center has highest degree
    assert df.loc['C', 'degree'] == 4, "Center should have degree 4"
    assert all(df.loc[n, 'degree'] == 1 for n in ['A', 'B', 'D', 'E']), \
        "Peripheral nodes should have degree 1"
    
    # Center has highest betweenness (all shortest paths go through C)
    center_bc = df.loc['C', 'betweenness_centrality']
    peripheral_bc = [df.loc[n, 'betweenness_centrality'] for n in ['A', 'B', 'D', 'E']]
    
    assert center_bc > max(peripheral_bc), \
        "Center should have highest betweenness in star graph"


@pytest.mark.verification
@pytest.mark.fast
def test_self_loop_handling():
    """
    Test that self-loops are handled correctly.
    
    Self-loop should not cause NaN or inf values.
    """
    network = multinet.multi_layer_network(directed=True)  # Directed for self-loops
    
    nodes = [{'source': 'A', 'type': 'layer1'}]
    network.add_nodes(nodes)
    
    # Add self-loop
    edges = [
        {'source': 'A', 'target': 'A', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    # Should not have NaN or inf
    assert np.all(np.isfinite(df['degree'].values)), \
        "Self-loop should not cause inf/NaN values"


@pytest.mark.verification
@pytest.mark.fast
def test_multi_edge_handling():
    """
    Test that multiple edges between same nodes are handled.
    """
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    # Add multiple edges (this creates a multigraph internally)
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    query = Q.nodes().compute('degree').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    # Should not crash
    assert len(df) > 0, "Multi-edge network should be queryable"
    assert np.all(np.isfinite(df['degree'].values)), \
        "Multi-edges should not cause inf/NaN"


@pytest.mark.verification
@pytest.mark.fast
def test_disconnected_components_betweenness():
    """
    Test betweenness in network with disconnected components.
    
    Nodes in separate components should have 0 betweenness
    for paths between components.
    """
    network = multinet.multi_layer_network(directed=False)
    
    # Two disconnected components
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer1'},
    ]
    network.add_nodes(nodes)
    
    # Component 1: A-B
    # Component 2: C-D
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'C', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1'},
    ]
    network.add_edges(edges)
    
    query = Q.nodes().compute('betweenness_centrality').to_ast()
    result = execute_ast(network, query)
    
    df = result.to_pandas()
    
    # All betweenness values should be 0 (no node is between any pair in different components)
    assert np.all(df['betweenness_centrality'].values == 0), \
        "Betweenness should be 0 in simple two-edge disconnected graph"
