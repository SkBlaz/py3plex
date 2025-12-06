"""Tests for robustness centrality module.

This module tests the robustness-oriented centrality measures that quantify
how important nodes or layers are for network connectivity and dynamics.
"""

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.centrality import robustness_centrality


def build_chain_network() -> multinet.multi_layer_network:
    """Build a simple chain network where middle node is critical.
    
    Structure: a -- b -- c (in layer L0)
    Node b is a bridge: removing it disconnects a and c.
    """
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


def build_ring_network() -> multinet.multi_layer_network:
    """Build a ring network where all nodes are equally important.
    
    Structure: a -- b -- c -- a (in layer L0)
    """
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
        ["c", "L0", "a", "L0", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


def build_multilayer_network() -> multinet.multi_layer_network:
    """Build a two-layer network for layer robustness testing.
    
    Structure:
    - L0: a -- b -- c
    - L1: a -- b
    """
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
        ["a", "L1", "b", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


class TestRobustnessCentralityBasic:
    """Basic tests for robustness_centrality function."""

    def test_invalid_target(self):
        """Test that invalid target raises ValueError."""
        net = build_chain_network()
        with pytest.raises(ValueError, match="target must be"):
            robustness_centrality(net, target="invalid")

    def test_invalid_metric(self):
        """Test that invalid metric raises ValueError."""
        net = build_chain_network()
        with pytest.raises(ValueError, match="metric must be one of"):
            robustness_centrality(net, metric="invalid_metric")

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        net = build_chain_network()
        result = robustness_centrality(net, target="node", metric="giant_component")
        assert isinstance(result, dict)
        assert len(result) > 0


class TestNodeRobustness:
    """Tests for node-level robustness measurement."""

    def test_chain_giant_component(self):
        """Test that bridge node (b) has highest robustness in chain.
        
        In chain a--b--c:
        - Removing b: giant component shrinks from 3 to 1 (impact = 2)
        - Removing a or c: giant component shrinks from 3 to 2 (impact = 1)
        """
        net = build_chain_network()
        scores = robustness_centrality(
            net, target="node", metric="giant_component", seed=42
        )
        
        # Bridge node should have highest robustness
        assert scores[("b", "L0")] > scores[("a", "L0")]
        assert scores[("b", "L0")] > scores[("c", "L0")]
        
        # End nodes should have equal robustness
        assert abs(scores[("a", "L0")] - scores[("c", "L0")]) < 1e-9

    def test_ring_equal_importance(self):
        """Test that all nodes have equal robustness in ring.
        
        In ring a--b--c--a:
        - Removing any single node leaves 2 nodes connected
        - All should have equal robustness
        """
        net = build_ring_network()
        scores = robustness_centrality(
            net, target="node", metric="giant_component", seed=42
        )
        
        # All nodes should have equal robustness
        values = list(scores.values())
        assert abs(values[0] - values[1]) < 1e-9
        assert abs(values[1] - values[2]) < 1e-9

    def test_avg_shortest_path(self):
        """Test average shortest path metric.
        
        Removing a bridge node should increase average path length
        (or make it infinite if graph becomes disconnected).
        """
        net = build_chain_network()
        scores = robustness_centrality(
            net, target="node", metric="avg_shortest_path", seed=42
        )
        
        # Bridge node should have highest impact (path length increases most)
        # Note: sign is flipped because lower path length is better
        assert scores[("b", "L0")] > scores[("a", "L0")]
        assert scores[("b", "L0")] > scores[("c", "L0")]

    def test_sample_nodes(self):
        """Test that sample_nodes restricts which nodes are measured."""
        net = build_chain_network()
        
        # Only measure nodes a and b
        sample = [("a", "L0"), ("b", "L0")]
        scores = robustness_centrality(
            net, target="node", metric="giant_component", sample_nodes=sample
        )
        
        assert len(scores) == 2
        assert ("a", "L0") in scores
        assert ("b", "L0") in scores
        assert ("c", "L0") not in scores

    def test_empty_network(self):
        """Test handling of empty network."""
        # Create empty network by adding no edges
        net = multinet.multi_layer_network(directed=False, verbose=False)
        # Force initialization by attempting to add an empty edge list
        try:
            net.add_edges([], input_type="list")
        except:
            pass  # May fail, but that's ok
        
        scores = robustness_centrality(
            net, target="node", metric="giant_component", seed=42
        )
        
        assert len(scores) == 0


class TestLayerRobustness:
    """Tests for layer-level robustness measurement."""

    def test_layer_removal(self):
        """Test that layer removal works correctly."""
        net = build_multilayer_network()
        scores = robustness_centrality(
            net, target="layer", metric="giant_component", seed=42
        )
        
        # Both layers should be in results
        assert "L0" in scores
        assert "L1" in scores
        
        # L0 has more nodes, should have higher impact
        assert scores["L0"] > scores["L1"]

    def test_sample_layers(self):
        """Test that sample_layers restricts which layers are measured."""
        net = build_multilayer_network()
        
        scores = robustness_centrality(
            net, target="layer", metric="giant_component", 
            sample_layers=["L0"]
        )
        
        assert len(scores) == 1
        assert "L0" in scores
        assert "L1" not in scores


class TestDynamicsMetrics:
    """Tests for dynamics-based robustness metrics."""

    def test_sis_final_prevalence(self):
        """Test SIS prevalence metric.
        
        Note: Due to stochastic effects, removing a node can sometimes increase
        prevalence (e.g., by concentrating disease in a denser subgraph).
        So scores can be positive or negative.
        """
        net = build_chain_network()
        
        scores = robustness_centrality(
            net,
            target="node",
            metric="sis_final_prevalence",
            dynamics_params={"beta": 0.5, "mu": 0.1, "steps": 50},
            seed=42,
        )
        
        # All nodes should have finite scores
        assert all(isinstance(v, (int, float)) and not np.isnan(v) for v in scores.values())
        
        # Result should be deterministic with same seed
        scores2 = robustness_centrality(
            net,
            target="node",
            metric="sis_final_prevalence",
            dynamics_params={"beta": 0.5, "mu": 0.1, "steps": 50},
            seed=42,
        )
        
        for node in scores:
            assert abs(scores[node] - scores2[node]) < 1e-6

    def test_sir_final_size(self):
        """Test SIR final size metric.
        
        Removing a central node should reduce epidemic final size.
        """
        net = build_chain_network()
        
        scores = robustness_centrality(
            net,
            target="node",
            metric="sir_final_size",
            dynamics_params={"beta": 0.5, "gamma": 0.1, "steps": 50},
            seed=42,
        )
        
        # All nodes should have some impact
        assert all(v >= 0 for v in scores.values())
        
        # Bridge node might have higher impact in epidemic spread
        # (though this depends on the specific dynamics)
        assert isinstance(scores[("b", "L0")], float)

    def test_dynamics_deterministic_with_seed(self):
        """Test that dynamics metrics are deterministic with fixed seed."""
        net = build_ring_network()
        
        # Run twice with same seed
        scores1 = robustness_centrality(
            net,
            target="node",
            metric="sis_final_prevalence",
            dynamics_params={"beta": 0.3, "mu": 0.1, "steps": 30},
            seed=123,
        )
        
        scores2 = robustness_centrality(
            net,
            target="node",
            metric="sis_final_prevalence",
            dynamics_params={"beta": 0.3, "mu": 0.1, "steps": 30},
            seed=123,
        )
        
        # Results should be identical
        for node in scores1:
            assert abs(scores1[node] - scores2[node]) < 1e-6

    def test_dynamics_different_with_different_seed(self):
        """Test that dynamics metrics differ with different seeds."""
        net = build_ring_network()
        
        # Run with different seeds
        scores1 = robustness_centrality(
            net,
            target="node",
            metric="sis_final_prevalence",
            dynamics_params={"beta": 0.3, "mu": 0.1, "steps": 30},
            seed=123,
        )
        
        scores2 = robustness_centrality(
            net,
            target="node",
            metric="sis_final_prevalence",
            dynamics_params={"beta": 0.3, "mu": 0.1, "steps": 30},
            seed=456,
        )
        
        # At least one result should be different (with very high probability)
        # Due to stochastic nature, they might occasionally be close but not identical
        all_same = all(
            abs(scores1[node] - scores2[node]) < 1e-9 for node in scores1
        )
        assert not all_same, "Scores should differ with different seeds"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_single_node_network(self):
        """Test network with single node."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        # Add a single isolated node by creating and then removing an edge
        edges = [["a", "L0", "b", "L0", 1.0]]
        net.add_edges(edges, input_type="list")
        # Now remove node b to leave only node a
        net.core_network.remove_node(("b", "L0"))
        
        scores = robustness_centrality(
            net, target="node", metric="giant_component", seed=42
        )
        
        # Single node removal should reduce component from 1 to 0
        assert scores[("a", "L0")] == 1.0

    def test_disconnected_network(self):
        """Test network with multiple disconnected components."""
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = [
            ["a", "L0", "b", "L0", 1.0],
            ["c", "L0", "d", "L0", 1.0],  # Separate component
        ]
        net.add_edges(edges, input_type="list")
        
        scores = robustness_centrality(
            net, target="node", metric="giant_component", seed=42
        )
        
        # Baseline giant component is 2 (either component)
        # Removing any node still leaves giant component of 2 (the other component)
        # So robustness should be 0 for all nodes
        assert all(abs(score - 0.0) < 1e-9 for score in scores.values())

    def test_default_dynamics_params(self):
        """Test that dynamics metrics work with default parameters."""
        net = build_chain_network()
        
        # Should work without explicit dynamics_params
        scores = robustness_centrality(
            net, target="node", metric="sis_final_prevalence", seed=42
        )
        
        assert len(scores) == 3
        assert all(isinstance(v, float) for v in scores.values())


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_multilayer_node_and_layer(self):
        """Test both node and layer robustness on same network."""
        net = build_multilayer_network()
        
        node_scores = robustness_centrality(
            net, target="node", metric="giant_component", seed=42
        )
        
        layer_scores = robustness_centrality(
            net, target="layer", metric="giant_component", seed=42
        )
        
        assert len(node_scores) > 0
        assert len(layer_scores) > 0
        
        # Nodes and layers are different types of targets
        assert set(node_scores.keys()).isdisjoint(set(layer_scores.keys()))

    def test_all_metrics_on_same_network(self):
        """Test all metrics produce valid results on same network."""
        net = build_chain_network()
        
        metrics = [
            "giant_component",
            "avg_shortest_path",
            "sis_final_prevalence",
            "sir_final_size",
        ]
        
        for metric in metrics:
            scores = robustness_centrality(
                net,
                target="node",
                metric=metric,
                dynamics_params={"steps": 20},  # Short for speed
                seed=42,
            )
            
            assert len(scores) == 3, f"Failed for metric {metric}"
            assert all(isinstance(v, (int, float)) for v in scores.values())

    def test_larger_network_performance(self):
        """Test performance on slightly larger network."""
        # Build a larger network (grid-like)
        net = multinet.multi_layer_network(directed=False, verbose=False)
        edges = []
        
        # Create a 4x4 grid in layer L0
        for i in range(4):
            for j in range(4):
                node = f"n{i}{j}"
                # Connect to right neighbor
                if j < 3:
                    edges.append([node, "L0", f"n{i}{j+1}", "L0", 1.0])
                # Connect to bottom neighbor
                if i < 3:
                    edges.append([node, "L0", f"n{i+1}{j}", "L0", 1.0])
        
        net.add_edges(edges, input_type="list")
        
        # Sample a few nodes for speed
        sample = [("n00", "L0"), ("n11", "L0"), ("n22", "L0"), ("n33", "L0")]
        
        scores = robustness_centrality(
            net,
            target="node",
            metric="giant_component",
            sample_nodes=sample,
            seed=42,
        )
        
        assert len(scores) == 4
        
        # Corner nodes should have lower impact than central nodes
        # n11 and n22 are more central than n00 and n33
        assert scores[("n11", "L0")] >= scores[("n00", "L0")]
        assert scores[("n22", "L0")] >= scores[("n33", "L0")]
