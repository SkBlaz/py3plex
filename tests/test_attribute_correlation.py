"""
Tests for py3plex.algorithms.attribute_correlation module.

This module tests node-attribute correlation analysis.
"""

import pytest
import networkx as nx
from py3plex.core import multinet
from py3plex.algorithms.attribute_correlation import (
    correlate_attributes_with_centrality,
)


class TestAttributeCorrelation:
    """Test attribute-centrality correlation analysis."""

    def test_correlate_with_degree(self):
        """Test correlation of node attributes with degree centrality."""
        # Create a simple network
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B', 
             'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'B', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        # Add node attributes - use actual node names from core_network
        if net.core_network:
            node_attrs = {}
            for node in net.core_network.nodes():
                # Assign weight based on node identity
                if 'A' in str(node):
                    node_attrs[node] = 1.0
                elif 'B' in str(node):
                    node_attrs[node] = 2.0
                elif 'C' in str(node):
                    node_attrs[node] = 1.5
            nx.set_node_attributes(net.core_network, node_attrs, 'weight')
        
        # Test correlation with by_layer=False to get global result
        result = correlate_attributes_with_centrality(
            net, 
            attribute_name='weight',
            centrality_type='degree',
            correlation_method='pearson',
            by_layer=False
        )
        
        assert isinstance(result, dict), "Result should be a dictionary"
        # Should have at least one result (global)
        assert 'global' in result, "Should return global correlation result"

    def test_correlate_missing_scipy(self, monkeypatch):
        """Test error when scipy is not available."""
        # Mock scipy as unavailable
        import py3plex.algorithms.attribute_correlation as module
        monkeypatch.setattr(module, 'SCIPY_AVAILABLE', False)
        
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        with pytest.raises(ImportError, match="scipy is required"):
            correlate_attributes_with_centrality(net, 'weight')

    def test_correlate_no_core_network(self):
        """Test error when network has no core_network."""
        net = multinet.multi_layer_network(directed=False)
        # Create a network without initializing core_network
        net.core_network = None
        
        with pytest.raises(ValueError, match="Network has no core_network"):
            correlate_attributes_with_centrality(net, 'weight')

    def test_correlate_unknown_centrality(self):
        """Test error with unknown centrality type."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        with pytest.raises(ValueError, match="Unknown centrality type"):
            correlate_attributes_with_centrality(
                net, 
                'weight',
                centrality_type='unknown_centrality'
            )

    def test_correlate_different_methods(self):
        """Test different correlation methods."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'B', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        if net.core_network:
            # Use actual node identifiers from core_network
            node_attrs = {}
            for node in net.core_network.nodes():
                # Assign weight based on node identity
                if 'A' in str(node):
                    node_attrs[node] = 1.0
                elif 'B' in str(node):
                    node_attrs[node] = 2.0
                elif 'C' in str(node):
                    node_attrs[node] = 1.5
            nx.set_node_attributes(net.core_network, node_attrs, 'weight')
        
        # Test pearson
        result1 = correlate_attributes_with_centrality(
            net, 'weight', correlation_method='pearson'
        )
        assert isinstance(result1, dict)
        
        # Test spearman
        result2 = correlate_attributes_with_centrality(
            net, 'weight', correlation_method='spearman'
        )
        assert isinstance(result2, dict)

    def test_correlate_by_layer_flag(self):
        """Test by_layer parameter."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        if net.core_network:
            # Use actual node identifiers from core_network
            node_attrs = {}
            for node in net.core_network.nodes():
                # Assign weight based on node identity
                if 'A' in str(node):
                    node_attrs[node] = 1.0
                elif 'B' in str(node):
                    node_attrs[node] = 2.0
            nx.set_node_attributes(net.core_network, node_attrs, 'weight')
        
        # Test with by_layer=True
        result1 = correlate_attributes_with_centrality(
            net, 'weight', by_layer=True
        )
        assert isinstance(result1, dict)
        
        # Test with by_layer=False
        result2 = correlate_attributes_with_centrality(
            net, 'weight', by_layer=False
        )
        assert isinstance(result2, dict)

    def test_correlate_insufficient_nodes(self):
        """Test with insufficient nodes for correlation."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
        ])
        
        if net.core_network:
            # Use actual node identifiers from core_network
            node_attrs = {}
            for node in net.core_network.nodes():
                if 'A' in str(node):
                    node_attrs[node] = 1.0
            nx.set_node_attributes(net.core_network, node_attrs, 'weight')
        
        # Should handle gracefully
        result = correlate_attributes_with_centrality(
            net, 'weight', by_layer=False
        )
        assert isinstance(result, dict)
