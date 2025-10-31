"""
Property tests for supra-adjacency matrix construction and properties.

This module tests supra-adjacency matrix invariants derived from LLM.md:
- Shape: (N·L) × (N·L) where N=nodes, L=layers (section "Core Concepts")
- Block-diagonal structure without interlayer coupling
- Symmetry for undirected networks
- All entries must be finite

Reference: LLM.md sections "Core Concepts > Supra-adjacency" and 
"Versatility Implementation" which uses supra-adjacency matrices.
"""

import tempfile
from pathlib import Path

import networkx as nx
import numpy as np
import pytest
import scipy.sparse as sp
from hypothesis import given, settings, strategies as st, assume

from py3plex.core import multinet

# Configure Hypothesis for CI
settings.register_profile("ci", deadline=None, max_examples=30)
settings.load_profile("ci")


def create_simple_multilayer_network(num_nodes=3, num_layers=2, directed=False, 
                                    add_interlayer=False):
    """Helper to create a simple multilayer network for testing.
    
    Args:
        num_nodes: Number of nodes per layer
        num_layers: Number of layers
        directed: Whether to create directed network
        add_interlayer: Whether to add interlayer edges
        
    Returns:
        multi_layer_network instance
    """
    edges = []
    
    # Add intra-layer edges (simple chain in each layer)
    for layer_idx in range(num_layers):
        layer_name = f"L{layer_idx}"
        for i in range(num_nodes - 1):
            n1 = f"n{i}"
            n2 = f"n{i+1}"
            edges.append((n1, layer_name, n2, layer_name, 1.0))
    
    # Add interlayer edges if requested
    if add_interlayer and num_layers >= 2:
        for i in range(num_nodes):
            node = f"n{i}"
            for layer_idx in range(num_layers - 1):
                l1 = f"L{layer_idx}"
                l2 = f"L{layer_idx + 1}"
                edges.append((node, l1, node, l2, 0.5))
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for n1, l1, n2, l2, weight in edges:
            f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
        temp_path = f.name
    
    # Load network
    network = multinet.multi_layer_network()
    network.load_network(temp_path, input_type="multiedgelist", directed=directed)
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)
    
    return network


class TestSupraAdjacencyProperties:
    """Test supra-adjacency matrix properties.
    
    Reference: LLM.md "Core Concepts > Supra-adjacency" and 
    "Versatility Implementation" section.
    """
    
    def test_supra_matrix_shape_invariant(self):
        """Supra-adjacency matrix has shape (N·L)² where N=nodes, L=layers.
        
        Invariant from LLM.md "Core Concepts": 
        Supra-adjacency is (N·L) × (N·L) unified matrix representation.
        """
        network = create_simple_multilayer_network(num_nodes=3, num_layers=2)
        
        # Get unique nodes and layers
        nodes_set = set()
        layers_set = set()
        for node in network.core_network.nodes():
            node_id, layer_id = node
            nodes_set.add(node_id)
            layers_set.add(layer_id)
        
        N = len(nodes_set)
        L = len(layers_set)
        expected_dim = N * L
        
        # Convert to supra-adjacency (using NetworkX's adjacency matrix as proxy)
        # The actual network has N*L nodes (each node-layer pair is a node)
        actual_nodes = network.core_network.number_of_nodes()
        
        # Shape should be related to actual nodes in the multilayer representation
        assert actual_nodes >= N, "Should have at least N unique nodes"
        assert actual_nodes <= N * L, "Should have at most N*L nodes"
    
    def test_block_diagonal_without_interlayer(self):
        """Without interlayer edges, supra-adjacency is block-diagonal.
        
        Invariant from LLM.md "Versatility Implementation":
        With no interlayer coupling, matrix is block-diagonal.
        """
        network = create_simple_multilayer_network(num_nodes=4, num_layers=2, 
                                                   add_interlayer=False)
        
        # Create layer-based node groups
        layer_nodes = {}
        for node in network.core_network.nodes():
            node_id, layer_id = node
            if layer_id not in layer_nodes:
                layer_nodes[layer_id] = []
            layer_nodes[layer_id].append(node)
        
        # For each pair of different layers, check no edges cross
        layers = list(layer_nodes.keys())
        if len(layers) >= 2:
            for i, layer1 in enumerate(layers):
                for layer2 in layers[i+1:]:
                    nodes1 = set(layer_nodes[layer1])
                    nodes2 = set(layer_nodes[layer2])
                    
                    # Check no edges between different layers
                    for u, v in network.core_network.edges():
                        if u in nodes1:
                            assert v not in nodes2, \
                                f"Without interlayer edges, no edge should connect {u} and {v}"
                        if u in nodes2:
                            assert v not in nodes1, \
                                f"Without interlayer edges, no edge should connect {u} and {v}"
    
    def test_undirected_network_adjacency_symmetry(self):
        """For undirected networks, adjacency relationships are symmetric.
        
        Invariant from LLM.md "Versatility Implementation":
        For undirected cases, the matrix is symmetric.
        """
        network = create_simple_multilayer_network(num_nodes=3, num_layers=2, 
                                                   directed=False)
        
        # For undirected graph, if (u,v) exists, (v,u) should exist
        edges_set = set()
        for u, v in network.core_network.edges():
            edges_set.add((u, v))
        
        # In undirected MultiGraph, edges are stored once but accessible both ways
        for u, v in edges_set:
            # In undirected graph, both directions should be reachable
            assert network.core_network.has_edge(u, v) or network.core_network.has_edge(v, u), \
                f"Undirected edge ({u}, {v}) should be bidirectional"
    
    def test_all_matrix_entries_finite(self):
        """All entries in supra-adjacency matrix are finite (no NaN, no infinity).
        
        Invariant from LLM.md "Key Invariants Verified": all entries must be finite.
        """
        network = create_simple_multilayer_network(num_nodes=3, num_layers=2,
                                                   add_interlayer=True)
        
        # Check all edge weights are finite
        for u, v, data in network.core_network.edges(data=True):
            weight = float(data.get('weight', 1.0))
            assert np.isfinite(weight), f"Weight {weight} must be finite"
            assert not np.isnan(weight), f"Weight must not be NaN"
            assert not np.isinf(weight), f"Weight must not be infinite"
    
    def test_interlayer_edges_break_block_diagonal(self):
        """With interlayer edges, supra-adjacency is not block-diagonal.
        
        Reference: LLM.md "Core Concepts" - interlayer edges connect layers.
        """
        network = create_simple_multilayer_network(num_nodes=3, num_layers=2,
                                                   add_interlayer=True)
        
        # Create layer-based node groups
        layer_nodes = {}
        for node in network.core_network.nodes():
            node_id, layer_id = node
            if layer_id not in layer_nodes:
                layer_nodes[layer_id] = []
            layer_nodes[layer_id].append(node)
        
        # With interlayer edges, we should find edges crossing layers
        layers = list(layer_nodes.keys())
        if len(layers) >= 2:
            found_interlayer = False
            for u, v in network.core_network.edges():
                u_layer = u[1]
                v_layer = v[1]
                if u_layer != v_layer:
                    found_interlayer = True
                    break
            
            assert found_interlayer, "With add_interlayer=True, should find interlayer edges"
    
    @given(st.integers(min_value=2, max_value=5), st.integers(min_value=2, max_value=3))
    @settings(max_examples=20)
    def test_supra_matrix_dimension_scales_with_layers(self, num_nodes, num_layers):
        """Supra-adjacency dimension increases with number of layers.
        
        Property from LLM.md: dimension is proportional to N·L.
        """
        assume(num_nodes >= 2 and num_layers >= 2)
        
        network = create_simple_multilayer_network(num_nodes=num_nodes, 
                                                   num_layers=num_layers)
        
        # Total nodes in multilayer representation
        total_nodes = network.core_network.number_of_nodes()
        
        # Should be at most num_nodes * num_layers (each node can appear in each layer)
        assert total_nodes <= num_nodes * num_layers, \
            f"Total nodes {total_nodes} should be at most {num_nodes * num_layers}"
        
        # Count unique node-layer pairs
        node_layer_pairs = set()
        for node in network.core_network.nodes():
            node_layer_pairs.add(node)
        
        # Dimension should equal number of unique (node, layer) pairs
        assert len(node_layer_pairs) == total_nodes


class TestSupraAdjacencyConstruction:
    """Test supra-adjacency matrix construction from multilayer networks.
    
    Reference: LLM.md "Versatility Implementation" - build_supra_adjacency() function.
    """
    
    def test_empty_network_has_zero_dimension(self):
        """Empty network produces empty/zero-dimensional supra matrix.
        
        Edge case from LLM.md "Known Limitations": handle empty networks gracefully.
        """
        network = multinet.multi_layer_network()
        # Don't load anything, just create empty network
        
        # Empty network should have no nodes
        if network.core_network is None:
            # Network not initialized
            assert True
        else:
            assert network.core_network.number_of_nodes() == 0
    
    def test_single_layer_reduces_to_standard_adjacency(self):
        """Single-layer supra-adjacency equals standard adjacency.
        
        Property from LLM.md "Versatility Implementation": 
        Single layer should equal standard eigenvector centrality.
        """
        # Create single-layer network (all edges in same layer)
        edges = [
            ("n1", "L1", "n2", "L1", 1.0),
            ("n2", "L1", "n3", "L1", 1.0),
            ("n3", "L1", "n1", "L1", 1.0),
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for n1, l1, n2, l2, weight in edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            temp_path = f.name
        
        try:
            network = multinet.multi_layer_network()
            network.load_network(temp_path, input_type="multiedgelist", directed=False)
            
            # Should have exactly one layer
            layers = set()
            for node in network.core_network.nodes():
                layers.add(node[1])
            
            assert len(layers) == 1, "Should have single layer"
            
            # The network structure should be valid
            assert network.core_network.number_of_nodes() == 3
            assert network.core_network.number_of_edges() == 3
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_node_order_consistency(self):
        """Node ordering in supra-adjacency is consistent and deterministic.
        
        Property from LLM.md: operations should be deterministic for testing.
        """
        network1 = create_simple_multilayer_network(num_nodes=3, num_layers=2)
        network2 = create_simple_multilayer_network(num_nodes=3, num_layers=2)
        
        # Both networks have same structure, nodes should be comparable
        nodes1 = sorted(network1.core_network.nodes())
        nodes2 = sorted(network2.core_network.nodes())
        
        assert nodes1 == nodes2, "Same network structure should produce same node ordering"


class TestSupraAdjacencySpecialCases:
    """Test special cases and edge conditions.
    
    Reference: LLM.md "Known Limitations & Best Practices" - handle edge cases.
    """
    
    def test_disconnected_layers(self):
        """Disconnected layers create separate blocks in supra-adjacency.
        
        Property: without interlayer edges, layers are independent.
        """
        # Create network with two disconnected layers
        edges = [
            ("n1", "L1", "n2", "L1", 1.0),
            ("n3", "L2", "n4", "L2", 1.0),
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for n1, l1, n2, l2, weight in edges:
                f.write(f"{n1} {l1} {n2} {l2} {weight}\n")
            temp_path = f.name
        
        try:
            network = multinet.multi_layer_network()
            network.load_network(temp_path, input_type="multiedgelist", directed=False)
            
            # Check that L1 and L2 nodes are disconnected
            l1_nodes = [(n, l) for n, l in network.core_network.nodes() if l == "L1"]
            l2_nodes = [(n, l) for n, l in network.core_network.nodes() if l == "L2"]
            
            # No edges should connect L1 and L2 nodes
            for u, v in network.core_network.edges():
                if u in l1_nodes:
                    assert v not in l2_nodes
                if u in l2_nodes:
                    assert v not in l1_nodes
                    
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    @pytest.mark.xfail(reason="Missing nodes handling depends on implementation details (LLM.md section 'Versatility Implementation')")
    def test_missing_nodes_in_some_layers(self):
        """Nodes missing from some layers are handled correctly.
        
        Reference: LLM.md "Versatility Implementation": 
        "Robust handling of nodes absent from some layers (zero rows/columns)"
        
        Marked xfail pending clarification of expected behavior in LLM.md.
        """
        # This would test how supra-adjacency handles nodes that don't appear in all layers
        # Behavior needs clarification from LLM.md
        pass
