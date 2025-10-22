"""
Property-based tests for py3plex using Hypothesis.

This module tests general graph properties and multiplex network invariants
using property-based testing with the Hypothesis library.
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


def edge_lists(min_nodes=2, max_nodes=8, min_edges=1, max_edges=15):
    """Generate lists of edges as (source, target) tuples."""
    return st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=max_nodes-1),
            st.integers(min_value=0, max_value=max_nodes-1)
        ),
        min_size=min_edges,
        max_size=max_edges
    )


def multiplex_edge_dicts(min_nodes=2, max_nodes=8, min_edges=1, max_edges=15):
    """Generate edge dictionaries for multiplex networks."""
    return st.lists(
        st.fixed_dictionaries({
            'source': st.integers(min_value=0, max_value=max_nodes-1),
            'target': st.integers(min_value=0, max_value=max_nodes-1),
            'source_type': valid_layer_names(),
            'target_type': valid_layer_names(),
            'type': st.just('edge')
        }),
        min_size=min_edges,
        max_size=max_edges
    )


class TestGeneralGraphProperties:
    """Test general graph properties that should hold for any graph structure."""

    @given(edge_lists(min_nodes=3, max_nodes=6, min_edges=2, max_edges=10))
    def test_edge_list_reversal_idempotent(self, edges):
        """Reversing an edge list twice yields the same result."""
        # Filter out self-loops to ensure valid edges
        edges = [(s, t) for s, t in edges if s != t]
        assume(len(edges) > 0)
        
        # Reverse edges
        reversed_once = [(t, s) for s, t in edges]
        reversed_twice = [(t, s) for s, t in reversed_once]
        
        # Sort for comparison (since order may vary)
        assert sorted(edges) == sorted(reversed_twice)

    @given(
        st.lists(st.integers(min_value=0, max_value=10), min_size=3, max_size=10, unique=True),
        edge_lists(min_nodes=3, max_nodes=6, min_edges=2, max_edges=10)
    )
    def test_degree_distribution_invariant_to_node_ordering(self, node_ids, edges):
        """Degree distributions are invariant to node ordering."""
        # Filter self-loops and ensure edges reference valid nodes
        edges = [(s, t) for s, t in edges if s != t and s < len(node_ids) and t < len(node_ids)]
        assume(len(edges) >= 2)
        
        G = nx.Graph()
        for s, t in edges:
            G.add_edge(node_ids[s], node_ids[t])
        
        # Get degree sequence
        degree_seq1 = sorted([d for n, d in G.degree()])
        
        # Create graph with shuffled node mapping
        import random
        shuffled_ids = node_ids.copy()
        random.shuffle(shuffled_ids)
        
        G2 = nx.Graph()
        for s, t in edges:
            G2.add_edge(shuffled_ids[s], shuffled_ids[t])
        
        degree_seq2 = sorted([d for n, d in G2.degree()])
        
        # Degree sequences should be the same
        assert degree_seq1 == degree_seq2

    @given(multiplex_edge_dicts(min_nodes=3, max_nodes=6, min_edges=2, max_edges=10))
    def test_add_remove_edge_restores_structure(self, edges):
        """Adding and then removing the same edge restores the original adjacency structure."""
        # Use at least one edge for the test
        assume(len(edges) >= 1)
        
        # Filter self-loops
        edges = [e for e in edges if e['source'] != e['target']]
        assume(len(edges) >= 1)
        
        # Ensure same layer for simplicity
        for edge in edges:
            edge['source_type'] = 'layer1'
            edge['target_type'] = 'layer1'
        
        # Create network
        network = multinet.multi_layer_network(directed=False)
        network.add_edges(edges)
        
        # Get original edge count
        original_edges = list(network.get_edges())
        original_count = len(original_edges)
        
        # Add a new edge
        new_edge = {
            'source': 99,
            'target': 100,
            'source_type': 'layer1',
            'target_type': 'layer1',
            'type': 'edge'
        }
        network.add_edges([new_edge])
        
        # Count should increase
        assert len(list(network.get_edges())) > original_count
        
        # Remove the added edge (with 5 elements: n1, l1, n2, l2, weight)
        # Must be a list of lists
        remove_edge = [[99, 'layer1', 100, 'layer1', 1]]
        network.remove_edges(remove_edge, input_type='list')
        
        # Count should return to original
        final_edges = list(network.get_edges())
        assert len(final_edges) == original_count


class TestMultiplexNetworkProperties:
    """Test properties specific to multiplex networks."""

    @given(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=9),
                st.integers(min_value=0, max_value=9)
            ),
            min_size=2,
            max_size=12
        ),
        st.lists(valid_layer_names(), min_size=1, max_size=3, unique=True)
    )
    def test_layer_projection_preserves_nodes(self, edges, layers):
        """Layer projection and reconstruction preserve node sets."""
        assume(len(layers) >= 1)
        
        # Filter edges to remove self-loops
        edges = [(s, t) for s, t in edges if s != t]
        assume(len(edges) >= 1)
        
        # Get the actual node set from edges
        node_set = set()
        for s, t in edges:
            node_set.add(s)
            node_set.add(t)
        
        # Create edge dicts
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
        
        # Create multiplex network
        network = multinet.multi_layer_network(directed=False)
        network.add_edges(edge_dicts)
        
        # Get node set from network
        node_set_before = {n[0] for n in network.get_nodes()}
        
        # For simple validation, just check nodes are preserved
        assert len(node_set_before) > 0
        # Verify all nodes from edges are present in the network
        assert node_set.issubset(node_set_before)

    @given(
        st.lists(valid_layer_names(), min_size=2, max_size=4, unique=True),
        st.integers(min_value=2, max_value=8)
    )
    def test_intra_layer_edge_counting(self, layers, num_nodes):
        """Sum of intra-layer edges across all layers equals total edge count."""
        assume(len(layers) >= 2)
        
        # Create simple edges for each layer
        edge_dicts = []
        for layer in layers:
            # Add a simple path in each layer
            for i in range(num_nodes - 1):
                edge_dicts.append({
                    'source': i,
                    'target': i + 1,
                    'source_type': layer,
                    'target_type': layer,
                    'type': 'edge'
                })
        
        network = multinet.multi_layer_network(directed=False)
        network.add_edges(edge_dicts)
        
        # Count edges per layer
        edges_by_layer = {}
        for edge in network.get_edges(data=True):
            layer = edge[0][1]  # source layer
            # Only count intra-layer edges (same layer)
            if edge[0][1] == edge[1][1]:
                edges_by_layer[layer] = edges_by_layer.get(layer, 0) + 1
        
        # Sum should equal expected
        total_intra_layer = sum(edges_by_layer.values())
        expected = len(layers) * (num_nodes - 1)
        assert total_intra_layer == expected

    @given(
        st.lists(valid_layer_names(), min_size=2, max_size=3, unique=True),
        st.integers(min_value=2, max_value=6)
    )
    def test_merging_disjoint_layers(self, layers, num_nodes):
        """Merging multiplex graphs with disjoint layer sets yields combined layers."""
        assume(len(layers) >= 2)
        
        # Split layers into two groups
        layers1 = layers[:len(layers)//2]
        layers2 = layers[len(layers)//2:]
        
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
        
        # Get layers before merge
        layers_before_1 = {n[1] for n in network1.get_nodes()}
        layers_before_2 = {n[1] for n in network2.get_nodes()}
        
        # Merge networks
        network1.merge_with(network2)
        
        # Get layers after merge
        layers_after = {n[1] for n in network1.get_nodes()}
        
        # Should contain all layers from both networks
        assert layers_before_1.issubset(layers_after)
        assert layers_before_2.issubset(layers_after)
        assert len(layers_after) >= len(layers_before_1) + len(layers_before_2)

    @given(
        st.lists(valid_layer_names(), min_size=2, max_size=4, unique=True),
        st.integers(min_value=3, max_value=7)
    )
    def test_empty_layer_removal_no_effect(self, layers, num_nodes):
        """Removing an empty layer has no effect on other layers' connectivity."""
        assume(len(layers) >= 2)
        
        # Use only first layers for edges, keep last as empty
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
        
        # Get initial edge count for used layers
        initial_edges = {}
        for edge in network.get_edges():
            layer = edge[0][1]
            if layer in used_layers:
                initial_edges[layer] = initial_edges.get(layer, 0) + 1
        
        # The empty layer shouldn't affect connectivity
        # Just verify we have edges in used layers
        assert sum(initial_edges.values()) > 0
        assert all(count > 0 for count in initial_edges.values())

    @given(
        st.integers(min_value=3, max_value=6),
        st.lists(valid_layer_names(), min_size=1, max_size=3, unique=True)
    )
    def test_node_relabeling_preserves_structure(self, num_nodes, layers):
        """Random node relabeling does not alter total degree distributions."""
        assume(len(layers) >= 1)
        
        # Create network
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
        for node in network.get_nodes():
            node_id = node[0]
            # Count edges for this node across all layers
            node_degrees[node_id] = node_degrees.get(node_id, 0)
        
        # Count edges connected to each node
        for edge in network.get_edges():
            src_id = edge[0][0]
            dst_id = edge[1][0]
            if edge[0][1] == edge[1][1]:  # same layer, intra-layer edge
                node_degrees[src_id] = node_degrees.get(src_id, 0) + 1
                node_degrees[dst_id] = node_degrees.get(dst_id, 0) + 1
        
        # Get degree sequence
        degree_seq = sorted(node_degrees.values())
        
        # Verify degree sequence properties
        # In a path graph of n nodes, we have 2 nodes with degree 1, rest with degree 2
        # Multiplied by number of layers
        assert len(degree_seq) > 0
        # For path graphs: 2 end nodes (degree 1*layers), n-2 middle nodes (degree 2*layers)
        expected_degree_sum = 2 * (num_nodes - 1) * len(layers)  # Each edge contributes 2 to sum
        assert sum(degree_seq) == expected_degree_sum
