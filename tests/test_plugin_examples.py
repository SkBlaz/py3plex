"""Tests for py3plex.plugins.examples module.

This module tests the example plugin implementations.
"""

import pytest
from py3plex.core import multinet
from py3plex.plugins.examples import (
    ExampleDegreeCentrality,
    ExampleSimpleCommunity,
)


@pytest.fixture
def simple_network():
    """Create a simple test network."""
    network = multinet.multi_layer_network(directed=False, verbose=False)
    network.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer1'},
    ])
    network.add_edges([
        {
            'source': 'A',
            'target': 'B',
            'source_type': 'layer1',
            'target_type': 'layer1'
        },
        {
            'source': 'B',
            'target': 'C',
            'source_type': 'layer1',
            'target_type': 'layer1'
        },
        {
            'source': 'C',
            'target': 'D',
            'source_type': 'layer1',
            'target_type': 'layer1'
        }
    ])
    return network


@pytest.fixture
def star_network():
    """Create a star network for testing centrality."""
    network = multinet.multi_layer_network(directed=False, verbose=False)
    network.add_nodes([
        {'source': 'center', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
    ])
    network.add_edges([
        {
            'source': 'center',
            'target': 'A',
            'source_type': 'layer1',
            'target_type': 'layer1'
        },
        {
            'source': 'center',
            'target': 'B',
            'source_type': 'layer1',
            'target_type': 'layer1'
        },
        {
            'source': 'center',
            'target': 'C',
            'source_type': 'layer1',
            'target_type': 'layer1'
        }
    ])
    return network


class TestExampleDegreeCentrality:
    """Test ExampleDegreeCentrality plugin."""

    def test_plugin_properties(self):
        """Test plugin metadata properties."""
        plugin = ExampleDegreeCentrality()
        
        assert plugin.name == "example_degree"
        assert "degree centrality" in plugin.description.lower()
        assert plugin.author == "Py3plex Development Team"
        assert plugin.supports_weighted is True
        assert plugin.supports_directed is True
        assert plugin.supports_multilayer is True

    def test_compute_basic(self, simple_network):
        """Test basic degree centrality computation."""
        plugin = ExampleDegreeCentrality()
        centrality = plugin.compute(simple_network)
        
        assert isinstance(centrality, dict)
        assert len(centrality) == 4  # 4 nodes
        
        # Check that middle nodes have degree 2, end nodes have degree 1
        # Nodes are stored as (id, layer) tuples
        assert centrality[('B', 'layer1')] == 2
        assert centrality[('C', 'layer1')] == 2
        assert centrality[('A', 'layer1')] == 1
        assert centrality[('D', 'layer1')] == 1

    def test_compute_normalized(self, star_network):
        """Test normalized degree centrality."""
        plugin = ExampleDegreeCentrality()
        centrality = plugin.compute(star_network, normalized=True)
        
        # Center node should have highest normalized centrality
        center_centrality = centrality[('center', 'layer1')]
        assert center_centrality == 1.0  # 3/(4-1) = 1.0
        
        # Peripheral nodes should have lower centrality
        assert centrality[('A', 'layer1')] < center_centrality

    def test_compute_unnormalized(self, star_network):
        """Test unnormalized degree centrality."""
        plugin = ExampleDegreeCentrality()
        centrality = plugin.compute(star_network, normalized=False)
        
        # Center node should have degree 3
        assert centrality[('center', 'layer1')] == 3
        
        # Peripheral nodes should have degree 1
        assert centrality[('A', 'layer1')] == 1
        assert centrality[('B', 'layer1')] == 1
        assert centrality[('C', 'layer1')] == 1

    def test_compute_empty_network(self):
        """Test with empty network."""
        network = multinet.multi_layer_network(directed=False, verbose=False)
        plugin = ExampleDegreeCentrality()
        centrality = plugin.compute(network)
        
        assert centrality == {}

    def test_validate(self):
        """Test plugin validation."""
        plugin = ExampleDegreeCentrality()
        assert plugin.validate() is True

    def test_compute_with_invalid_network(self):
        """Test compute with invalid network object."""
        plugin = ExampleDegreeCentrality()
        
        # Create a mock object without core_network
        class BadNetwork:
            pass
        
        with pytest.raises(ValueError, match="multi_layer_network"):
            plugin.compute(BadNetwork())


class TestExampleSimpleCommunity:
    """Test ExampleSimpleCommunity plugin."""

    def test_plugin_properties(self):
        """Test plugin metadata properties."""
        plugin = ExampleSimpleCommunity()
        
        assert plugin.name == "example_simple"
        assert "community detection" in plugin.description.lower()
        assert plugin.author == "Py3plex Development Team"
        assert plugin.supports_overlapping is False

    def test_compute_basic(self, simple_network):
        """Test basic community detection."""
        plugin = ExampleSimpleCommunity()
        communities = plugin.detect(simple_network)
        
        assert isinstance(communities, dict)
        assert len(communities) > 0

    def test_compute_connected_components(self):
        """Test detection of connected components."""
        # Create a network with 2 components
        network = multinet.multi_layer_network(directed=False, verbose=False)
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
            {'source': 'X', 'type': 'layer1'},
            {'source': 'Y', 'type': 'layer1'},
        ])
        network.add_edges([
            {
                'source': 'A',
                'target': 'B',
                'source_type': 'layer1',
                'target_type': 'layer1'
            },
            {
                'source': 'X',
                'target': 'Y',
                'source_type': 'layer1',
                'target_type': 'layer1'
            }
        ])
        
        plugin = ExampleSimpleCommunity()
        communities = plugin.detect(network)
        
        # Should detect 2 communities
        community_ids = set(communities.values())
        assert len(community_ids) == 2

    def test_compute_empty_network(self):
        """Test with empty network."""
        network = multinet.multi_layer_network(directed=False, verbose=False)
        plugin = ExampleSimpleCommunity()
        communities = plugin.detect(network)
        
        assert communities == {}

    def test_validate(self):
        """Test plugin validation."""
        plugin = ExampleSimpleCommunity()
        assert plugin.validate() is True

    def test_compute_with_invalid_network(self):
        """Test compute with invalid network object."""
        plugin = ExampleSimpleCommunity()
        
        # Create a mock object without core_network
        class BadNetwork:
            pass
        
        with pytest.raises(ValueError, match="multi_layer_network"):
            plugin.detect(BadNetwork())


class TestPluginIntegration:
    """Integration tests for example plugins."""

    def test_both_plugins_on_same_network(self, simple_network):
        """Test using multiple plugins on the same network."""
        centrality_plugin = ExampleDegreeCentrality()
        community_plugin = ExampleSimpleCommunity()
        
        # Compute both analyses
        centrality = centrality_plugin.compute(simple_network)
        communities = community_plugin.detect(simple_network)
        
        # Both should return results
        assert len(centrality) > 0
        assert len(communities) > 0
        
        # They should have the same nodes
        assert set(centrality.keys()) == set(communities.keys())
