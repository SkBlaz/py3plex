"""
Tests for Ollivier-Ricci curvature and Ricci flow on multilayer networks.

This module tests the integration of GraphRicciCurvature with py3plex's
multilayer network structures, including curvature computation and Ricci flow
on aggregated networks, individual layers, and supra-graphs.
"""

import pytest
import networkx as nx

from py3plex.core import multinet
from py3plex.algorithms.curvature.ollivier_ricci_multilayer import (
    RicciBackendNotAvailable,
)

# Check if GraphRicciCurvature is available
try:
    from GraphRicciCurvature.OllivierRicci import OllivierRicci
    GRAPHRICCICURVATURE_AVAILABLE = True
except ImportError:
    GRAPHRICCICURVATURE_AVAILABLE = False


# Skip all tests if GraphRicciCurvature is not available
pytestmark = pytest.mark.skipif(
    not GRAPHRICCICURVATURE_AVAILABLE,
    reason="GraphRicciCurvature not installed"
)


@pytest.fixture
def simple_multilayer_network():
    """Create a simple multilayer network for testing."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add edges in two layers
    net.add_edges([
        ['A', 'layer1', 'B', 'layer1', 1],
        ['B', 'layer1', 'C', 'layer1', 1],
        ['C', 'layer1', 'D', 'layer1', 1],
        ['A', 'layer2', 'B', 'layer2', 1],
        ['B', 'layer2', 'D', 'layer2', 1],
    ], input_type="list")
    
    return net


@pytest.fixture
def karate_multilayer():
    """Create a multilayer network based on Karate club graph."""
    net = multinet.multi_layer_network(directed=False)
    
    # Create two layers with Karate club structure
    G = nx.karate_club_graph()
    
    # Layer 1: first half of edges
    edges_list = list(G.edges())
    mid = len(edges_list) // 2
    
    for u, v in edges_list[:mid]:
        net.add_edges([[u, 'layer1', v, 'layer1', 1]], input_type="list")
    
    # Layer 2: second half of edges
    for u, v in edges_list[mid:]:
        net.add_edges([[u, 'layer2', v, 'layer2', 1]], input_type="list")
    
    return net


class TestRicciBackendAvailability:
    """Test that RicciBackendNotAvailable exception works correctly."""
    
    def test_exception_message(self):
        """Test that the exception has a clear message."""
        exc = RicciBackendNotAvailable()
        assert "GraphRicciCurvature" in str(exc)
        assert "pip install" in str(exc)


class TestComputeOllivierRicciCore:
    """Test Ollivier-Ricci curvature computation on aggregated (core) networks."""
    
    def test_core_mode_basic(self, simple_multilayer_network):
        """Test basic curvature computation on core network."""
        net = simple_multilayer_network
        
        # Compute curvature on core network
        result = net.compute_ollivier_ricci(mode="core", inplace=True)
        
        # Check result structure
        assert "core" in result
        assert result["core"] is not None
        
        # Check that curvatures are computed
        # Note: result graph may be a simple Graph (not MultiGraph)
        edges_with_curvature = 0
        for u, v, data in result["core"].edges(data=True):
            if "ricciCurvature" in data:
                edges_with_curvature += 1
                # Curvature should be a number in a reasonable range
                assert isinstance(data["ricciCurvature"], (int, float))
        
        # At least some edges should have curvature
        assert edges_with_curvature > 0
    
    def test_core_mode_inplace_false(self, simple_multilayer_network):
        """Test that inplace=False doesn't modify the original network."""
        net = simple_multilayer_network
        
        # Get original edge count
        original_edges = list(net.core_network.edges(data=True))
        
        # Compute without modifying
        result = net.compute_ollivier_ricci(mode="core", inplace=False)
        
        # Original network should not have curvature attributes
        edges_with_curvature = sum(
            1 for u, v, data in net.core_network.edges(data=True)
            if "ricciCurvature" in data
        )
        assert edges_with_curvature == 0
        
        # Result should have curvatures
        result_edges_with_curvature = sum(
            1 for u, v, data in result["core"].edges(data=True)
            if "ricciCurvature" in data
        )
        assert result_edges_with_curvature > 0
    
    def test_core_mode_custom_params(self, simple_multilayer_network):
        """Test curvature computation with custom parameters."""
        net = simple_multilayer_network
        
        # Compute with custom alpha and attribute name
        result = net.compute_ollivier_ricci(
            mode="core",
            alpha=0.7,
            curvature_attr="myRicci",
            inplace=True
        )
        
        # Check that custom attribute is used
        edges_with_custom_attr = sum(
            1 for u, v, data in result["core"].edges(data=True)
            if "myRicci" in data
        )
        assert edges_with_custom_attr > 0


class TestComputeOllivierRicciLayers:
    """Test Ollivier-Ricci curvature computation on individual layers."""
    
    def test_layers_mode_all_layers(self, simple_multilayer_network):
        """Test curvature computation on all layers."""
        net = simple_multilayer_network
        
        # Compute on all layers
        result = net.compute_ollivier_ricci(mode="layers", inplace=True)
        
        # Check that we have results for both layers
        assert "layer1" in result
        assert "layer2" in result
        
        # Each layer should have curvatures
        for layer_id, G_layer in result.items():
            edges_with_curvature = sum(
                1 for u, v, data in G_layer.edges(data=True)
                if "ricciCurvature" in data
            )
            assert edges_with_curvature > 0
    
    def test_layers_mode_specific_layers(self, simple_multilayer_network):
        """Test curvature computation on specific layers only."""
        net = simple_multilayer_network
        
        # Compute only on layer1
        result = net.compute_ollivier_ricci(
            mode="layers",
            layers=["layer1"],
            inplace=False
        )
        
        # Should only have layer1 in result
        assert "layer1" in result
        assert "layer2" not in result
        
        # layer1 should have curvatures
        edges_with_curvature = sum(
            1 for u, v, data in result["layer1"].edges(data=True)
            if "ricciCurvature" in data
        )
        assert edges_with_curvature > 0
    
    def test_layers_mode_invalid_layer(self, simple_multilayer_network):
        """Test error handling for invalid layer identifiers."""
        net = simple_multilayer_network
        
        # Try to compute on non-existent layer
        with pytest.raises(ValueError, match="Invalid layer identifiers"):
            net.compute_ollivier_ricci(
                mode="layers",
                layers=["nonexistent_layer"]
            )


class TestComputeOllivierRicciSupra:
    """Test Ollivier-Ricci curvature computation on supra-graphs."""
    
    def test_supra_mode_basic(self, simple_multilayer_network):
        """Test curvature computation on supra-graph."""
        net = simple_multilayer_network
        
        # Compute on supra-graph
        result = net.compute_ollivier_ricci(mode="supra", inplace=False)
        
        # Check result structure
        assert "supra" in result
        G_supra = result["supra"]
        
        # Supra-graph should have nodes from both layers
        nodes = list(G_supra.nodes())
        layer1_nodes = [n for n in nodes if isinstance(n, tuple) and n[1] == "layer1"]
        layer2_nodes = [n for n in nodes if isinstance(n, tuple) and n[1] == "layer2"]
        assert len(layer1_nodes) > 0
        assert len(layer2_nodes) > 0
        
        # Should have inter-layer edges (coupling edges)
        has_interlayer_edge = False
        for u, v in G_supra.edges():
            if isinstance(u, tuple) and isinstance(v, tuple):
                if u[0] == v[0] and u[1] != v[1]:  # Same node, different layer
                    has_interlayer_edge = True
                    break
        assert has_interlayer_edge
        
        # Should have curvatures computed
        edges_with_curvature = sum(
            1 for u, v, data in G_supra.edges(data=True)
            if "ricciCurvature" in data
        )
        assert edges_with_curvature > 0
    
    def test_supra_mode_custom_interlayer_weight(self, simple_multilayer_network):
        """Test supra-graph with custom inter-layer weight."""
        net = simple_multilayer_network
        
        # Compute with custom inter-layer weight
        result = net.compute_ollivier_ricci(
            mode="supra",
            interlayer_weight=2.0,
            inplace=False
        )
        
        G_supra = result["supra"]
        
        # Check that inter-layer edges have the correct weight
        found_interlayer = False
        for u, v, data in G_supra.edges(data=True):
            if isinstance(u, tuple) and isinstance(v, tuple):
                if u[0] == v[0] and u[1] != v[1]:  # Inter-layer edge
                    assert data.get("weight") == 2.0
                    found_interlayer = True
        
        assert found_interlayer


class TestComputeOllivierRicciFlow:
    """Test Ollivier-Ricci flow computation."""
    
    def test_flow_core_mode(self, simple_multilayer_network):
        """Test Ricci flow on core network."""
        net = simple_multilayer_network
        
        # Get original edge weights from result since it might be converted to simple graph
        # Apply Ricci flow
        result = net.compute_ollivier_ricci_flow(
            mode="core",
            iterations=5,
            inplace=True
        )
        
        # Check that weights exist and flow has been applied
        edges_with_weight = 0
        edges_with_curvature = 0
        
        for u, v, data in result["core"].edges(data=True):
            if "weight" in data:
                edges_with_weight += 1
            if "ricciCurvature" in data:
                edges_with_curvature += 1
        
        # Edges should have weights and curvatures
        assert edges_with_weight > 0
        assert edges_with_curvature > 0
    
    def test_flow_layers_mode(self, simple_multilayer_network):
        """Test Ricci flow on individual layers."""
        net = simple_multilayer_network
        
        # Apply flow to all layers
        result = net.compute_ollivier_ricci_flow(
            mode="layers",
            iterations=3,
            inplace=False
        )
        
        # Should have results for both layers
        assert "layer1" in result
        assert "layer2" in result
        
        # Each layer should have modified weights and curvatures
        for layer_id, G_layer in result.items():
            edges_with_weight = sum(
                1 for u, v, data in G_layer.edges(data=True)
                if "weight" in data
            )
            edges_with_curvature = sum(
                1 for u, v, data in G_layer.edges(data=True)
                if "ricciCurvature" in data
            )
            assert edges_with_weight > 0
            assert edges_with_curvature > 0
    
    def test_flow_supra_mode(self, simple_multilayer_network):
        """Test Ricci flow on supra-graph."""
        net = simple_multilayer_network
        
        # Apply flow to supra-graph
        result = net.compute_ollivier_ricci_flow(
            mode="supra",
            iterations=5,
            method="OTD",
            inplace=False
        )
        
        # Check result
        assert "supra" in result
        G_supra = result["supra"]
        
        # Should have weights and curvatures
        edges_with_weight = sum(
            1 for u, v, data in G_supra.edges(data=True)
            if "weight" in data
        )
        edges_with_curvature = sum(
            1 for u, v, data in G_supra.edges(data=True)
            if "ricciCurvature" in data
        )
        assert edges_with_weight > 0
        assert edges_with_curvature > 0


class TestErrorHandling:
    """Test error handling and parameter validation."""
    
    def test_invalid_mode(self, simple_multilayer_network):
        """Test error for invalid mode parameter."""
        net = simple_multilayer_network
        
        with pytest.raises(ValueError, match="Invalid mode"):
            net.compute_ollivier_ricci(mode="invalid_mode")
        
        with pytest.raises(ValueError, match="Invalid mode"):
            net.compute_ollivier_ricci_flow(mode="invalid_mode")
    
    def test_empty_network(self):
        """Test error for uninitialized network."""
        net = multinet.multi_layer_network()
        
        with pytest.raises(ValueError, match="Core network is not initialized"):
            net.compute_ollivier_ricci(mode="core")
        
        with pytest.raises(ValueError, match="Core network is not initialized"):
            net.compute_ollivier_ricci_flow(mode="core")


class TestLargerNetwork:
    """Test on larger, more realistic networks."""
    
    def test_karate_multilayer_curvature(self, karate_multilayer):
        """Test curvature computation on Karate club multilayer network."""
        net = karate_multilayer
        
        # Compute on all modes
        result_core = net.compute_ollivier_ricci(mode="core", inplace=False)
        result_layers = net.compute_ollivier_ricci(mode="layers", inplace=False)
        result_supra = net.compute_ollivier_ricci(mode="supra", inplace=False)
        
        # All should have computed curvatures
        assert "core" in result_core
        assert "layer1" in result_layers
        assert "layer2" in result_layers
        assert "supra" in result_supra
        
        # Verify curvatures exist
        for G in [result_core["core"], result_layers["layer1"], 
                  result_layers["layer2"], result_supra["supra"]]:
            edges_with_curvature = sum(
                1 for u, v, data in G.edges(data=True)
                if "ricciCurvature" in data
            )
            assert edges_with_curvature > 0
    
    def test_karate_multilayer_flow(self, karate_multilayer):
        """Test Ricci flow on Karate club multilayer network."""
        net = karate_multilayer
        
        # Apply flow on core network
        result = net.compute_ollivier_ricci_flow(
            mode="core",
            iterations=10,
            inplace=False
        )
        
        G_flow = result["core"]
        
        # Verify that flow has been applied
        edges_with_modified_weights = 0
        edges_with_curvature = 0
        
        for u, v, data in G_flow.edges(data=True):
            if "weight" in data and data["weight"] != 1.0:
                edges_with_modified_weights += 1
            if "ricciCurvature" in data:
                edges_with_curvature += 1
        
        # Most edges should have been modified by flow
        assert edges_with_modified_weights > 0
        assert edges_with_curvature > 0


# Test for missing dependency handling
def test_missing_dependency():
    """Test that missing GraphRicciCurvature is handled gracefully."""
    # This test is conceptual - in practice, if GraphRicciCurvature is
    # installed, we can't really test the missing case without mocking.
    # The important thing is that the exception class exists and has
    # a clear message.
    exc = RicciBackendNotAvailable()
    assert "GraphRicciCurvature" in str(exc)
    assert "pip install GraphRicciCurvature" in str(exc)


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
