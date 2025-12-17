"""
Tests for py3plex.algorithms.graph_summarization module.

This module tests graph summarization algorithms.
"""

import pytest
from py3plex.core import multinet
from py3plex.algorithms.graph_summarization import (
    collapse_low_degree_nodes,
)


class TestGraphSummarization:
    """Test graph summarization algorithms."""

    def test_collapse_low_degree_star(self):
        """Test collapsing low-degree nodes using star aggregation."""
        # Create a network with a low-degree node
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'C', 'type': 'layer1'},
            {'source': 'D', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'B', 'target': 'C',
             'source_type': 'layer1', 'target_type': 'layer1'},
            {'source': 'C', 'target': 'D',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        # Collapse nodes with degree < 2
        summarized = collapse_low_degree_nodes(net, degree_threshold=2, aggregation_method='star')
        
        assert summarized is not None, "Should return a summarized network"
        assert hasattr(summarized, 'core_network'), "Should have core_network"

    def test_collapse_low_degree_clique(self):
        """Test collapsing low-degree nodes using clique aggregation."""
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
        
        summarized = collapse_low_degree_nodes(net, degree_threshold=2, aggregation_method='clique')
        
        assert summarized is not None
        assert hasattr(summarized, 'core_network')

    def test_collapse_low_degree_remove(self):
        """Test removing low-degree nodes."""
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
        
        summarized = collapse_low_degree_nodes(net, degree_threshold=2, aggregation_method='remove')
        
        assert summarized is not None
        assert hasattr(summarized, 'core_network')

    def test_collapse_no_core_network(self):
        """Test error when network has no core_network."""
        net = multinet.multi_layer_network(directed=False)
        net.core_network = None
        
        with pytest.raises(ValueError, match="Network has no core_network"):
            collapse_low_degree_nodes(net)

    def test_collapse_empty_network(self):
        """Test collapsing on empty network."""
        net = multinet.multi_layer_network(directed=False)
        
        # Empty network has no core_network, should raise error
        with pytest.raises(ValueError, match="Network has no core_network"):
            collapse_low_degree_nodes(net, degree_threshold=1)

    def test_collapse_threshold_zero(self):
        """Test with threshold 0 (all nodes have degree >= 0)."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        # Threshold 0 means no nodes should be removed
        summarized = collapse_low_degree_nodes(net, degree_threshold=0)
        assert summarized is not None

    def test_collapse_high_threshold(self):
        """Test with very high threshold (removes all nodes)."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        # Very high threshold should remove most/all nodes
        summarized = collapse_low_degree_nodes(net, degree_threshold=100)
        assert summarized is not None
