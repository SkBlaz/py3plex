#!/usr/bin/env python3
"""
Property-based tests for community detection.

Tests Louvain community detection wrapper invariants.
"""

import networkx as nx
import pytest
from hypothesis import given, strategies as st, settings, assume

from py3plex.core import multinet

# Try to import community detection, but handle gracefully if not available
try:
    from py3plex.algorithms.community_detection import community_wrapper as cw
    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False
    cw = None

# Check if python-louvain is installed
try:
    import community as community_louvain
    PYTHON_LOUVAIN_AVAILABLE = True
except ImportError:
    PYTHON_LOUVAIN_AVAILABLE = False


@pytest.mark.skipif(
    not LOUVAIN_AVAILABLE or not PYTHON_LOUVAIN_AVAILABLE,
    reason="Louvain community detection not available"
)
@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(n=st.integers(min_value=3, max_value=15))
def test_louvain_partition_covers_all_nodes(n):
    """
    Test that Louvain partition covers all nodes exactly once.
    
    Property: 
    - Every node appears in exactly one community
    - Partition keys exactly match the node set
    """
    # Create a simple connected graph
    G = nx.cycle_graph(n)
    
    network = multinet.multi_layer_network(directed=False)
    network.load_network(G, input_type="nx", directed=False)
    
    # Get Louvain communities
    partition = cw.louvain_communities(network)
    
    # Check that all nodes are covered
    assert set(partition.keys()) == set(network.core_network.nodes()), \
        f"Partition keys {set(partition.keys())} != nodes {set(network.core_network.nodes())}"
    
    # Check that all community IDs are valid integers
    assert all(isinstance(c, int) and c >= 0 for c in partition.values()), \
        f"Invalid community IDs: {partition.values()}"


@pytest.mark.skipif(
    not LOUVAIN_AVAILABLE or not PYTHON_LOUVAIN_AVAILABLE,
    reason="Louvain community detection not available"
)
@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(n=st.integers(min_value=4, max_value=12))
def test_louvain_num_communities_bounded(n):
    """
    Test that number of communities is bounded by number of nodes.
    
    Property: 1 <= num_communities <= num_nodes
    """
    G = nx.gnp_random_graph(n, 0.3, seed=hash(n) % (2**32))
    assume(nx.is_connected(G))
    
    network = multinet.multi_layer_network(directed=False)
    network.load_network(G, input_type="nx", directed=False)
    
    partition = cw.louvain_communities(network)
    
    # Count unique communities
    num_communities = len(set(partition.values()))
    
    assert 1 <= num_communities <= n, \
        f"Num communities {num_communities} not in range [1, {n}]"


@pytest.mark.skipif(
    not LOUVAIN_AVAILABLE or not PYTHON_LOUVAIN_AVAILABLE,
    reason="Louvain community detection not available"
)
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=3, max_value=10))
def test_louvain_complete_graph_single_community(n):
    """
    Test that complete graph has single community.
    
    Property: Complete graphs (fully connected) should be detected
    as a single community.
    """
    G = nx.complete_graph(n)
    
    network = multinet.multi_layer_network(directed=False)
    network.load_network(G, input_type="nx", directed=False)
    
    partition = cw.louvain_communities(network)
    
    # Complete graph should have 1 community
    num_communities = len(set(partition.values()))
    
    assert num_communities == 1, \
        f"Complete graph should have 1 community, got {num_communities}"


@pytest.mark.skipif(
    not LOUVAIN_AVAILABLE or not PYTHON_LOUVAIN_AVAILABLE,
    reason="Louvain community detection not available"
)
@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(k=st.integers(min_value=2, max_value=5))
def test_louvain_disconnected_components_separate_communities(k):
    """
    Test that disconnected components are in different communities.
    
    Property: For a graph with k disconnected components,
    there should be at least k communities.
    """
    # Create k disconnected cliques
    G = nx.Graph()
    for i in range(k):
        # Add a small clique for each component
        size = 3
        nodes = [f"c{i}_n{j}" for j in range(size)]
        G.add_nodes_from(nodes)
        for u in nodes:
            for v in nodes:
                if u != v:
                    G.add_edge(u, v)
    
    # Verify we have k components
    assert nx.number_connected_components(G) == k
    
    network = multinet.multi_layer_network(directed=False)
    network.load_network(G, input_type="nx", directed=False)
    
    partition = cw.louvain_communities(network)
    
    # Should have at least k communities (one per component)
    num_communities = len(set(partition.values()))
    
    assert num_communities >= k, \
        f"Expected at least {k} communities for {k} components, got {num_communities}"


@pytest.mark.skipif(
    not LOUVAIN_AVAILABLE or not PYTHON_LOUVAIN_AVAILABLE,
    reason="Louvain community detection not available"
)
@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(n=st.integers(min_value=6, max_value=12))
def test_louvain_partition_valid_structure(n):
    """
    Test that partition has valid structure.
    
    Property: Partition is a dict mapping nodes to community IDs.
    """
    G = nx.karate_club_graph() if n >= 34 else nx.gnp_random_graph(
        n, 0.4, seed=hash(n) % (2**32)
    )
    assume(G.number_of_nodes() > 0)
    
    network = multinet.multi_layer_network(directed=False)
    network.load_network(G, input_type="nx", directed=False)
    
    partition = cw.louvain_communities(network)
    
    # Check structure
    assert isinstance(partition, dict), \
        f"Partition should be dict, got {type(partition)}"
    
    # Note: Louvain may not include isolated nodes (nodes with no edges)
    # Check that at least connected nodes are in partition
    connected_nodes = set(G.nodes()) - set(nx.isolates(G))
    assert len(partition) >= len(connected_nodes), \
        f"Partition size {len(partition)} < connected nodes {len(connected_nodes)}"
    
    # Check each partitioned node is mapped to exactly one community
    for node in partition.keys():
        assert isinstance(partition[node], int), \
            f"Community ID for {node} is not int: {partition[node]}"
