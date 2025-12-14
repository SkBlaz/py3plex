"""
Tests for multilayer clustering coefficients.

This module tests the implementation of multilayer clustering coefficients
including intra-layer, multiplex, and supra-adjacency variants.
"""

import pytest
import numpy as np
import networkx as nx

from py3plex.core import multinet
from py3plex.algorithms.multilayer_clustering import (
    multilayer_clustering,
    _build_layer_adjacency,
    _build_state_node_index,
)


class TestMultilayerClustering:
    """Test suite for multilayer clustering coefficients."""

    def test_single_layer_triangle_intra(self):
        """Test that a perfect triangle in a single layer has clustering = 1.0"""
        network = multinet.multi_layer_network()
        
        # Create a perfect triangle: A-B-C with all edges present
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        result = multilayer_clustering(network, coefficient="intra", mode="local")
        
        # All three nodes should have clustering coefficient = 1.0
        assert result[('A', 'L1')] == pytest.approx(1.0)
        assert result[('B', 'L1')] == pytest.approx(1.0)
        assert result[('C', 'L1')] == pytest.approx(1.0)

    def test_two_layer_split_triangle(self):
        """Test multiplex clustering with edges split across two layers."""
        network = multinet.multi_layer_network()
        
        # Create split triangle:
        # Layer L1: A-B, A-C (node A connects to B and C)
        # Layer L2: B-C (closure edge)
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
        ])
        
        result = multilayer_clustering(network, coefficient="multiplex", mode="local")
        
        # Node A has 2 neighbors (B, C) that are connected in L2
        # So clustering for A should be 1.0
        assert result[('A', None)] == pytest.approx(1.0)
        
        # Node B has 2 neighbors (A in L1, C in L2)
        # A and C are connected in L1, so clustering should be 1.0
        assert result[('B', None)] == pytest.approx(1.0)
        
        # Node C has 2 neighbors (A in L1, B in L2)
        # A and B are connected in L1, so clustering should be 1.0
        assert result[('C', None)] == pytest.approx(1.0)

    def test_multiplex_aggregated_vs_per_layer(self):
        """Test multiplex uses union of neighbors across layers."""
        network = multinet.multi_layer_network()
        
        # Node A has different neighbors in each layer
        # L1: A-B, B-C (A neighbors: {B})
        # L2: A-D, D-E (A neighbors: {D})
        # Multiplex: A neighbors: {B, D} - not connected, so clustering = 0
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'D', 'source_type': 'L2', 'target_type': 'L2'},
            {'source': 'D', 'target': 'E', 'source_type': 'L2', 'target_type': 'L2'},
        ])
        
        # Intra-layer: A has only 1 neighbor in each layer, so clustering = 0
        intra_result = multilayer_clustering(network, coefficient="intra", mode="local")
        assert intra_result[('A', 'L1')] == 0.0
        assert intra_result[('A', 'L2')] == 0.0
        
        # Multiplex: A has 2 neighbors {B, D} but they're not connected
        multiplex_result = multilayer_clustering(network, coefficient="multiplex", mode="local")
        assert multiplex_result[('A', None)] == 0.0

    def test_no_triangles(self):
        """Test that networks with no triangles have clustering = 0."""
        network = multinet.multi_layer_network()
        
        # Create a star graph: A-B, A-C, A-D (no triangles)
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'D', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        result = multilayer_clustering(network, coefficient="intra", mode="local")
        
        # A has 3 neighbors but none are connected to each other
        assert result[('A', 'L1')] == 0.0
        
        # B, C, D each have only 1 neighbor (A), so clustering = 0
        assert result[('B', 'L1')] == 0.0
        assert result[('C', 'L1')] == 0.0
        assert result[('D', 'L1')] == 0.0

    def test_intra_validation_vs_networkx(self):
        """Validate intra clustering matches NetworkX for simple cases."""
        network = multinet.multi_layer_network()
        
        # Create a simple graph
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'C', 'target': 'D', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        # Compute using our implementation
        result = multilayer_clustering(network, coefficient="intra", mode="local")
        
        # Compute using NetworkX
        G = nx.Graph()
        G.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'D'), ('A', 'C')])
        nx_clustering = nx.clustering(G)
        
        # Compare values
        for node in ['A', 'B', 'C', 'D']:
            assert result[(node, 'L1')] == pytest.approx(nx_clustering[node], abs=0.001)

    def test_isolated_node(self):
        """Test that isolated nodes have clustering = 0."""
        network = multinet.multi_layer_network()
        
        # Add nodes without edges
        network.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'B', 'type': 'L1'},
        ])
        
        # Add one edge to make it non-empty
        network.add_edges([
            {'source': 'C', 'target': 'D', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        result = multilayer_clustering(network, coefficient="intra", mode="local")
        
        # C and D have only 1 neighbor each
        assert result[('C', 'L1')] == 0.0
        assert result[('D', 'L1')] == 0.0
        
        # A and B are isolated (not in result as they have no edges)
        assert ('A', 'L1') not in result
        assert ('B', 'L1') not in result

    def test_degree_less_than_two(self):
        """Test nodes with degree < 2 have clustering = 0."""
        network = multinet.multi_layer_network()
        
        # Create a chain: A-B-C
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        result = multilayer_clustering(network, coefficient="intra", mode="local")
        
        # A and C have degree 1
        assert result[('A', 'L1')] == 0.0
        assert result[('C', 'L1')] == 0.0
        
        # B has degree 2 but no triangles
        assert result[('B', 'L1')] == 0.0

    def test_empty_network(self):
        """Test behavior with empty network."""
        network = multinet.multi_layer_network()
        
        # Try to compute on empty network
        with pytest.raises(ValueError, match="No layers specified or available"):
            multilayer_clustering(network, coefficient="intra", mode="local")

    def test_invalid_layers(self):
        """Test error handling for invalid layer specifications."""
        network = multinet.multi_layer_network()
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        # Test with non-existent layer
        with pytest.raises(ValueError, match="Invalid layers"):
            multilayer_clustering(
                network, coefficient="intra", mode="local", layers=['NonExistent']
            )

    def test_invalid_coefficient_type(self):
        """Test error handling for invalid coefficient types."""
        network = multinet.multi_layer_network()
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        with pytest.raises(ValueError, match="Invalid coefficient type"):
            multilayer_clustering(network, coefficient="invalid", mode="local")

    def test_invalid_mode(self):
        """Test error handling for invalid modes."""
        network = multinet.multi_layer_network()
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        with pytest.raises(ValueError, match="Invalid mode"):
            multilayer_clustering(network, coefficient="intra", mode="invalid")

    def test_global_mode(self):
        """Test global mode returns average of local coefficients."""
        network = multinet.multi_layer_network()
        
        # Create a simple network
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        # Get local coefficients
        local_result = multilayer_clustering(network, coefficient="intra", mode="local")
        
        # Get global coefficient
        global_result = multilayer_clustering(network, coefficient="intra", mode="global")
        
        # Global should be average of local
        expected_global = sum(local_result.values()) / len(local_result)
        assert global_result == pytest.approx(expected_global)

    def test_supra_adjacency_clustering(self):
        """Test supra-adjacency clustering coefficient computation."""
        network = multinet.multi_layer_network()
        
        # Create a simple triangle in one layer
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        result = multilayer_clustering(network, coefficient="supra", mode="local")
        
        # All nodes in the triangle should have clustering = 1.0
        assert result[('A', 'L1')] == pytest.approx(1.0, abs=0.01)
        assert result[('B', 'L1')] == pytest.approx(1.0, abs=0.01)
        assert result[('C', 'L1')] == pytest.approx(1.0, abs=0.01)

    def test_supra_with_cross_layer_edges(self):
        """Test supra clustering with inter-layer edges."""
        network = multinet.multi_layer_network()
        
        # Create structure with inter-layer edges
        # L1: A-B
        # L2: B-C
        # Inter-layer: A(L1)-A(L2), B(L1)-B(L2), C(L1)-C(L2)
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
            {'source': 'A', 'target': 'A', 'source_type': 'L1', 'target_type': 'L2'},
            {'source': 'B', 'target': 'B', 'source_type': 'L1', 'target_type': 'L2'},
            {'source': 'C', 'target': 'C', 'source_type': 'L1', 'target_type': 'L2'},
        ])
        
        # With cross-layer edges
        result_with = multilayer_clustering(
            network, coefficient="supra", mode="local", include_cross_layer=True
        )
        
        # Without cross-layer edges
        result_without = multilayer_clustering(
            network, coefficient="supra", mode="local", include_cross_layer=False
        )
        
        # Results should differ when cross-layer edges affect triangle counts
        # This is a smoke test - exact values depend on the supra structure
        assert len(result_with) == len(result_without)

    def test_multiple_layers_intra(self):
        """Test intra clustering across multiple layers."""
        network = multinet.multi_layer_network()
        
        # Create triangles in multiple layers
        network.add_edges([
            # Triangle in L1
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            # Triangle in L2
            {'source': 'A', 'target': 'B', 'source_type': 'L2', 'target_type': 'L2'},
            {'source': 'B', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
            {'source': 'A', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
        ])
        
        result = multilayer_clustering(network, coefficient="intra", mode="local")
        
        # All nodes in both layers should have clustering = 1.0
        for layer in ['L1', 'L2']:
            for node in ['A', 'B', 'C']:
                assert result[(node, layer)] == pytest.approx(1.0)

    def test_layer_subset(self):
        """Test computing clustering on a subset of layers."""
        network = multinet.multi_layer_network()
        
        # Create triangles in three layers
        for layer in ['L1', 'L2', 'L3']:
            network.add_edges([
                {'source': 'A', 'target': 'B', 'source_type': layer, 'target_type': layer},
                {'source': 'B', 'target': 'C', 'source_type': layer, 'target_type': layer},
                {'source': 'A', 'target': 'C', 'source_type': layer, 'target_type': layer},
            ])
        
        # Compute only for L1 and L2
        result = multilayer_clustering(
            network, coefficient="intra", mode="local", layers=['L1', 'L2']
        )
        
        # Should have results for L1 and L2, but not L3
        assert ('A', 'L1') in result
        assert ('A', 'L2') in result
        assert ('A', 'L3') not in result

    def test_multiplex_with_partial_overlap(self):
        """Test multiplex clustering with partially overlapping node sets."""
        network = multinet.multi_layer_network()
        
        # L1: A-B-C (chain)
        # L2: B-C-D (chain)
        # Node B appears in both, C appears in both
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
            {'source': 'C', 'target': 'D', 'source_type': 'L2', 'target_type': 'L2'},
        ])
        
        result = multilayer_clustering(network, coefficient="multiplex", mode="local")
        
        # Node B: neighbors are {A, C} in aggregated view
        # A and C are not connected, so clustering = 0
        assert result[('B', None)] == 0.0
        
        # Node C: neighbors are {B, D} in aggregated view
        # B and D are not connected, so clustering = 0
        assert result[('C', None)] == 0.0


class TestHelperFunctions:
    """Test helper functions used in clustering computation."""

    def test_build_layer_adjacency(self):
        """Test _build_layer_adjacency helper function."""
        network = multinet.multi_layer_network()
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        adjacency = _build_layer_adjacency(network, ['L1'])
        
        assert 'L1' in adjacency
        assert 'A' in adjacency['L1']
        assert 'B' in adjacency['L1']['A']
        assert 'A' in adjacency['L1']['B']
        assert 'C' in adjacency['L1']['B']

    def test_build_state_node_index(self):
        """Test _build_state_node_index helper function."""
        network = multinet.multi_layer_network()
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
        ])
        
        state_nodes, state_idx = _build_state_node_index(network, ['L1', 'L2'])
        
        # Should have state nodes for all node-layer combinations
        assert len(state_nodes) > 0
        assert ('A', 'L1') in state_idx
        assert ('B', 'L1') in state_idx
        assert ('A', 'L2') in state_idx
        assert ('C', 'L2') in state_idx
        
        # Indices should be unique and sequential
        assert len(set(state_idx.values())) == len(state_idx)


class TestEdgeCases:
    """Test edge cases and corner cases."""

    def test_self_loops(self):
        """Test handling of self-loops (if present in network)."""
        network = multinet.multi_layer_network()
        
        # Add regular edges
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        # Self-loops are typically ignored in clustering
        result = multilayer_clustering(network, coefficient="intra", mode="local")
        
        # Should compute without errors
        assert len(result) > 0

    def test_large_degree_node(self):
        """Test clustering for a node with many neighbors."""
        network = multinet.multi_layer_network()
        
        # Create a star with 10 neighbors, plus some triangles
        edges = []
        for i in range(10):
            edges.append({
                'source': 'center', 
                'target': f'node{i}', 
                'source_type': 'L1', 
                'target_type': 'L1'
            })
        
        # Connect first 3 neighbors to form triangles
        edges.append({
            'source': 'node0', 
            'target': 'node1', 
            'source_type': 'L1', 
            'target_type': 'L1'
        })
        edges.append({
            'source': 'node1', 
            'target': 'node2', 
            'source_type': 'L1', 
            'target_type': 'L1'
        })
        
        network.add_edges(edges)
        
        result = multilayer_clustering(network, coefficient="intra", mode="local")
        
        # Center has 10 neighbors, 2 triangles among them
        # Clustering = 2 / (10*9/2) = 2/45 ≈ 0.044
        expected = 2.0 / 45.0
        assert result[('center', 'L1')] == pytest.approx(expected, abs=0.01)

    def test_disconnected_components(self):
        """Test clustering with disconnected components."""
        network = multinet.multi_layer_network()
        
        # Create two separate triangles
        network.add_edges([
            # Triangle 1
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'B', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L1', 'target_type': 'L1'},
            # Triangle 2
            {'source': 'X', 'target': 'Y', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'Y', 'target': 'Z', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'X', 'target': 'Z', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        result = multilayer_clustering(network, coefficient="intra", mode="local")
        
        # Both triangles should have clustering = 1.0
        for node in ['A', 'B', 'C', 'X', 'Y', 'Z']:
            assert result[(node, 'L1')] == pytest.approx(1.0)
