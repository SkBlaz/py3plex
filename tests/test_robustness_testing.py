"""
Tests for py3plex.algorithms.robustness_testing module.

This module tests network robustness and stability analysis.
"""

import pytest
from py3plex.core import multinet
from py3plex.algorithms.robustness_testing import (
    targeted_node_removal,
)


class TestRobustnessTesting:
    """Test network robustness analysis."""

    def test_targeted_removal_degree(self):
        """Test targeted removal by degree."""
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
            {'source': 'B', 'target': 'D',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        results = targeted_node_removal(net, removal_strategy='degree', fraction=0.25)
        
        assert isinstance(results, dict), "Should return dictionary of metrics"
        assert 'size' in results, "Should track size metric"
        assert isinstance(results['size'], list), "Metric values should be a list"

    def test_targeted_removal_betweenness(self):
        """Test targeted removal by betweenness centrality."""
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
        
        results = targeted_node_removal(net, removal_strategy='betweenness', fraction=0.33)
        
        assert isinstance(results, dict)
        assert len(results) > 0

    def test_targeted_removal_random(self):
        """Test random node removal."""
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
        
        results = targeted_node_removal(net, removal_strategy='random', fraction=0.33)
        
        assert isinstance(results, dict)

    def test_targeted_removal_eigenvector(self):
        """Test targeted removal by eigenvector centrality."""
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
        
        results = targeted_node_removal(net, removal_strategy='eigenvector', fraction=0.33)
        
        assert isinstance(results, dict)

    def test_targeted_removal_no_core_network(self):
        """Test error when network has no core_network."""
        net = multinet.multi_layer_network(directed=False)
        net.core_network = None
        
        with pytest.raises(ValueError, match="Network has no core_network"):
            targeted_node_removal(net)

    def test_targeted_removal_custom_metrics(self):
        """Test with custom metrics."""
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
        
        results = targeted_node_removal(
            net, 
            removal_strategy='degree',
            fraction=0.33,
            metrics=['size', 'edges']
        )
        
        assert 'size' in results
        assert 'edges' in results

    def test_targeted_removal_num_removals(self):
        """Test with explicit number of removals."""
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
        ])
        
        results = targeted_node_removal(net, num_removals=2)
        
        assert isinstance(results, dict)

    def test_targeted_removal_unknown_strategy(self):
        """Test error with unknown removal strategy."""
        net = multinet.multi_layer_network(directed=False)
        net.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        net.add_edges([
            {'source': 'A', 'target': 'B',
             'source_type': 'layer1', 'target_type': 'layer1'},
        ])
        
        with pytest.raises(ValueError, match="Unknown removal strategy"):
            targeted_node_removal(net, removal_strategy='unknown_strategy')
