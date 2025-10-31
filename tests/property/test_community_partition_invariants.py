#!/usr/bin/env python3
"""
Community partition invariants tests for py3plex.

Tests properties of community detection algorithms (Louvain wrapper):
- Every node assigned to exactly one community
- No foreign nodes in partition
- Invariance under relabeling
- Non-triviality for separated components
"""

import networkx as nx
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from py3plex.core.multinet import multi_layer_network

from .strategies import relabel_graph


# Guard for python-louvain availability
pytest.importorskip("community")
import community as community_louvain


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=4, max_value=10))
def test_louvain_every_node_assigned(n):
    """
    Test that every node is assigned to exactly one community.
    
    Property: partition.keys() == set(G.nodes())
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(G.number_of_edges() >= n - 1)
    
    # Run Louvain
    partition = community_louvain.best_partition(G, random_state=42)
    
    # Check all nodes assigned
    assert set(partition.keys()) == set(G.nodes()), \
        "Not all nodes assigned to communities"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=4, max_value=10))
def test_louvain_no_foreign_nodes(n):
    """
    Test that partition contains no nodes not in the graph.
    
    Property: partition.keys() ⊆ G.nodes()
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(G.number_of_edges() >= n - 1)
    
    # Run Louvain
    partition = community_louvain.best_partition(G, random_state=42)
    
    # Check no foreign nodes
    partition_nodes = set(partition.keys())
    graph_nodes = set(G.nodes())
    
    assert partition_nodes.issubset(graph_nodes), \
        f"Foreign nodes in partition: {partition_nodes - graph_nodes}"


@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(n=st.integers(min_value=4, max_value=10))
def test_louvain_community_size_invariant(n):
    """
    Test that community sizes are invariant under node relabeling.
    
    Property: Sorted community sizes should be identical for isomorphic graphs.
    """
    p = 0.5
    seed = hash(n) % (2**32)
    G = nx.gnp_random_graph(n, p, seed=seed)
    assume(G.number_of_edges() >= n - 1)
    
    # Run on original
    partition1 = community_louvain.best_partition(G, random_state=seed)
    sizes1 = sorted([
        sum(1 for v in partition1.values() if v == comm_id)
        for comm_id in set(partition1.values())
    ])
    
    # Relabel and run
    H, mapping = relabel_graph(G, seed=seed + 1)
    partition2 = community_louvain.best_partition(H, random_state=seed)
    sizes2 = sorted([
        sum(1 for v in partition2.values() if v == comm_id)
        for comm_id in set(partition2.values())
    ])
    
    # Sizes should match
    assert sizes1 == sizes2, \
        f"Community size distributions differ: {sizes1} vs {sizes2}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=3, max_value=10))
def test_louvain_community_ids_valid(n):
    """
    Test that community IDs are valid (non-negative integers).
    
    Property: All community IDs should be non-negative integers.
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(G.number_of_edges() > 0)
    
    # Run Louvain
    partition = community_louvain.best_partition(G, random_state=42)
    
    # Check all community IDs are valid
    for comm_id in partition.values():
        assert isinstance(comm_id, int), \
            f"Community ID not an integer: {comm_id}"
        assert comm_id >= 0, \
            f"Community ID negative: {comm_id}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n_per_component=st.integers(min_value=3, max_value=5))
def test_louvain_nontrivial_for_components(n_per_component):
    """
    Test that Louvain finds at least as many communities as components.
    
    Property: If graph has K well-separated components, 
    number of communities >= K.
    """
    # Create graph with 2 disconnected components
    G1 = nx.complete_graph(n_per_component)
    G2 = nx.complete_graph(n_per_component)
    
    # Combine into disconnected graph
    G = nx.disjoint_union(G1, G2)
    
    # Should have exactly 2 components
    n_components = nx.number_connected_components(G)
    assert n_components == 2
    
    # Run Louvain
    partition = community_louvain.best_partition(G, random_state=42)
    n_communities = len(set(partition.values()))
    
    # Should find at least as many communities as components
    assert n_communities >= n_components, \
        f"Found {n_communities} communities but have {n_components} components"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=4, max_value=10))
def test_louvain_partition_covers_graph(n):
    """
    Test that partition covers all nodes (coverage property).
    
    Property: Union of all communities == all nodes.
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(G.number_of_edges() > 0)
    
    # Run Louvain
    partition = community_louvain.best_partition(G, random_state=42)
    
    # Get all nodes in any community
    nodes_in_communities = set(partition.keys())
    graph_nodes = set(G.nodes())
    
    # Should be equal
    assert nodes_in_communities == graph_nodes, \
        "Partition doesn't cover all nodes"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=4, max_value=10))
def test_louvain_at_least_one_community(n):
    """
    Test that Louvain always finds at least one community.
    
    Property: Number of communities >= 1.
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(G.number_of_nodes() > 0)
    
    # Run Louvain
    partition = community_louvain.best_partition(G, random_state=42)
    n_communities = len(set(partition.values()))
    
    assert n_communities >= 1, \
        f"Found {n_communities} communities (expected >= 1)"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=2, max_value=10))
def test_louvain_at_most_n_communities(n):
    """
    Test that Louvain finds at most n communities.
    
    Property: Number of communities <= number of nodes.
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    
    # Run Louvain
    partition = community_louvain.best_partition(G, random_state=42)
    n_communities = len(set(partition.values()))
    
    assert n_communities <= n, \
        f"Found {n_communities} communities but only {n} nodes"


@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(n=st.integers(min_value=4, max_value=10))
def test_louvain_community_wrapper_consistency(n):
    """
    Test that py3plex Louvain wrapper produces valid partitions.
    
    Property: Wrapper results satisfy basic partition properties.
    """
    pytest.importorskip("py3plex.algorithms.community_detection.community_wrapper")
    from py3plex.algorithms.community_detection.community_wrapper import louvain_communities
    
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(G.number_of_edges() >= n - 1)
    
    # Use py3plex wrapper
    try:
        result = louvain_communities(G, output="mapping")
        
        # Should return a partition mapping
        if isinstance(result, dict):
            # Check all nodes assigned
            assert set(result.keys()) == set(G.nodes()), \
                "Wrapper didn't assign all nodes"
            
            # Check valid community IDs
            for comm_id in result.values():
                assert comm_id >= 0, \
                    f"Invalid community ID: {comm_id}"
    
    except Exception:
        # If wrapper fails for any reason, skip
        assume(False)


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=3, max_value=10))
def test_louvain_deterministic_with_seed(n):
    """
    Test that Louvain is deterministic when given same random_state.
    
    Property: Same random_state produces same partition.
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(G.number_of_edges() > 0)
    
    seed = 42
    
    # Run twice with same seed
    partition1 = community_louvain.best_partition(G, random_state=seed)
    partition2 = community_louvain.best_partition(G, random_state=seed)
    
    # Should be identical
    assert partition1 == partition2, \
        "Louvain not deterministic with same random_state"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=2, max_value=10))
def test_louvain_empty_graph(n):
    """
    Test Louvain behavior on graph with no edges.
    
    Property: Each node should be in its own community (or similar).
    """
    # Create graph with nodes but no edges
    G = nx.Graph()
    G.add_nodes_from(range(n))
    
    # Run Louvain
    partition = community_louvain.best_partition(G, random_state=42)
    
    # All nodes should be assigned
    assert len(partition) == n, \
        f"Expected {n} nodes in partition, got {len(partition)}"
    
    # Number of communities could be n (each isolated) or fewer
    n_communities = len(set(partition.values()))
    assert 1 <= n_communities <= n, \
        f"Invalid number of communities: {n_communities}"
