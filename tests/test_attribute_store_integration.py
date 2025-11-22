"""
Integration tests for AttributeStore with multi_layer_network.

This module tests that the AttributeStore correctly synchronizes with
NetworkX operations in multi_layer_network when enabled.
"""

import pytest
from py3plex.core.multinet import multi_layer_network


class TestAttributeStoreIntegration:
    """Test AttributeStore integration with multi_layer_network."""
    
    def test_basic_network_without_store(self):
        """Test that networks work without attribute store (default behavior)."""
        net = multi_layer_network(use_attribute_store=False)
        
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ]
        net.add_nodes(nodes)
        
        edges = [
            {'source': 'A', 'target': 'B', 
             'source_type': 'layer1', 'target_type': 'layer1'},
        ]
        net.add_edges(edges)
        
        assert net.attribute_store is None
        # Network should still function normally
        assert len(list(net.get_nodes())) == 2
        assert len(list(net.get_edges())) == 1
    
    def test_basic_network_with_store(self):
        """Test that networks work with attribute store enabled."""
        net = multi_layer_network(use_attribute_store=True)
        
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ]
        net.add_nodes(nodes)
        
        edges = [
            {'source': 'A', 'target': 'B', 
             'source_type': 'layer1', 'target_type': 'layer1'},
        ]
        net.add_edges(edges)
        
        assert net.attribute_store is not None
        
        # Verify synchronization with NetworkX
        assert len(list(net.get_nodes())) == 2
        assert len(list(net.get_edges())) == 1
        
        # Verify attribute store has same data
        assert net.attribute_store.node_count() == 2
        assert net.attribute_store.edge_count() == 1
    
    def test_add_nodes_syncs_to_store(self):
        """Test that adding nodes syncs to attribute store."""
        net = multi_layer_network(use_attribute_store=True)
        
        # Add single node
        net.add_nodes({'source': 'A', 'type': 'layer1', 'weight': 0.5})
        
        assert net.attribute_store.has_node('A', 'layer1')
        attrs = net.attribute_store.get_node_attributes('A', 'layer1')
        assert attrs['weight'] == 0.5
        
        # Add batch of nodes
        nodes = [
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer2'},
        ]
        net.add_nodes(nodes)
        
        assert net.attribute_store.node_count() == 3
        assert net.attribute_store.has_node('B', 'layer1')
        assert net.attribute_store.has_node('C', 'layer2')
    
    def test_add_edges_syncs_to_store(self):
        """Test that adding edges syncs to attribute store."""
        net = multi_layer_network(use_attribute_store=True)
        
        # Add nodes first
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer2'},
        ]
        net.add_nodes(nodes)
        
        # Add single edge
        net.add_edges({
            'source': 'A', 
            'target': 'B',
            'source_type': 'layer1',
            'target_type': 'layer1',
            'weight': 0.8
        })
        
        assert net.attribute_store.has_edge('A', 'layer1', 'B', 'layer1')
        attrs = net.attribute_store.get_edge_attributes('A', 'layer1', 'B', 'layer1')
        assert attrs['weight'] == 0.8
        
        # Add batch of edges
        edges = [
            {'source': 'B', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer2'},
        ]
        net.add_edges(edges)
        
        assert net.attribute_store.edge_count() == 2
        assert net.attribute_store.has_edge('B', 'layer1', 'C', 'layer2')
    
    def test_layer_filtering_with_store(self):
        """Test layer-specific queries with attribute store."""
        net = multi_layer_network(use_attribute_store=True)
        
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer2'},
            {'source': 'D', 'type': 'layer2'},
        ]
        net.add_nodes(nodes)
        
        # Query nodes in specific layer
        layer1_nodes = net.attribute_store.get_nodes_in_layer('layer1')
        assert len(layer1_nodes) == 2
        assert 'A' in layer1_nodes
        assert 'B' in layer1_nodes
        
        layer2_nodes = net.attribute_store.get_nodes_in_layer('layer2')
        assert len(layer2_nodes) == 2
        assert 'C' in layer2_nodes
        assert 'D' in layer2_nodes
    
    def test_unique_layers_with_store(self):
        """Test getting unique layers with attribute store."""
        net = multi_layer_network(use_attribute_store=True)
        
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer2'},
            {'source': 'C', 'type': 'layer3'},
        ]
        net.add_nodes(nodes)
        
        layers = net.attribute_store.get_unique_layers()
        assert len(layers) == 3
        assert 'layer1' in layers
        assert 'layer2' in layers
        assert 'layer3' in layers
    
    def test_interlayer_edges_with_store(self):
        """Test filtering inter-layer edges with attribute store."""
        net = multi_layer_network(use_attribute_store=True)
        
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer2'},
        ]
        net.add_nodes(nodes)
        
        edges = [
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},  # Intra-layer
            {'source': 'A', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer2'},  # Inter-layer
            {'source': 'B', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer2'},  # Inter-layer
        ]
        net.add_edges(edges)
        
        interlayer = net.attribute_store.get_interlayer_edges()
        assert len(interlayer) == 2
    
    def test_neighbors_with_store(self):
        """Test getting neighbors with attribute store."""
        net = multi_layer_network(use_attribute_store=True)
        
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer1'},
        ]
        net.add_nodes(nodes)
        
        edges = [
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'A', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ]
        net.add_edges(edges)
        
        neighbors = net.attribute_store.get_neighbors('A', 'layer1')
        assert len(neighbors) == 2
        assert ('B', 'layer1') in neighbors
        assert ('C', 'layer1') in neighbors
    
    def test_summary_stats_with_store(self):
        """Test summary statistics with attribute store."""
        net = multi_layer_network(use_attribute_store=True)
        
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer2'},
        ]
        net.add_nodes(nodes)
        
        edges = [
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'A', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer2'},
        ]
        net.add_edges(edges)
        
        summary = net.attribute_store.summary()
        assert summary['nodes'] == 3
        assert summary['edges'] == 2
        assert summary['layers'] == 2
        assert summary['unique_node_ids'] == 3


class TestAttributeStorePerformance:
    """Test performance characteristics with attribute store enabled."""
    
    def test_large_batch_operations(self):
        """Test that large batch operations work efficiently with attribute store."""
        net = multi_layer_network(use_attribute_store=True)
        
        # Add 1000 nodes
        nodes = []
        for i in range(1000):
            nodes.append({
                'source': f'node_{i}',
                'type': f'layer_{i % 10}',
                'weight': i * 0.1
            })
        
        net.add_nodes(nodes)
        assert net.attribute_store.node_count() == 1000
        
        # Add 2000 edges
        edges = []
        for i in range(2000):
            edges.append({
                'source': f'node_{i % 1000}',
                'target': f'node_{(i + 1) % 1000}',
                'source_type': f'layer_{i % 10}',
                'target_type': f'layer_{(i + 1) % 10}',
                'weight': i * 0.1
            })
        
        net.add_edges(edges)
        assert net.attribute_store.edge_count() == 2000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
