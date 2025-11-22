"""
Tests for random walk primitives in py3plex.

This module tests basic and second-order random walks used for graph algorithms
like Node2Vec and DeepWalk.
"""
import networkx as nx
import pytest

from py3plex.algorithms.general.walkers import basic_random_walk


def test_basic_random_walk_simple():
    """Test basic random walk on a simple path graph."""
    G = nx.path_graph(5)  # Linear graph: 0-1-2-3-4
    
    walk = basic_random_walk(G, start_node=0, walk_length=3, seed=42)
    
    assert len(walk) == 4  # start + 3 steps
    assert walk[0] == 0
    # All nodes in walk should be connected
    for i in range(len(walk) - 1):
        assert G.has_edge(walk[i], walk[i+1])


def test_basic_random_walk_weighted():
    """Test weighted random walk."""
    G = nx.Graph()
    G.add_weighted_edges_from([
        (0, 1, 1.0),
        (0, 2, 10.0),  # Much higher weight
    ])
    
    # Run multiple walks to check weight influence
    walks_to_1 = 0
    walks_to_2 = 0
    for seed in range(100):
        walk = basic_random_walk(G, start_node=0, walk_length=1, weighted=True, seed=seed)
        if len(walk) > 1:
            if walk[1] == 1:
                walks_to_1 += 1
            elif walk[1] == 2:
                walks_to_2 += 1
    
    # With 10x weight, should go to node 2 much more often
    assert walks_to_2 > walks_to_1


def test_basic_random_walk_unweighted():
    """Test unweighted random walk."""
    G = nx.Graph()
    G.add_weighted_edges_from([
        (0, 1, 1.0),
        (0, 2, 10.0),
    ])
    
    # Run unweighted walk
    walk = basic_random_walk(G, start_node=0, walk_length=1, weighted=False, seed=42)
    
    assert len(walk) == 2
    assert walk[0] == 0
    assert walk[1] in [1, 2]


def test_basic_random_walk_deterministic():
    """Test that same seed produces same walk."""
    G = nx.karate_club_graph()
    
    walk1 = basic_random_walk(G, start_node=0, walk_length=10, seed=42)
    walk2 = basic_random_walk(G, start_node=0, walk_length=10, seed=42)
    
    assert walk1 == walk2


def test_basic_random_walk_different_seeds():
    """Test that different seeds produce different walks."""
    G = nx.karate_club_graph()
    
    walk1 = basic_random_walk(G, start_node=0, walk_length=10, seed=42)
    walk2 = basic_random_walk(G, start_node=0, walk_length=10, seed=43)
    
    # Should be different (though theoretically could be same by chance)
    # We run long enough that they should differ
    assert walk1 != walk2 or len(walk1) < 5


def test_basic_random_walk_invalid_start_node():
    """Test error handling for invalid start node."""
    G = nx.path_graph(5)
    
    with pytest.raises(ValueError, match="Start node.*not in graph"):
        basic_random_walk(G, start_node=999, walk_length=3)


@pytest.mark.parametrize("walk_length", [0, -1, -5])
def test_basic_random_walk_invalid_length(walk_length):
    """Test error handling for invalid walk lengths."""
    G = nx.path_graph(5)
    
    with pytest.raises(ValueError, match="Walk length must be"):
        basic_random_walk(G, start_node=0, walk_length=walk_length)


def test_basic_random_walk_isolated_node():
    """Test walk on isolated node (no neighbors)."""
    G = nx.Graph()
    G.add_node(0)  # Isolated node
    
    walk = basic_random_walk(G, start_node=0, walk_length=5, seed=42)
    
    # Should only contain the start node (can't move)
    assert walk == [0]


def test_basic_random_walk_directed_graph():
    """Test random walk on directed graph."""
    G = nx.DiGraph()
    G.add_edges_from([
        (0, 1),
        (1, 2),
        (2, 3),
    ])
    
    walk = basic_random_walk(G, start_node=0, walk_length=3, seed=42)
    
    assert len(walk) == 4
    assert walk[0] == 0
    # Check valid directed transitions
    for i in range(len(walk) - 1):
        assert G.has_edge(walk[i], walk[i+1])


def test_basic_random_walk_cycle():
    """Test random walk on cycle graph."""
    G = nx.cycle_graph(5)
    
    walk = basic_random_walk(G, start_node=0, walk_length=10, seed=42)
    
    assert len(walk) == 11
    assert walk[0] == 0
    # All consecutive nodes should be connected
    for i in range(len(walk) - 1):
        assert G.has_edge(walk[i], walk[i+1])


def test_basic_random_walk_complete_graph():
    """Test random walk on complete graph."""
    G = nx.complete_graph(5)
    
    walk = basic_random_walk(G, start_node=0, walk_length=5, seed=42)
    
    assert len(walk) == 6
    assert walk[0] == 0
    # Can reach any node from any node in complete graph
    for node in walk:
        assert node in G.nodes()


def test_basic_random_walk_string_nodes():
    """Test random walk with string node identifiers."""
    G = nx.Graph()
    G.add_edges_from([
        ('A', 'B'),
        ('B', 'C'),
        ('C', 'D'),
    ])
    
    walk = basic_random_walk(G, start_node='A', walk_length=3, seed=42)
    
    assert len(walk) == 4
    assert walk[0] == 'A'
    assert all(isinstance(node, str) for node in walk)


def test_basic_random_walk_single_step():
    """Test single-step walk."""
    G = nx.path_graph(5)
    
    walk = basic_random_walk(G, start_node=2, walk_length=1, seed=42)
    
    assert len(walk) == 2
    assert walk[0] == 2
    assert walk[1] in [1, 3]  # Can go left or right


def test_basic_random_walk_disconnected_component():
    """Test walk stops at disconnected component."""
    G = nx.Graph()
    G.add_edges_from([
        (0, 1),
        (1, 2),
    ])
    G.add_node(3)  # Disconnected
    
    # Start from connected component
    walk = basic_random_walk(G, start_node=0, walk_length=10, seed=42)
    
    # Walk should stay in connected component
    assert all(node in [0, 1, 2] for node in walk)


def test_basic_random_walk_large_graph():
    """Test random walk on larger graph."""
    G = nx.barabasi_albert_graph(100, 3, seed=42)
    
    walk = basic_random_walk(G, start_node=0, walk_length=50, seed=42)
    
    assert len(walk) == 51
    assert walk[0] == 0
    # Verify all transitions are valid
    for i in range(len(walk) - 1):
        assert G.has_edge(walk[i], walk[i+1])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
