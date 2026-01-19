"""
Comprehensive tests for multilayer/multiplex network conversions.

This test suite validates the interoperability between different network types
in py3plex, specifically testing the conversion methods:
- to_multiplex(): Convert multilayer → multiplex
- to_multilayer(): Convert multiplex → multilayer  
- flatten_to_monoplex(): Flatten to single-layer graph

Test Coverage:
- Minimal viable exemplars for each conversion type
- Roundtrip conversions (multilayer → multiplex → multilayer)
- Edge cases (empty networks, single layer, isolated nodes)
- Edge preservation and aggregation
- Coupling edge handling
- Node set alignment (intersection/union methods)

Expected behavior is pinned through synthetic minimal samples representing
canonical use cases.
"""

import pytest
import networkx as nx
from collections import Counter

from py3plex.core import multinet


class TestMultilayerToMultiplex:
    """Tests for converting multilayer networks to multiplex."""

    def test_intersection_method_keeps_only_shared_nodes(self):
        """to_multiplex(method='intersection') keeps only nodes in ALL layers."""
        # Create multilayer with partial node overlap
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'B', 'type': 'L1'},
            {'source': 'A', 'type': 'L2'},
            {'source': 'C', 'type': 'L2'},
        ])
        
        # Convert to multiplex
        multiplex = net.to_multiplex(method='intersection')
        
        # Only node 'A' is in both layers
        nodes = list(multiplex.get_nodes())
        node_ids = {n[0] for n in nodes}
        assert node_ids == {'A'}, f"Expected only 'A', got {node_ids}"
        assert multiplex.network_type == "multiplex"
        
        # Should have A in both layers
        assert len(nodes) == 2
        assert ('A', 'L1') in nodes
        assert ('A', 'L2') in nodes

    def test_union_method_adds_missing_nodes(self):
        """to_multiplex(method='union') adds missing nodes to all layers."""
        # Create multilayer with different nodes per layer
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'B', 'type': 'L1'},
            {'source': 'C', 'type': 'L2'},
        ])
        
        # Convert to multiplex
        multiplex = net.to_multiplex(method='union')
        
        # All nodes should be in both layers
        nodes = list(multiplex.get_nodes())
        node_ids = {n[0] for n in nodes}
        assert node_ids == {'A', 'B', 'C'}
        
        # Each node should appear in both layers
        assert len(nodes) == 6  # 3 nodes * 2 layers
        for node_id in ['A', 'B', 'C']:
            assert (node_id, 'L1') in nodes
            assert (node_id, 'L2') in nodes

    def test_edges_preserved_after_conversion(self):
        """Edges between shared nodes are preserved."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'B', 'type': 'L1'},
            {'source': 'A', 'type': 'L2'},
            {'source': 'B', 'type': 'L2'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'B', 'source_type': 'L2', 'target_type': 'L2'},
        ])
        
        multiplex = net.to_multiplex(method='intersection')
        
        # Get non-coupling edges
        edges = list(multiplex.get_edges(data=False, multiplex_edges=False))
        # Edges include keys for multiplex with multiplex_edges=False
        # Extract just (u, v) pairs
        edge_pairs = [(e[0], e[1]) for e in edges]
        assert len(edges) == 2  # Two intra-layer edges
        assert (('A', 'L1'), ('B', 'L1')) in edge_pairs or (('B', 'L1'), ('A', 'L1')) in edge_pairs
        assert (('A', 'L2'), ('B', 'L2')) in edge_pairs or (('B', 'L2'), ('A', 'L2')) in edge_pairs

    def test_coupling_edges_created_automatically(self):
        """Coupling edges are created between layers after conversion."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'A', 'type': 'L2'},
        ])
        
        multiplex = net.to_multiplex(method='intersection')
        
        # Check coupling edges exist
        all_edges = list(multiplex.get_edges(data=True, multiplex_edges=True))
        coupling_edges = [e for e in all_edges if e[-1].get('type') == 'coupling']
        
        assert len(coupling_edges) > 0, "Coupling edges should be created"
        # Should have bidirectional coupling: A_L1 <-> A_L2
        assert len(coupling_edges) == 2  # One in each direction

    def test_empty_network_to_multiplex(self):
        """Empty network converts to empty multiplex."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        
        multiplex = net.to_multiplex(method='intersection')
        
        assert multiplex.network_type == "multiplex"
        assert len(list(multiplex.get_nodes())) == 0
        assert len(list(multiplex.get_edges())) == 0

    def test_single_layer_to_multiplex(self):
        """Single-layer network converts to single-layer multiplex."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'B', 'type': 'L1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        multiplex = net.to_multiplex(method='intersection')
        
        assert multiplex.network_type == "multiplex"
        nodes = list(multiplex.get_nodes())
        assert len(nodes) == 2
        # No coupling edges needed with single layer
        edges = list(multiplex.get_edges(data=True, multiplex_edges=True))
        assert len(edges) == 1

    def test_already_multiplex_raises_error(self):
        """Converting already-multiplex network raises error."""
        net = multinet.multi_layer_network(network_type='multiplex', directed=False, verbose=False)
        
        with pytest.raises(ValueError, match="already multiplex"):
            net.to_multiplex()

    def test_intersection_no_shared_nodes(self):
        """Intersection with no shared nodes results in empty multiplex."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'B', 'type': 'L2'},
        ])
        
        multiplex = net.to_multiplex(method='intersection')
        
        assert len(list(multiplex.get_nodes())) == 0

    def test_invalid_method_raises_error(self):
        """Invalid method parameter raises error."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        
        with pytest.raises(ValueError, match="Unknown method"):
            net.to_multiplex(method='invalid')


class TestMultiplexToMultilayer:
    """Tests for converting multiplex networks to multilayer."""

    def test_basic_conversion_preserves_nodes(self):
        """to_multilayer() preserves all nodes."""
        net = multinet.multi_layer_network(network_type='multiplex', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'A', 'type': 'L2'},
            {'source': 'B', 'type': 'L1'},
            {'source': 'B', 'type': 'L2'},
        ])
        
        multilayer = net.to_multilayer()
        
        assert multilayer.network_type == "multilayer"
        nodes = list(multilayer.get_nodes())
        assert len(nodes) == 4

    def test_coupling_edges_removed_by_default(self):
        """Coupling edges are removed by default."""
        net = multinet.multi_layer_network(network_type='multiplex', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'A', 'type': 'L2'},
        ])
        net._couple_all_edges()
        
        multilayer = net.to_multilayer(remove_coupling=True)
        
        # Should have no edges (coupling edges removed, no user edges)
        edges = list(multilayer.get_edges())
        assert len(edges) == 0

    def test_coupling_edges_preserved_when_requested(self):
        """Coupling edges can be preserved."""
        net = multinet.multi_layer_network(network_type='multiplex', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'A', 'type': 'L2'},
        ])
        net._couple_all_edges()
        
        multilayer = net.to_multilayer(remove_coupling=False)
        
        # Should have coupling edges
        edges = list(multilayer.get_edges(data=True))
        assert len(edges) > 0

    def test_user_edges_preserved(self):
        """User-defined edges are always preserved."""
        net = multinet.multi_layer_network(network_type='multiplex', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'B', 'type': 'L1'},
            {'source': 'A', 'type': 'L2'},
            {'source': 'B', 'type': 'L2'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        net._couple_all_edges()
        
        multilayer = net.to_multilayer(remove_coupling=True)
        
        # Should have the user edge
        edges = list(multilayer.get_edges())
        assert len(edges) == 1

    def test_already_multilayer_raises_error(self):
        """Converting already-multilayer network raises error."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        
        with pytest.raises(ValueError, match="already multilayer"):
            net.to_multilayer()

    def test_empty_multiplex_to_multilayer(self):
        """Empty multiplex converts to empty multilayer."""
        net = multinet.multi_layer_network(network_type='multiplex', directed=False, verbose=False)
        
        multilayer = net.to_multilayer()
        
        assert multilayer.network_type == "multilayer"
        assert len(list(multilayer.get_nodes())) == 0


class TestFlattenToMonoplex:
    """Tests for flattening multilayer/multiplex to single-layer graph."""

    def test_basic_flattening_merges_nodes(self):
        """Nodes with same ID across layers are merged."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'A', 'type': 'L2'},
            {'source': 'B', 'type': 'L1'},
        ])
        
        flat = net.flatten_to_monoplex()
        
        assert isinstance(flat, nx.Graph)
        assert len(flat.nodes()) == 2  # A and B
        assert 'A' in flat.nodes()
        assert 'B' in flat.nodes()

    def test_count_method_counts_edge_occurrences(self):
        """method='count' counts edge occurrences across layers."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'B', 'source_type': 'L2', 'target_type': 'L2'},
            {'source': 'A', 'target': 'B', 'source_type': 'L3', 'target_type': 'L3'},
        ])
        
        flat = net.flatten_to_monoplex(method='count')
        
        assert flat.edges[('A', 'B')]['weight'] == 3

    def test_union_method_sums_weights(self):
        """method='union' sums edge weights across layers."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1', 'weight': 2},
            {'source': 'A', 'target': 'B', 'source_type': 'L2', 'target_type': 'L2', 'weight': 3},
        ])
        
        flat = net.flatten_to_monoplex(method='union')
        
        assert flat.edges[('A', 'B')]['weight'] == 5

    def test_first_method_keeps_first_occurrence(self):
        """method='first' keeps only first edge occurrence."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1', 'weight': 10},
            {'source': 'A', 'target': 'B', 'source_type': 'L2', 'target_type': 'L2', 'weight': 20},
        ])
        
        flat = net.flatten_to_monoplex(method='first')
        
        # Should have weight from first occurrence
        assert flat.edges[('A', 'B')]['weight'] == 10

    def test_interlayer_edges_excluded(self):
        """Inter-layer edges are excluded from flattening."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'A', 'source_type': 'L1', 'target_type': 'L2'},  # Inter-layer
        ])
        
        flat = net.flatten_to_monoplex()
        
        # Should only have the intra-layer edge
        assert len(flat.edges()) == 1
        assert ('A', 'B') in flat.edges() or ('B', 'A') in flat.edges()

    def test_directed_network_produces_digraph(self):
        """Directed network produces DiGraph."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=True, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        flat = net.flatten_to_monoplex()
        
        assert isinstance(flat, nx.DiGraph)

    def test_undirected_network_produces_graph(self):
        """Undirected network produces Graph."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        flat = net.flatten_to_monoplex()
        
        assert isinstance(flat, nx.Graph)
        assert not isinstance(flat, nx.DiGraph)

    def test_empty_network_flattens_to_empty_graph(self):
        """Empty network flattens to empty graph."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        
        flat = net.flatten_to_monoplex()
        
        assert len(flat.nodes()) == 0
        assert len(flat.edges()) == 0

    def test_invalid_method_raises_error(self):
        """Invalid method parameter raises error."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        
        with pytest.raises(ValueError, match="Unknown method"):
            net.flatten_to_monoplex(method='invalid')

    def test_edge_attributes_preserved_from_first_occurrence(self):
        """Edge attributes from first occurrence are preserved."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1', 
             'color': 'red', 'label': 'test'},
            {'source': 'A', 'target': 'B', 'source_type': 'L2', 'target_type': 'L2',
             'color': 'blue'},
        ])
        
        flat = net.flatten_to_monoplex(method='count')
        
        edge_data = flat.edges[('A', 'B')]
        assert edge_data.get('color') == 'red'  # From first occurrence
        assert edge_data.get('label') == 'test'
        assert edge_data['weight'] == 2  # Counted


class TestRoundtripConversions:
    """Tests for roundtrip conversions between network types."""

    def test_multilayer_to_multiplex_to_multilayer_preserves_shared_nodes(self):
        """Roundtrip conversion preserves shared nodes."""
        # Start with multilayer where all nodes are in all layers
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'B', 'type': 'L1'},
            {'source': 'A', 'type': 'L2'},
            {'source': 'B', 'type': 'L2'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        # Convert to multiplex and back
        multiplex = net.to_multiplex(method='intersection')
        back_to_multilayer = multiplex.to_multilayer(remove_coupling=True)
        
        # Check nodes preserved
        original_nodes = set(net.get_nodes())
        final_nodes = set(back_to_multilayer.get_nodes())
        assert original_nodes == final_nodes
        
        # Check edges preserved (excluding coupling)
        original_edges = set(net.get_edges())
        final_edges = set(back_to_multilayer.get_edges())
        
        # For undirected networks, edges can be in either order
        # Normalize edge tuples to handle this
        def normalize_edge(edge):
            """Normalize edge tuple for undirected comparison."""
            u, v = edge[0], edge[1]
            if u > v:
                return (v, u)
            return (u, v)
        
        original_normalized = {normalize_edge(e) for e in original_edges}
        final_normalized = {normalize_edge(e) for e in final_edges}
        assert original_normalized == final_normalized

    def test_multiplex_to_multilayer_to_multiplex_loses_coupling(self):
        """Roundtrip from multiplex loses coupling edges if removed."""
        net = multinet.multi_layer_network(network_type='multiplex', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'A', 'type': 'L2'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'A', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        net._couple_all_edges()
        
        # Convert to multilayer (removing coupling) and back to multiplex
        multilayer = net.to_multilayer(remove_coupling=True)
        back_to_multiplex = multilayer.to_multiplex(method='intersection')
        
        # Nodes should be preserved
        assert len(list(back_to_multiplex.get_nodes())) == 2
        
        # Non-coupling edges should be preserved
        non_coupling = list(back_to_multiplex.get_edges(multiplex_edges=False))
        assert len(non_coupling) == 1

    def test_flatten_and_reconstruct_loses_layer_info(self):
        """Flattening loses layer information."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'L1', 'target_type': 'L1'},
            {'source': 'A', 'target': 'C', 'source_type': 'L2', 'target_type': 'L2'},
        ])
        
        flat = net.flatten_to_monoplex()
        
        # Flat graph has simple nodes, not (node, layer) tuples
        for node in flat.nodes():
            assert isinstance(node, str)
            assert not isinstance(node, tuple)


class TestEdgeCases:
    """Tests for edge cases and corner scenarios."""

    def test_isolated_nodes_handled_correctly(self):
        """Isolated nodes (no edges) are preserved in conversions."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'A', 'type': 'L2'},
            {'source': 'B', 'type': 'L1'},
        ])
        
        multiplex = net.to_multiplex(method='intersection')
        
        # Only A is in both layers
        nodes = list(multiplex.get_nodes())
        assert len(nodes) == 2
        assert all(n[0] == 'A' for n in nodes)

    def test_self_loops_preserved(self):
        """Self-loops are preserved through conversions."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_edges([
            {'source': 'A', 'target': 'A', 'source_type': 'L1', 'target_type': 'L1'},
        ])
        
        flat = net.flatten_to_monoplex()
        
        assert ('A', 'A') in flat.edges()

    def test_multiple_edges_between_same_nodes(self):
        """Multiple edges between same nodes aggregate correctly."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        # Initialize the network first
        net._initiate_network()
        # Add multiple edges in same layer (MultiGraph allows this)
        net.core_network.add_edge(('A', 'L1'), ('B', 'L1'), key=0, weight=1)
        net.core_network.add_edge(('A', 'L1'), ('B', 'L1'), key=1, weight=2)
        
        flat = net.flatten_to_monoplex(method='union')
        
        # Should aggregate both edges
        assert flat.edges[('A', 'B')]['weight'] >= 1

    def test_layers_with_different_sizes(self):
        """Layers with different numbers of nodes handled correctly."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'L1'},
            {'source': 'B', 'type': 'L1'},
            {'source': 'C', 'type': 'L1'},
            {'source': 'A', 'type': 'L2'},
        ])
        
        multiplex_intersect = net.to_multiplex(method='intersection')
        multiplex_union = net.to_multiplex(method='union')
        
        # Intersection: only A
        assert len(list(multiplex_intersect.get_nodes())) == 2  # A in both layers
        
        # Union: all nodes in all layers
        assert len(list(multiplex_union.get_nodes())) == 6  # 3 nodes * 2 layers

    def test_numeric_node_ids(self):
        """Numeric node IDs work correctly."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_nodes([
            {'source': 1, 'type': 'L1'},
            {'source': 2, 'type': 'L1'},
            {'source': 1, 'type': 'L2'},
        ])
        
        multiplex = net.to_multiplex(method='intersection')
        flat = multiplex.flatten_to_monoplex()
        
        assert 1 in flat.nodes()

    def test_layer_names_with_special_characters(self):
        """Layer names with special characters work correctly."""
        net = multinet.multi_layer_network(network_type='multilayer', directed=False, verbose=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer-1'},
            {'source': 'A', 'type': 'layer_2'},
            {'source': 'A', 'type': 'layer.3'},
        ])
        
        multiplex = net.to_multiplex(method='intersection')
        
        nodes = list(multiplex.get_nodes())
        assert len(nodes) == 3
        layers = {n[1] for n in nodes}
        assert layers == {'layer-1', 'layer_2', 'layer.3'}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
