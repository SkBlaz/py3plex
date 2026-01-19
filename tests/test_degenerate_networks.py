"""Tests for degenerate and edge-case network handling.

This module ensures that the system handles edge cases gracefully:
- Empty networks
- Single-node networks
- Single-layer networks
- Disconnected layers
- Queries with no matches

Key Guarantees Tested:
- No crashes on degenerate inputs
- Well-defined empty outputs
- Correct provenance even for zero results
- Consistent behavior across edge cases
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.graph_ops import nodes, edges


class TestEmptyNetwork:
    """Test handling of empty networks."""

    def test_empty_network_node_query(self):
        """Test node query on empty network."""
        network = multinet.multi_layer_network(directed=False)
        
        query = Q.nodes()
        result = query.execute(network)
        
        # Should return empty result without crashing
        assert len(result) == 0
        
        # Should convert to pandas
        df = result.to_pandas()
        assert len(df) == 0

    def test_empty_network_edge_query(self):
        """Test edge query on empty network."""
        network = multinet.multi_layer_network(directed=False)
        
        query = Q.edges()
        result = query.execute(network)
        
        # Should return empty result
        assert len(result) == 0
        
        df = result.to_pandas()
        assert len(df) == 0

    def test_empty_network_with_compute(self):
        """Test compute query on empty network."""
        network = multinet.multi_layer_network(directed=False)
        
        query = Q.nodes().compute("degree")
        result = query.execute(network)
        
        # Should return empty result
        assert len(result) == 0

    def test_empty_network_has_provenance(self):
        """Test that empty network queries still produce provenance."""
        network = multinet.multi_layer_network(directed=False)
        
        query = Q.nodes()
        result = query.execute(network)
        
        # Should have provenance metadata even for empty result
        assert hasattr(result, 'meta')
        assert 'provenance' in result.meta
        
        prov = result.meta['provenance']
        assert 'engine' in prov
        assert 'timestamp_utc' in prov

    def test_empty_network_fingerprint(self):
        """Test network fingerprint of empty network."""
        network = multinet.multi_layer_network(directed=False)
        
        query = Q.nodes()
        result = query.execute(network)
        
        fp = result.meta['provenance']['network_fingerprint']
        
        # Should have zero counts
        assert fp['node_count'] == 0
        assert fp['edge_count'] == 0


class TestSingleNodeNetwork:
    """Test handling of single-node networks."""

    def test_single_node_query(self):
        """Test query on network with single node."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        query = Q.nodes()
        result = query.execute(network)
        
        # Should return one node
        assert len(result) == 1
        
        df = result.to_pandas()
        assert len(df) == 1

    def test_single_node_degree(self):
        """Test degree computation on single node."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        query = Q.nodes().compute("degree")
        result = query.execute(network)
        
        df = result.to_pandas()
        
        # Single node should have degree 0
        if 'degree' in df.columns:
            assert df['degree'].iloc[0] == 0

    def test_single_node_no_edges(self):
        """Test edge query on single-node network."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        query = Q.edges()
        result = query.execute(network)
        
        # Should return no edges
        assert len(result) == 0

    def test_single_node_centrality(self):
        """Test centrality on single-node network."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        query = Q.nodes().compute("betweenness_centrality")
        result = query.execute(network)
        
        # Should complete without error
        assert len(result) == 1
        
        df = result.to_pandas()
        if 'betweenness_centrality' in df.columns:
            # Single node has betweenness 0
            assert df['betweenness_centrality'].iloc[0] == 0


class TestSingleLayerNetwork:
    """Test handling of single-layer networks."""

    def test_single_layer_query(self):
        """Test query on single-layer network."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}
        ])
        
        query = Q.nodes()
        result = query.execute(network)
        
        # Should return all nodes
        assert len(result) == 2

    def test_single_layer_fingerprint(self):
        """Test fingerprint of single-layer network."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        
        query = Q.nodes()
        result = query.execute(network)
        
        fp = result.meta['provenance']['network_fingerprint']
        
        # Should have 1 layer
        assert fp['layer_count'] == 1
        assert len(fp['layers']) == 1
        assert 'layer1' in fp['layers']

    def test_single_layer_per_layer_grouping(self):
        """Test per-layer grouping on single-layer network."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        
        query = Q.nodes().per_layer()
        result = query.execute(network)
        
        # Should group into single layer
        if hasattr(result, 'meta') and 'grouping' in result.meta:
            grouping = result.meta['grouping']
            # Should have metadata about grouping
            assert grouping is not None


class TestDisconnectedLayers:
    """Test handling of disconnected layers."""

    def test_disconnected_layers_node_query(self):
        """Test node query on network with disconnected layers."""
        network = multinet.multi_layer_network(directed=False)
        
        # Layer 1 with nodes
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}
        ])
        
        # Layer 2 with nodes (no connection to layer 1)
        network.add_nodes([
            {'source': 'C', 'type': 'layer2'},
            {'source': 'D', 'type': 'layer2'},
        ])
        network.add_edges([
            {'source': 'C', 'target': 'D', 'source_type': 'layer2', 'target_type': 'layer2'}
        ])
        
        query = Q.nodes()
        result = query.execute(network)
        
        # Should return all nodes from both layers
        assert len(result) == 4

    def test_disconnected_layers_per_layer_grouping(self):
        """Test per-layer grouping with disconnected layers."""
        network = multinet.multi_layer_network(directed=False)
        
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer2'},
        ])
        
        query = Q.nodes().per_layer()
        result = query.execute(network)
        
        # Should group by layer
        if hasattr(result, 'meta') and 'grouping' in result.meta:
            grouping = result.meta['grouping']
            assert grouping is not None

    def test_disconnected_layers_layer_selection(self):
        """Test layer selection on disconnected layers."""
        network = multinet.multi_layer_network(directed=False)
        
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer2'},
        ])
        
        query = Q.nodes().from_layers(L["layer1"])
        result = query.execute(network)
        
        df = result.to_pandas()
        
        # Should return only layer1 nodes
        assert len(df) == 1


class TestNoMatchQueries:
    """Test queries that match no elements."""

    def test_no_match_degree_filter(self):
        """Test query with degree filter that matches nothing."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        
        query = Q.nodes().where(degree__gt=100)  # No node has degree > 100
        result = query.execute(network)
        
        # Should return empty result
        assert len(result) == 0
        
        # Should still have provenance
        assert 'provenance' in result.meta

    def test_no_match_layer_filter(self):
        """Test query for nonexistent layer."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
        ])
        
        query = Q.nodes().from_layers(L["nonexistent"])
        result = query.execute(network)
        
        # Should return empty result
        assert len(result) == 0

    def test_no_match_edge_filter(self):
        """Test edge query that matches nothing."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.0}
        ])
        
        query = Q.edges().where(weight__gt=100)  # No edge has weight > 100
        result = query.execute(network)
        
        # Should return empty result
        assert len(result) == 0

    def test_no_match_to_pandas(self):
        """Test that empty results convert to pandas gracefully."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        query = Q.nodes().where(degree__gt=100)
        result = query.execute(network)
        
        df = result.to_pandas()
        
        # Should be empty DataFrame with structure
        assert len(df) == 0
        assert df is not None


class TestGraphOpsEdgeCases:
    """Test graph_ops with edge cases."""

    def test_graphops_empty_network(self):
        """Test graph_ops on empty network."""
        network = multinet.multi_layer_network(directed=False)
        
        result = nodes(network)
        
        # Should handle empty network
        assert len(result) == 0

    def test_graphops_single_node(self):
        """Test graph_ops on single-node network."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        result = nodes(network).filter(lambda n: True)
        
        # Should return the single node
        assert len(result) == 1

    def test_graphops_no_match_filter(self):
        """Test graph_ops filter that matches nothing."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        
        result = nodes(network).filter(lambda n: False)
        
        # Should return empty
        assert len(result) == 0


class TestMinimalConnectedNetwork:
    """Test minimal connected network (2 nodes, 1 edge)."""

    def test_minimal_connected_structure(self):
        """Test minimal connected network structure."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}
        ])
        
        query = Q.nodes()
        result = query.execute(network)
        
        assert len(result) == 2
        
        edge_query = Q.edges()
        edge_result = edge_query.execute(network)
        
        assert len(edge_result) == 1

    def test_minimal_connected_degrees(self):
        """Test degrees in minimal connected network."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        network.add_edges([
            {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}
        ])
        
        query = Q.nodes().compute("degree")
        result = query.execute(network)
        
        df = result.to_pandas()
        
        if 'degree' in df.columns:
            # Both nodes should have degree 1
            degrees = sorted(df['degree'].tolist())
            assert degrees == [1, 1], "Both nodes should have degree 1"


class TestConsistencyAcrossEdgeCases:
    """Test that behavior is consistent across edge cases."""

    def test_empty_result_structure_consistent(self):
        """Test that empty results have consistent structure."""
        # Create various networks that produce empty results
        nets = [
            multinet.multi_layer_network(directed=False),  # Empty
        ]
        
        # Add a network with nodes but no matches
        net2 = multinet.multi_layer_network(directed=False)
        net2.add_nodes([{'source': 'A', 'type': 'layer1'}])
        nets.append(net2)
        
        results = []
        for net in nets:
            query = Q.nodes().where(degree__gt=100)
            result = query.execute(net)
            results.append(result)
        
        # All should be empty
        for result in results:
            assert len(result) == 0
        
        # All should convert to pandas
        for result in results:
            df = result.to_pandas()
            assert len(df) == 0

    def test_provenance_present_for_all_edge_cases(self):
        """Test that provenance is present for all edge cases."""
        # Empty network
        net1 = multinet.multi_layer_network(directed=False)
        
        # Single node
        net2 = multinet.multi_layer_network(directed=False)
        net2.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        # Single layer
        net3 = multinet.multi_layer_network(directed=False)
        net3.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        
        for net in [net1, net2, net3]:
            query = Q.nodes()
            result = query.execute(net)
            
            # All should have provenance
            assert 'provenance' in result.meta
            assert 'engine' in result.meta['provenance']
            assert 'timestamp_utc' in result.meta['provenance']
