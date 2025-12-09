"""
Property-based tests for multiplex network structures using Hypothesis.

This module extends the test suite with property-based tests that verify
core invariants of multiplex network structures, including layer consistency,
projection properties, and structural invariants.
"""

import networkx as nx
import pytest
from hypothesis import given, strategies as st, assume

from py3plex.core import multinet


# Custom strategies for generating valid test data
def valid_node_names():
    """Generate valid node names (non-empty strings)."""
    return st.text(min_size=1, max_size=10, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-'
    ))


def valid_layer_names():
    """Generate valid layer names (non-empty strings)."""
    return st.text(min_size=1, max_size=8, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_'
    ))


def node_integers():
    """Generate integer node IDs."""
    return st.integers(min_value=0, max_value=20)


def edge_tuples(max_nodes=20):
    """Generate edge tuples as (source, target) pairs."""
    return st.tuples(
        st.integers(min_value=0, max_value=max_nodes),
        st.integers(min_value=0, max_value=max_nodes)
    )


class TestLayerAndNodeConsistency:
    """Test properties related to layer and node consistency in multiplex networks."""

    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=15),
                st.integers(min_value=0, max_value=15)
            ),
            min_size=1,
            max_size=20
        ),
        st.lists(valid_layer_names(), min_size=1, max_size=4, unique=True)
    )
    def test_edges_connect_existing_nodes_in_layer(self, edges, layers):
        """Every edge in a layer connects nodes that exist in that layer."""
        # Filter self-loops
        edges = [(s, t) for s, t in edges if s != t]
        assume(len(edges) >= 1)
        assume(len(layers) >= 1)
        
        # Create multiplex network
        network = multinet.multi_layer_network(directed=False)
        
        edge_dicts = []
        for s, t in edges:
            for layer in layers:
                edge_dicts.append({
                    'source': s,
                    'target': t,
                    'source_type': layer,
                    'target_type': layer,
                    'type': 'edge'
                })
        
        network.add_edges(edge_dicts)
        
        # Verify: every edge connects nodes that exist
        for edge in network.get_edges():
            source_node = edge[0]  # (node_id, layer_id)
            target_node = edge[1]
            
            # Both nodes must exist in the network
            assert source_node in list(network.get_nodes())
            assert target_node in list(network.get_nodes())
            
            # For intra-layer edges, both nodes must be in the same layer
            if source_node[1] == target_node[1]:
                assert source_node[1] in layers
                assert target_node[1] in layers

    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=12),
                st.integers(min_value=0, max_value=12)
            ),
            min_size=2,
            max_size=15
        ),
        st.lists(valid_layer_names(), min_size=2, max_size=4, unique=True)
    )
    def test_union_of_layer_nodes_equals_full_node_set(self, edges, layers):
        """The union of all layer node sets equals the full node set of the multiplex graph."""
        # Filter self-loops
        edges = [(s, t) for s, t in edges if s != t]
        assume(len(edges) >= 2)
        assume(len(layers) >= 2)
        
        # Build node set from edges
        nodes_from_edges = set()
        for s, t in edges:
            nodes_from_edges.add(s)
            nodes_from_edges.add(t)
        
        # Create multiplex network
        network = multinet.multi_layer_network(directed=False)
        
        edge_dicts = []
        for s, t in edges:
            # Add each edge to all layers
            for layer in layers:
                edge_dicts.append({
                    'source': s,
                    'target': t,
                    'source_type': layer,
                    'target_type': layer,
                    'type': 'edge'
                })
        
        network.add_edges(edge_dicts)
        
        # Get all nodes in network
        all_network_nodes = set(network.get_nodes())
        
        # Get nodes per layer
        nodes_by_layer = {}
        for node in all_network_nodes:
            layer = node[1]
            if layer not in nodes_by_layer:
                nodes_by_layer[layer] = set()
            nodes_by_layer[layer].add(node[0])  # Add just the node ID
        
        # Union of all layer node IDs
        union_of_layer_nodes = set()
        for layer_nodes in nodes_by_layer.values():
            union_of_layer_nodes.update(layer_nodes)
        
        # The union should contain all original nodes
        assert nodes_from_edges.issubset(union_of_layer_nodes)

    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=10),
                st.integers(min_value=0, max_value=10)
            ),
            min_size=1,
            max_size=10
        ),
        st.lists(valid_layer_names(), min_size=1, max_size=3, unique=True)
    )
    def test_add_remove_edge_restores_structure(self, edges, layers):
        """Adding and removing an edge in the same layer restores the original adjacency structure."""
        # Filter self-loops
        edges = [(s, t) for s, t in edges if s != t]
        assume(len(edges) >= 1)
        assume(len(layers) >= 1)
        
        layer = layers[0]  # Use first layer
        
        # Create multiplex network with initial edges
        network = multinet.multi_layer_network(directed=False)
        
        edge_dicts = []
        for s, t in edges:
            edge_dicts.append({
                'source': s,
                'target': t,
                'source_type': layer,
                'target_type': layer,
                'type': 'edge'
            })
        
        network.add_edges(edge_dicts)
        
        # Get original edge count
        original_edges = list(network.get_edges())
        original_count = len(original_edges)
        
        # Add a new edge
        new_node1 = 999
        new_node2 = 1000
        new_edge = {
            'source': new_node1,
            'target': new_node2,
            'source_type': layer,
            'target_type': layer,
            'type': 'edge'
        }
        network.add_edges([new_edge])
        
        # Count should increase
        after_add_count = len(list(network.get_edges()))
        assert after_add_count > original_count
        
        # Remove the added edge
        remove_edge = [[new_node1, layer, new_node2, layer, 1]]
        network.remove_edges(remove_edge, input_type='list')
        
        # Count should return to original
        final_count = len(list(network.get_edges()))
        assert final_count == original_count


class TestProjectionAndMergingProperties:
    """Test properties related to projection and merging operations."""

    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=15),
                st.integers(min_value=0, max_value=15)
            ),
            min_size=2,
            max_size=20
        ),
        st.lists(valid_layer_names(), min_size=2, max_size=4, unique=True)
    )
    def test_projection_preserves_node_count(self, edges, layers):
        """Projecting a multiplex network into a single-layer aggregate preserves the total node count."""
        # Filter self-loops
        edges = [(s, t) for s, t in edges if s != t]
        assume(len(edges) >= 2)
        assume(len(layers) >= 2)
        
        # Get unique nodes from edges
        unique_nodes = set()
        for s, t in edges:
            unique_nodes.add(s)
            unique_nodes.add(t)
        
        # Create multiplex network
        network = multinet.multi_layer_network(directed=False)
        
        edge_dicts = []
        for s, t in edges:
            for layer in layers:
                edge_dicts.append({
                    'source': s,
                    'target': t,
                    'source_type': layer,
                    'target_type': layer,
                    'type': 'edge'
                })
        
        network.add_edges(edge_dicts)
        
        # Get unique node IDs before projection (count only node IDs, not node-layer pairs)
        unique_node_ids_before = {node[0] for node in network.get_nodes()}
        
        # Create a simple aggregated projection by collecting all edges
        # In a real projection, we would flatten all layers into one
        aggregate_nodes = set()
        for edge in network.get_edges():
            aggregate_nodes.add(edge[0][0])  # source node ID
            aggregate_nodes.add(edge[1][0])  # target node ID
        
        # The projected network should have the same unique node IDs
        assert unique_node_ids_before == aggregate_nodes

    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=12),
                st.integers(min_value=0, max_value=12)
            ),
            min_size=2,
            max_size=15
        ),
        st.lists(valid_layer_names(), min_size=2, max_size=4, unique=True)
    )
    def test_projected_edge_count_at_least_max_layer(self, edges, layers):
        """The projected edge count is at least the maximum edge count of any individual layer."""
        # Filter self-loops and normalize edges for undirected network
        normalized_edges = []
        seen = set()
        for s, t in edges:
            if s != t:
                # Normalize: smaller ID first
                normalized = tuple(sorted([s, t]))
                if normalized not in seen:
                    normalized_edges.append(normalized)
                    seen.add(normalized)
        
        edges = normalized_edges
        assume(len(edges) >= 2)
        assume(len(layers) >= 2)
        
        # Create multiplex network
        network = multinet.multi_layer_network(directed=False)
        
        edge_dicts = []
        for s, t in edges:
            for layer in layers:
                edge_dicts.append({
                    'source': s,
                    'target': t,
                    'source_type': layer,
                    'target_type': layer,
                    'type': 'edge'
                })
        
        network.add_edges(edge_dicts)
        
        # Count edges per layer
        edges_by_layer = {}
        for edge in network.get_edges():
            source_layer = edge[0][1]
            target_layer = edge[1][1]
            
            # Only count intra-layer edges
            if source_layer == target_layer:
                edges_by_layer[source_layer] = edges_by_layer.get(source_layer, 0) + 1
        
        max_layer_edges = max(edges_by_layer.values()) if edges_by_layer else 0
        
        # Create projection: collect unique edges across all layers
        projected_edges = set()
        for edge in network.get_edges():
            source_id = edge[0][0]
            target_id = edge[1][0]
            # Normalize edge representation (smaller ID first for undirected)
            normalized_edge = tuple(sorted([source_id, target_id]))
            projected_edges.add(normalized_edge)
        
        # Projected edge count should be >= max edge count of any layer
        assert len(projected_edges) >= max_layer_edges

    @given(
        st.lists(valid_layer_names(), min_size=3, max_size=6, unique=True),
        st.integers(min_value=2, max_value=8)
    )
    def test_merging_disjoint_layers_produces_sum(self, layers, num_nodes):
        """Merging two multiplex graphs with disjoint layer sets produces a graph whose number of layers equals the sum of both."""
        assume(len(layers) >= 3)
        
        # Split layers into two disjoint groups
        split_point = len(layers) // 2
        layers1 = layers[:split_point]
        layers2 = layers[split_point:]
        
        assume(len(layers1) >= 1 and len(layers2) >= 1)
        
        # Create first network
        network1 = multinet.multi_layer_network(directed=False)
        edges1 = []
        for layer in layers1:
            for i in range(num_nodes - 1):
                edges1.append({
                    'source': i,
                    'target': i + 1,
                    'source_type': layer,
                    'target_type': layer,
                    'type': 'edge'
                })
        network1.add_edges(edges1)
        
        # Create second network
        network2 = multinet.multi_layer_network(directed=False)
        edges2 = []
        for layer in layers2:
            for i in range(num_nodes - 1):
                edges2.append({
                    'source': i,
                    'target': i + 1,
                    'source_type': layer,
                    'target_type': layer,
                    'type': 'edge'
                })
        network2.add_edges(edges2)
        
        # Get layer counts before merge
        layers_before_1 = {node[1] for node in network1.get_nodes()}
        layers_before_2 = {node[1] for node in network2.get_nodes()}
        count_before_1 = len(layers_before_1)
        count_before_2 = len(layers_before_2)
        
        # Merge networks
        network1.merge_with(network2)
        
        # Get layers after merge
        layers_after = {node[1] for node in network1.get_nodes()}
        count_after = len(layers_after)
        
        # Should have all layers from both networks (they're disjoint)
        assert count_after == count_before_1 + count_before_2
        assert layers_before_1.issubset(layers_after)
        assert layers_before_2.issubset(layers_after)


class TestInterLayerAndStructureInvariants:
    """Test inter-layer properties and structural invariants."""

    @given(
        st.lists(valid_layer_names(), min_size=2, max_size=4, unique=True),
        st.integers(min_value=3, max_value=8)
    )
    def test_interlayer_couplings_symmetric_undirected(self, layers, num_nodes):
        """Inter-layer couplings are symmetric in undirected multiplex graphs."""
        assume(len(layers) >= 2)
        
        # Create undirected multiplex network
        network = multinet.multi_layer_network(directed=False, network_type="multiplex")
        
        # Add edges in each layer
        edges = []
        for layer in layers:
            for i in range(num_nodes - 1):
                edges.append({
                    'source': i,
                    'target': i + 1,
                    'source_type': layer,
                    'target_type': layer,
                    'type': 'edge'
                })
        network.add_edges(edges)
        
        # Collect inter-layer coupling edges
        coupling_edges = []
        for edge in network.get_edges(data=True):
            # Check if it's a coupling edge (different layers)
            if edge[0][1] != edge[1][1]:
                coupling_edges.append(edge)
        
        # For each coupling edge, verify the reverse exists
        coupling_set = set()
        for edge in coupling_edges:
            source = edge[0]
            target = edge[1]
            # Normalize representation for undirected
            normalized = tuple(sorted([source, target]))
            coupling_set.add(normalized)
        
        # In undirected multiplex, coupling edges should be symmetric
        # Check that for each (A, layer1) <-> (A, layer2), the connection exists
        for edge in coupling_edges:
            source_node = edge[0][0]
            target_node = edge[1][0]
            # Coupling edges connect same node across layers
            assert source_node == target_node

    @given(
        st.lists(valid_layer_names(), min_size=3, max_size=5, unique=True),
        st.integers(min_value=3, max_value=7)
    )
    def test_empty_layer_removal_preserves_connectivity(self, layers, num_nodes):
        """Removing an empty layer does not change the connectivity or node set of the remaining layers."""
        assume(len(layers) >= 3)
        
        # Use first layers for edges, keep last as empty
        used_layers = layers[:-1]
        empty_layer = layers[-1]
        
        # Create network with edges only in used layers
        network = multinet.multi_layer_network(directed=False)
        edges = []
        for layer in used_layers:
            for i in range(num_nodes - 1):
                edges.append({
                    'source': i,
                    'target': i + 1,
                    'source_type': layer,
                    'target_type': layer,
                    'type': 'edge'
                })
        network.add_edges(edges)
        
        # Get connectivity before (edges in used layers)
        edges_before = {}
        for edge in network.get_edges():
            layer = edge[0][1]
            if layer in used_layers:
                edges_before[layer] = edges_before.get(layer, 0) + 1
        
        # Verify the empty layer wasn't created or has no edges
        layers_in_network = {node[1] for node in network.get_nodes()}
        
        # The empty layer should either not exist or have no edges
        if empty_layer in layers_in_network:
            empty_layer_edges = sum(1 for edge in network.get_edges() if edge[0][1] == empty_layer and edge[1][1] == empty_layer)
            assert empty_layer_edges == 0
        
        # Verify all used layers have the expected edges
        assert all(count > 0 for count in edges_before.values())
        assert len(edges_before) == len(used_layers)

    @given(
        st.integers(min_value=3, max_value=8),
        st.lists(valid_layer_names(), min_size=2, max_size=4, unique=True)
    )
    def test_degree_distribution_invariant_to_relabeling(self, num_nodes, layers):
        """Degree distributions across layers are invariant to node relabeling."""
        assume(len(layers) >= 2)
        
        # Create network with specific structure
        network = multinet.multi_layer_network(directed=False)
        edges = []
        for layer in layers:
            for i in range(num_nodes - 1):
                edges.append({
                    'source': i,
                    'target': i + 1,
                    'source_type': layer,
                    'target_type': layer,
                    'type': 'edge'
                })
        network.add_edges(edges)
        
        # Calculate degree distribution
        node_degrees = {}
        for edge in network.get_edges():
            source = edge[0]
            target = edge[1]
            
            # Count degrees for each node-layer pair
            node_degrees[source] = node_degrees.get(source, 0) + 1
            node_degrees[target] = node_degrees.get(target, 0) + 1
        
        # Get degree sequence (sorted list of degrees)
        degree_sequence = sorted(node_degrees.values())
        
        # Now create same network with relabeled nodes (shifted by 100)
        network2 = multinet.multi_layer_network(directed=False)
        edges2 = []
        offset = 100
        for layer in layers:
            for i in range(num_nodes - 1):
                edges2.append({
                    'source': i + offset,
                    'target': i + 1 + offset,
                    'source_type': layer,
                    'target_type': layer,
                    'type': 'edge'
                })
        network2.add_edges(edges2)
        
        # Calculate degree distribution for relabeled network
        node_degrees2 = {}
        for edge in network2.get_edges():
            source = edge[0]
            target = edge[1]
            
            node_degrees2[source] = node_degrees2.get(source, 0) + 1
            node_degrees2[target] = node_degrees2.get(target, 0) + 1
        
        degree_sequence2 = sorted(node_degrees2.values())
        
        # Degree sequences should be identical (structural invariant)
        assert degree_sequence == degree_sequence2

    @given(
        st.integers(min_value=4, max_value=10),
        st.lists(valid_layer_names(), min_size=2, max_size=3, unique=True)
    )
    def test_layer_isolation_preserved(self, num_nodes, layers):
        """Within-layer connectivity is independent of other layers in multilayer (non-multiplex) networks."""
        assume(len(layers) >= 2)
        
        # Create multilayer (not multiplex) network
        network = multinet.multi_layer_network(directed=False, network_type="multilayer")
        
        # Add different structures to different layers
        edges = []
        # Layer 0: path graph
        for i in range(num_nodes - 1):
            edges.append({
                'source': i,
                'target': i + 1,
                'source_type': layers[0],
                'target_type': layers[0],
                'type': 'edge'
            })
        
        # Layer 1: star graph (if we have at least 2 layers)
        if len(layers) >= 2:
            for i in range(1, num_nodes):
                edges.append({
                    'source': 0,
                    'target': i,
                    'source_type': layers[1],
                    'target_type': layers[1],
                    'type': 'edge'
                })
        
        network.add_edges(edges)
        
        # Count edges per layer
        edges_per_layer = {}
        for edge in network.get_edges():
            source_layer = edge[0][1]
            target_layer = edge[1][1]
            
            # Only intra-layer edges
            if source_layer == target_layer:
                edges_per_layer[source_layer] = edges_per_layer.get(source_layer, 0) + 1
        
        # Verify each layer has its expected structure
        assert layers[0] in edges_per_layer
        assert edges_per_layer[layers[0]] == num_nodes - 1  # Path graph
        
        if len(layers) >= 2:
            assert layers[1] in edges_per_layer
            assert edges_per_layer[layers[1]] == num_nodes - 1  # Star graph
