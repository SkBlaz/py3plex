"""
Tests for the AttributeStore backend.

This module tests the Polars-based attribute storage backend for
efficient node/edge/metadata querying.
"""

import pytest
from py3plex.core.attribute_store import AttributeStore


class TestAttributeStoreNodes:
    """Test node operations in AttributeStore."""
    
    def test_add_single_node(self):
        """Test adding a single node."""
        store = AttributeStore()
        store.add_node('A', 'layer1')
        
        assert store.node_count() == 1
        assert store.has_node('A', 'layer1')
    
    def test_add_node_with_attributes(self):
        """Test adding a node with custom attributes."""
        store = AttributeStore()
        store.add_node('A', 'layer1', weight=0.5, label='Node A')
        
        attrs = store.get_node_attributes('A', 'layer1')
        assert attrs is not None
        assert attrs['weight'] == 0.5
        assert attrs['label'] == 'Node A'
    
    def test_add_nodes_batch(self):
        """Test adding multiple nodes in batch."""
        store = AttributeStore()
        nodes = [
            {'node_id': 'A', 'layer': 'layer1'},
            {'node_id': 'B', 'layer': 'layer1'},
            {'node_id': 'C', 'layer': 'layer2'},
        ]
        store.add_nodes_batch(nodes)
        
        assert store.node_count() == 3
        assert store.has_node('A', 'layer1')
        assert store.has_node('B', 'layer1')
        assert store.has_node('C', 'layer2')
    
    def test_add_nodes_batch_with_source_type_keys(self):
        """Test adding nodes using 'source' and 'type' keys (backward compatibility)."""
        store = AttributeStore()
        nodes = [
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ]
        store.add_nodes_batch(nodes)
        
        assert store.node_count() == 2
        assert store.has_node('A', 'layer1')
        assert store.has_node('B', 'layer1')
    
    def test_remove_node(self):
        """Test removing a node."""
        store = AttributeStore()
        store.add_node('A', 'layer1')
        store.add_node('B', 'layer1')
        
        assert store.node_count() == 2
        store.remove_node('A', 'layer1')
        
        assert store.node_count() == 1
        assert not store.has_node('A', 'layer1')
        assert store.has_node('B', 'layer1')
    
    def test_get_all_nodes(self):
        """Test getting all nodes."""
        store = AttributeStore()
        nodes = [
            {'node_id': 'A', 'layer': 'layer1'},
            {'node_id': 'B', 'layer': 'layer1'},
            {'node_id': 'C', 'layer': 'layer2'},
        ]
        store.add_nodes_batch(nodes)
        
        all_nodes = store.get_all_nodes()
        assert len(all_nodes) == 3
        assert ('A', 'layer1') in all_nodes
        assert ('B', 'layer1') in all_nodes
        assert ('C', 'layer2') in all_nodes
    
    def test_get_nodes_in_layer(self):
        """Test getting nodes in a specific layer."""
        store = AttributeStore()
        nodes = [
            {'node_id': 'A', 'layer': 'layer1'},
            {'node_id': 'B', 'layer': 'layer1'},
            {'node_id': 'C', 'layer': 'layer2'},
        ]
        store.add_nodes_batch(nodes)
        
        layer1_nodes = store.get_nodes_in_layer('layer1')
        assert len(layer1_nodes) == 2
        assert 'A' in layer1_nodes
        assert 'B' in layer1_nodes
        
        layer2_nodes = store.get_nodes_in_layer('layer2')
        assert len(layer2_nodes) == 1
        assert 'C' in layer2_nodes
    
    def test_get_unique_layers(self):
        """Test getting unique layer identifiers."""
        store = AttributeStore()
        nodes = [
            {'node_id': 'A', 'layer': 'layer1'},
            {'node_id': 'B', 'layer': 'layer1'},
            {'node_id': 'C', 'layer': 'layer2'},
            {'node_id': 'D', 'layer': 'layer3'},
        ]
        store.add_nodes_batch(nodes)
        
        layers = store.get_unique_layers()
        assert len(layers) == 3
        assert 'layer1' in layers
        assert 'layer2' in layers
        assert 'layer3' in layers
    
    def test_get_unique_node_ids(self):
        """Test getting unique node IDs across layers."""
        store = AttributeStore()
        nodes = [
            {'node_id': 'A', 'layer': 'layer1'},
            {'node_id': 'A', 'layer': 'layer2'},  # Same node, different layer
            {'node_id': 'B', 'layer': 'layer1'},
        ]
        store.add_nodes_batch(nodes)
        
        node_ids = store.get_unique_node_ids()
        assert len(node_ids) == 2
        assert 'A' in node_ids
        assert 'B' in node_ids


class TestAttributeStoreEdges:
    """Test edge operations in AttributeStore."""
    
    def test_add_single_edge(self):
        """Test adding a single edge."""
        store = AttributeStore()
        store.add_edge('A', 'layer1', 'B', 'layer1')
        
        assert store.edge_count() == 1
        assert store.has_edge('A', 'layer1', 'B', 'layer1')
    
    def test_add_edge_with_attributes(self):
        """Test adding an edge with custom attributes."""
        store = AttributeStore()
        store.add_edge('A', 'layer1', 'B', 'layer1', 
                      weight=0.8, edge_type='interaction', label='test')
        
        attrs = store.get_edge_attributes('A', 'layer1', 'B', 'layer1')
        assert attrs is not None
        assert attrs['weight'] == 0.8
        assert attrs['edge_type'] == 'interaction'
        assert attrs['label'] == 'test'
    
    def test_add_edges_batch(self):
        """Test adding multiple edges in batch."""
        store = AttributeStore()
        edges = [
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'B', 'target_layer': 'layer1'},
            {'source_id': 'B', 'source_layer': 'layer1', 
             'target_id': 'C', 'target_layer': 'layer1'},
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'A', 'target_layer': 'layer2'},  # Inter-layer
        ]
        store.add_edges_batch(edges)
        
        assert store.edge_count() == 3
        assert store.has_edge('A', 'layer1', 'B', 'layer1')
        assert store.has_edge('B', 'layer1', 'C', 'layer1')
        assert store.has_edge('A', 'layer1', 'A', 'layer2')
    
    def test_add_edges_batch_with_alternate_keys(self):
        """Test adding edges using alternate key names (backward compatibility)."""
        store = AttributeStore()
        edges = [
            {'source': 'A', 'source_type': 'layer1', 
             'target': 'B', 'target_type': 'layer1', 'weight': 0.5},
        ]
        store.add_edges_batch(edges)
        
        assert store.edge_count() == 1
        assert store.has_edge('A', 'layer1', 'B', 'layer1')
        attrs = store.get_edge_attributes('A', 'layer1', 'B', 'layer1')
        assert attrs['weight'] == 0.5
    
    def test_remove_edge(self):
        """Test removing an edge."""
        store = AttributeStore()
        store.add_edge('A', 'layer1', 'B', 'layer1')
        store.add_edge('B', 'layer1', 'C', 'layer1')
        
        assert store.edge_count() == 2
        store.remove_edge('A', 'layer1', 'B', 'layer1')
        
        assert store.edge_count() == 1
        assert not store.has_edge('A', 'layer1', 'B', 'layer1')
        assert store.has_edge('B', 'layer1', 'C', 'layer1')
    
    def test_get_all_edges(self):
        """Test getting all edges."""
        store = AttributeStore()
        edges = [
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'B', 'target_layer': 'layer1'},
            {'source_id': 'B', 'source_layer': 'layer1', 
             'target_id': 'C', 'target_layer': 'layer1'},
        ]
        store.add_edges_batch(edges)
        
        all_edges = store.get_all_edges()
        assert len(all_edges) == 2
        assert (('A', 'layer1'), ('B', 'layer1')) in all_edges
        assert (('B', 'layer1'), ('C', 'layer1')) in all_edges
    
    def test_get_neighbors(self):
        """Test getting neighbors of a node."""
        store = AttributeStore()
        edges = [
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'B', 'target_layer': 'layer1'},
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'C', 'target_layer': 'layer1'},
            {'source_id': 'D', 'source_layer': 'layer1', 
             'target_id': 'A', 'target_layer': 'layer1'},
        ]
        store.add_edges_batch(edges)
        
        neighbors = store.get_neighbors('A', 'layer1')
        assert len(neighbors) == 3
        assert ('B', 'layer1') in neighbors
        assert ('C', 'layer1') in neighbors
        assert ('D', 'layer1') in neighbors
    
    def test_get_edges_in_layer(self):
        """Test getting edges within a specific layer."""
        store = AttributeStore()
        edges = [
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'B', 'target_layer': 'layer1'},
            {'source_id': 'B', 'source_layer': 'layer1', 
             'target_id': 'C', 'target_layer': 'layer1'},
            {'source_id': 'D', 'source_layer': 'layer2', 
             'target_id': 'E', 'target_layer': 'layer2'},
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'D', 'target_layer': 'layer2'},  # Inter-layer
        ]
        store.add_edges_batch(edges)
        
        layer1_edges = store.get_edges_in_layer('layer1')
        assert len(layer1_edges) == 2
        assert (('A', 'layer1'), ('B', 'layer1')) in layer1_edges
        assert (('B', 'layer1'), ('C', 'layer1')) in layer1_edges
        
        layer2_edges = store.get_edges_in_layer('layer2')
        assert len(layer2_edges) == 1
        assert (('D', 'layer2'), ('E', 'layer2')) in layer2_edges
    
    def test_get_interlayer_edges(self):
        """Test getting inter-layer edges."""
        store = AttributeStore()
        edges = [
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'B', 'target_layer': 'layer1'},
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'A', 'target_layer': 'layer2'},  # Inter-layer
            {'source_id': 'B', 'source_layer': 'layer1', 
             'target_id': 'C', 'target_layer': 'layer2'},  # Inter-layer
        ]
        store.add_edges_batch(edges)
        
        interlayer_edges = store.get_interlayer_edges()
        assert len(interlayer_edges) == 2
        assert (('A', 'layer1'), ('A', 'layer2')) in interlayer_edges
        assert (('B', 'layer1'), ('C', 'layer2')) in interlayer_edges


class TestAttributeStoreStatistics:
    """Test statistics and summary operations."""
    
    def test_node_count(self):
        """Test node counting."""
        store = AttributeStore()
        assert store.node_count() == 0
        
        store.add_node('A', 'layer1')
        assert store.node_count() == 1
        
        store.add_node('B', 'layer1')
        assert store.node_count() == 2
    
    def test_edge_count(self):
        """Test edge counting."""
        store = AttributeStore()
        assert store.edge_count() == 0
        
        store.add_edge('A', 'layer1', 'B', 'layer1')
        assert store.edge_count() == 1
        
        store.add_edge('B', 'layer1', 'C', 'layer1')
        assert store.edge_count() == 2
    
    def test_layer_count(self):
        """Test layer counting."""
        store = AttributeStore()
        nodes = [
            {'node_id': 'A', 'layer': 'layer1'},
            {'node_id': 'B', 'layer': 'layer1'},
            {'node_id': 'C', 'layer': 'layer2'},
            {'node_id': 'D', 'layer': 'layer3'},
        ]
        store.add_nodes_batch(nodes)
        
        assert store.layer_count() == 3
    
    def test_degree(self):
        """Test node degree calculation."""
        store = AttributeStore()
        edges = [
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'B', 'target_layer': 'layer1'},
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'C', 'target_layer': 'layer1'},
            {'source_id': 'D', 'source_layer': 'layer1', 
             'target_id': 'A', 'target_layer': 'layer1'},
        ]
        store.add_edges_batch(edges)
        
        degree_a = store.degree('A', 'layer1')
        assert degree_a == 3  # Connected to B, C, D
        
        degree_b = store.degree('B', 'layer1')
        assert degree_b == 1  # Connected to A only
    
    def test_summary(self):
        """Test summary statistics."""
        store = AttributeStore()
        nodes = [
            {'node_id': 'A', 'layer': 'layer1'},
            {'node_id': 'B', 'layer': 'layer1'},
            {'node_id': 'C', 'layer': 'layer2'},
        ]
        store.add_nodes_batch(nodes)
        
        edges = [
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'B', 'target_layer': 'layer1'},
            {'source_id': 'A', 'source_layer': 'layer1', 
             'target_id': 'C', 'target_layer': 'layer2'},
        ]
        store.add_edges_batch(edges)
        
        summary = store.summary()
        assert summary['nodes'] == 3
        assert summary['edges'] == 2
        assert summary['layers'] == 2
        assert summary['unique_node_ids'] == 3
    
    def test_clear(self):
        """Test clearing the store."""
        store = AttributeStore()
        store.add_node('A', 'layer1')
        store.add_edge('A', 'layer1', 'B', 'layer1')
        
        assert store.node_count() > 0
        assert store.edge_count() > 0
        
        store.clear()
        
        assert store.node_count() == 0
        assert store.edge_count() == 0


class TestAttributeStoreEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_store(self):
        """Test operations on empty store."""
        store = AttributeStore()
        
        assert store.node_count() == 0
        assert store.edge_count() == 0
        assert len(store.get_all_nodes()) == 0
        assert len(store.get_all_edges()) == 0
    
    def test_nonexistent_node(self):
        """Test querying nonexistent node."""
        store = AttributeStore()
        
        assert not store.has_node('A', 'layer1')
        assert store.get_node_attributes('A', 'layer1') is None
    
    def test_nonexistent_edge(self):
        """Test querying nonexistent edge."""
        store = AttributeStore()
        
        assert not store.has_edge('A', 'layer1', 'B', 'layer1')
        assert store.get_edge_attributes('A', 'layer1', 'B', 'layer1') is None
    
    def test_same_node_different_layers(self):
        """Test same node ID in different layers."""
        store = AttributeStore()
        nodes = [
            {'node_id': 'A', 'layer': 'layer1', 'attr': 'val1'},
            {'node_id': 'A', 'layer': 'layer2', 'attr': 'val2'},
        ]
        store.add_nodes_batch(nodes)
        
        assert store.node_count() == 2
        assert store.has_node('A', 'layer1')
        assert store.has_node('A', 'layer2')
        
        attrs1 = store.get_node_attributes('A', 'layer1')
        attrs2 = store.get_node_attributes('A', 'layer2')
        assert attrs1['attr'] == 'val1'
        assert attrs2['attr'] == 'val2'
    
    def test_numeric_node_ids(self):
        """Test that numeric node IDs are converted to strings."""
        store = AttributeStore()
        store.add_node(123, 'layer1')
        
        assert store.has_node('123', 'layer1')
        # Also check if the original numeric ID works
        assert store.has_node(123, 'layer1')
    
    def test_empty_batch_operations(self):
        """Test batch operations with empty lists."""
        store = AttributeStore()
        
        store.add_nodes_batch([])
        assert store.node_count() == 0
        
        store.add_edges_batch([])
        assert store.edge_count() == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
