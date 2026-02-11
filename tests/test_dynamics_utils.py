"""
Tests for py3plex.dynamics._utils module.

This module tests utility functions for working with multilayer networks
in dynamics simulations.
"""

import pytest
import networkx as nx
import numpy as np
from py3plex.dynamics._utils import (
    iter_multilayer_nodes,
    iter_multilayer_neighbors,
    get_adjacency_matrix,
    dict_state_to_vector,
    vector_to_dict_state,
    get_node_layer_info,
    count_infected_neighbors,
)


class TestIterMultilayerNodes:
    """Test iter_multilayer_nodes function."""

    def test_networkx_graph(self):
        """Test iteration over NetworkX graph nodes."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3])
        
        nodes = list(iter_multilayer_nodes(G))
        
        assert len(nodes) == 3
        assert set(nodes) == {1, 2, 3}

    def test_multilayer_network(self):
        """Test iteration over py3plex multilayer network nodes."""
        from py3plex.core import multinet
        
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        
        nodes = list(iter_multilayer_nodes(net))
        
        assert len(nodes) >= 2  # At least A and B in some form

    def test_unsupported_type(self):
        """Test error for unsupported graph type."""
        with pytest.raises(TypeError, match="Unsupported graph type"):
            list(iter_multilayer_nodes("not a graph"))


class TestIterMultilayerNeighbors:
    """Test iter_multilayer_neighbors function."""

    def test_networkx_graph(self):
        """Test iteration over neighbors in NetworkX graph."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (1, 3)])
        
        neighbors = list(iter_multilayer_neighbors(G, 1))
        
        assert len(neighbors) == 2
        assert set(neighbors) == {2, 3}

    def test_networkx_no_neighbors(self):
        """Test node with no neighbors."""
        G = nx.Graph()
        G.add_node(1)
        
        neighbors = list(iter_multilayer_neighbors(G, 1))
        
        assert len(neighbors) == 0

    def test_unsupported_type(self):
        """Test error for unsupported graph type."""
        with pytest.raises(TypeError, match="Unsupported graph type"):
            list(iter_multilayer_neighbors("not a graph", 1))


class TestGetAdjacencyMatrix:
    """Test get_adjacency_matrix function."""

    def test_simple_graph(self):
        """Test adjacency matrix for simple undirected graph."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2)])
        
        adj, node_to_idx = get_adjacency_matrix(G)
        
        assert adj.shape == (3, 3)
        assert len(node_to_idx) == 3
        # Check symmetry for undirected graph
        assert adj[0, 1] == adj[1, 0]
        assert adj[1, 2] == adj[2, 1]

    def test_weighted_graph(self):
        """Test adjacency matrix with edge weights."""
        G = nx.Graph()
        G.add_edge(0, 1, weight=2.5)
        G.add_edge(1, 2, weight=3.0)
        
        adj, node_to_idx = get_adjacency_matrix(G)
        
        # Check weights are preserved
        i, j = node_to_idx[0], node_to_idx[1]
        assert adj[i, j] == 2.5
        assert adj[j, i] == 2.5  # Symmetric

    def test_directed_graph(self):
        """Test adjacency matrix for directed graph."""
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (1, 2)])
        
        adj, node_to_idx = get_adjacency_matrix(G)
        
        # Check asymmetry for directed graph
        i, j = node_to_idx[0], node_to_idx[1]
        assert adj[i, j] == 1.0
        assert adj[j, i] == 0.0  # No edge from 1 to 0

    def test_custom_nodelist(self):
        """Test adjacency matrix with custom nodelist."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])
        
        # Only include nodes 0, 1, 2
        adj, node_to_idx = get_adjacency_matrix(G, nodelist=[0, 1, 2])
        
        assert adj.shape == (3, 3)
        assert len(node_to_idx) == 3
        assert 3 not in node_to_idx


class TestDictStateToVector:
    """Test dict_state_to_vector function."""

    def test_simple_conversion(self):
        """Test converting dict state to vector."""
        state = {0: 1.0, 1: 0.0, 2: 1.0}
        node_to_idx = {0: 0, 1: 1, 2: 2}
        
        vector = dict_state_to_vector(state, node_to_idx)
        
        assert len(vector) == 3
        assert vector[0] == 1.0
        assert vector[1] == 0.0
        assert vector[2] == 1.0

    def test_partial_state(self):
        """Test conversion with partial state (missing nodes)."""
        state = {0: 1.0, 2: 1.0}  # Node 1 missing
        node_to_idx = {0: 0, 1: 1, 2: 2}
        
        vector = dict_state_to_vector(state, node_to_idx)
        
        assert len(vector) == 3
        assert vector[0] == 1.0
        assert vector[1] == 0.0  # Default to 0
        assert vector[2] == 1.0


class TestVectorToDictState:
    """Test vector_to_dict_state function."""

    def test_simple_conversion(self):
        """Test converting vector to dict state."""
        vector = np.array([1.0, 0.0, 1.0])
        idx_to_node = {0: 'A', 1: 'B', 2: 'C'}
        
        state = vector_to_dict_state(vector, idx_to_node)
        
        assert len(state) == 3
        assert state['A'] == 1.0
        assert state['B'] == 0.0
        assert state['C'] == 1.0

    def test_roundtrip(self):
        """Test roundtrip conversion: dict → vector → dict."""
        original = {0: 1.0, 1: 0.5, 2: 0.0}
        node_to_idx = {0: 0, 1: 1, 2: 2}
        idx_to_node = {0: 0, 1: 1, 2: 2}
        
        vector = dict_state_to_vector(original, node_to_idx)
        restored = vector_to_dict_state(vector, idx_to_node)
        
        assert original == restored


class TestGetNodeLayerInfo:
    """Test get_node_layer_info function."""

    def test_networkx_graph(self):
        """Test that regular NetworkX graph returns None."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3])
        
        layer_info = get_node_layer_info(G)
        
        assert layer_info is None

    def test_multilayer_network(self):
        """Test extracting layer info from multilayer network."""
        from py3plex.core import multinet
        
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'social'},
            {'source': 'B', 'type': 'work'},
        ])
        
        layer_info = get_node_layer_info(net)
        
        # Should have layer info for nodes
        assert layer_info is not None or layer_info == {}


class TestCountInfectedNeighbors:
    """Test count_infected_neighbors function."""

    def test_simple_count(self):
        """Test counting infected neighbors."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (1, 3), (1, 4)])
        
        state = {1: 0, 2: 1, 3: 1, 4: 0}  # 2 and 3 are infected
        
        count = count_infected_neighbors(G, 1, state, infected_value=1)
        
        assert count == 2

    def test_no_infected_neighbors(self):
        """Test when no neighbors are infected."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (1, 3)])
        
        state = {1: 0, 2: 0, 3: 0}  # All susceptible
        
        count = count_infected_neighbors(G, 1, state, infected_value=1)
        
        assert count == 0

    def test_all_infected_neighbors(self):
        """Test when all neighbors are infected."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (1, 3)])
        
        state = {1: 0, 2: 1, 3: 1}  # All neighbors infected
        
        count = count_infected_neighbors(G, 1, state, infected_value=1)
        
        assert count == 2

    def test_isolated_node(self):
        """Test isolated node with no neighbors."""
        G = nx.Graph()
        G.add_node(1)
        
        state = {1: 0}
        
        count = count_infected_neighbors(G, 1, state, infected_value=1)
        
        assert count == 0

    def test_custom_infected_value(self):
        """Test with custom infected value."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (1, 3)])
        
        state = {1: 0, 2: 5, 3: 5}  # Infected value is 5
        
        count = count_infected_neighbors(G, 1, state, infected_value=5)
        
        assert count == 2
