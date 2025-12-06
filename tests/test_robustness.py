"""Tests for the robustness module.

This module tests perturbation classes and experiment functions
for robustness analysis on multilayer networks.
"""

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.robustness import (
    EdgeDrop,
    EdgeAdd,
    NodeDrop,
    compose,
    estimate_metric_distribution,
    centrality_robustness,
)


def build_small_network() -> multinet.multi_layer_network:
    """Build a small test multilayer network."""
    mnet = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
        ["c", "L0", "a", "L0", 1.0],
        ["a", "L1", "b", "L1", 1.0],
    ]
    mnet.add_edges(edges, input_type="list")
    return mnet


def count_edges(net: multinet.multi_layer_network) -> int:
    """Count edges in a network."""
    return sum(1 for _ in net.get_edges())


def count_nodes(net: multinet.multi_layer_network) -> int:
    """Count nodes in a network."""
    return sum(1 for _ in net.get_nodes())


class TestEdgeDrop:
    """Tests for EdgeDrop perturbation."""

    def test_edge_drop_p_zero(self):
        """p=0.0: no edges should be dropped."""
        net = build_small_network()
        rng = np.random.default_rng(0)

        e0 = EdgeDrop(p=0.0)
        net0 = e0.apply(net, rng)
        assert count_edges(net0) == count_edges(net)

    def test_edge_drop_p_one(self):
        """p=1.0: all edges should be dropped."""
        net = build_small_network()
        rng = np.random.default_rng(0)

        e1 = EdgeDrop(p=1.0)
        net1 = e1.apply(net, rng)
        assert count_edges(net1) == 0

    def test_edge_drop_preserves_original(self):
        """Verify that the original network is not mutated."""
        net = build_small_network()
        original_edge_count = count_edges(net)
        rng = np.random.default_rng(42)

        e = EdgeDrop(p=0.5)
        _ = e.apply(net, rng)

        assert count_edges(net) == original_edge_count

    def test_edge_drop_layer_filter(self):
        """Test edge drop with layer filtering."""
        net = build_small_network()
        rng = np.random.default_rng(42)

        # Drop all edges from L0 only
        e = EdgeDrop(p=1.0, layer="L0")
        net1 = e.apply(net, rng)

        # Should only have L1 edges remaining (1 edge)
        edges = list(net1.get_edges())
        l1_edges = [e for e in edges if e[0][1] == "L1" and e[1][1] == "L1"]
        assert len(l1_edges) == 1

    def test_edge_drop_invalid_p(self):
        """Test that invalid p values raise ValueError."""
        with pytest.raises(ValueError):
            EdgeDrop(p=-0.1)
        with pytest.raises(ValueError):
            EdgeDrop(p=1.5)


class TestNodeDrop:
    """Tests for NodeDrop perturbation."""

    def test_node_drop_p_zero(self):
        """p=0.0: no nodes should be dropped."""
        net = build_small_network()
        rng = np.random.default_rng(0)

        d0 = NodeDrop(p=0.0)
        net0 = d0.apply(net, rng)
        assert count_nodes(net0) == count_nodes(net)

    def test_node_drop_p_one(self):
        """p=1.0: all nodes should be dropped."""
        net = build_small_network()
        rng = np.random.default_rng(0)

        d1 = NodeDrop(p=1.0)
        net1 = d1.apply(net, rng)
        assert count_nodes(net1) == 0
        assert count_edges(net1) == 0

    def test_node_drop_preserves_original(self):
        """Verify that the original network is not mutated."""
        net = build_small_network()
        original_node_count = count_nodes(net)
        rng = np.random.default_rng(42)

        d = NodeDrop(p=0.5)
        _ = d.apply(net, rng)

        assert count_nodes(net) == original_node_count

    def test_node_drop_invalid_p(self):
        """Test that invalid p values raise ValueError."""
        with pytest.raises(ValueError):
            NodeDrop(p=-0.1)
        with pytest.raises(ValueError):
            NodeDrop(p=1.5)


class TestEdgeAdd:
    """Tests for EdgeAdd perturbation."""

    def test_edge_add_p_zero(self):
        """p=0.0: no edges should be added."""
        net = build_small_network()
        rng = np.random.default_rng(0)
        original_count = count_edges(net)

        ea = EdgeAdd(p=0.0)
        net0 = ea.apply(net, rng)
        assert count_edges(net0) == original_count

    def test_edge_add_preserves_original(self):
        """Verify that the original network is not mutated."""
        net = build_small_network()
        original_edge_count = count_edges(net)
        rng = np.random.default_rng(42)

        ea = EdgeAdd(p=0.5)
        _ = ea.apply(net, rng)

        assert count_edges(net) == original_edge_count

    def test_edge_add_invalid_p(self):
        """Test that invalid p values raise ValueError."""
        with pytest.raises(ValueError):
            EdgeAdd(p=-0.1)
        with pytest.raises(ValueError):
            EdgeAdd(p=1.5)


class TestCompose:
    """Tests for compose function."""

    def test_compose_single(self):
        """Composing a single perturbation should work."""
        net = build_small_network()
        rng = np.random.default_rng(0)

        perturb = compose(EdgeDrop(p=1.0))
        net1 = perturb.apply(net, rng)
        assert count_edges(net1) == 0

    def test_compose_multiple(self):
        """Composing multiple perturbations should apply in sequence."""
        net = build_small_network()
        rng = np.random.default_rng(0)

        perturb = compose(EdgeDrop(p=0.0), NodeDrop(p=0.0))
        net1 = perturb.apply(net, rng)
        assert count_edges(net1) == count_edges(net)
        assert count_nodes(net1) == count_nodes(net)

    def test_compose_drop_then_drop(self):
        """Test that edge drop then node drop works correctly."""
        net = build_small_network()
        rng = np.random.default_rng(42)

        perturb = compose(EdgeDrop(p=1.0), NodeDrop(p=0.0))
        net1 = perturb.apply(net, rng)
        # All edges dropped but nodes preserved
        assert count_edges(net1) == 0
        assert count_nodes(net1) == count_nodes(net)


class TestEstimateMetricDistribution:
    """Tests for estimate_metric_distribution function."""

    def test_scalar_metric(self):
        """Test with a scalar-returning metric function."""
        net = build_small_network()

        def edge_count_metric(n):
            return float(count_edges(n))

        result = estimate_metric_distribution(
            network=net,
            metric_fn=edge_count_metric,
            perturbation=EdgeDrop(p=0.5),
            n_samples=10,
            random_state=123,
        )

        assert "samples" in result
        assert "summary" in result
        assert len(result["samples"]) == 10
        summary = result["summary"]
        assert all(k in summary for k in ("mean", "std", "ci95"))

    def test_dict_metric(self):
        """Test with a dict-returning metric function."""
        net = build_small_network()

        def multi_metric(n):
            return {
                "edges": float(count_edges(n)),
                "nodes": float(count_nodes(n)),
            }

        result = estimate_metric_distribution(
            network=net,
            metric_fn=multi_metric,
            perturbation=EdgeDrop(p=0.5),
            n_samples=10,
            random_state=123,
        )

        assert "samples" in result
        assert "summary" in result
        assert len(result["samples"]) == 10
        summary = result["summary"]
        assert "edges" in summary
        assert "nodes" in summary
        assert all(k in summary["edges"] for k in ("mean", "std", "ci95"))

    def test_reproducibility(self):
        """Test that random_state provides reproducibility."""
        net = build_small_network()

        def edge_count_metric(n):
            return float(count_edges(n))

        result1 = estimate_metric_distribution(
            network=net,
            metric_fn=edge_count_metric,
            perturbation=EdgeDrop(p=0.5),
            n_samples=5,
            random_state=42,
        )

        result2 = estimate_metric_distribution(
            network=net,
            metric_fn=edge_count_metric,
            perturbation=EdgeDrop(p=0.5),
            n_samples=5,
            random_state=42,
        )

        assert result1["samples"] == result2["samples"]

    def test_invalid_n_samples(self):
        """Test that invalid n_samples raises ValueError."""
        net = build_small_network()

        with pytest.raises(ValueError):
            estimate_metric_distribution(
                network=net,
                metric_fn=lambda n: 0.0,
                perturbation=EdgeDrop(p=0.5),
                n_samples=0,
            )


class TestCentralityRobustness:
    """Tests for centrality_robustness function."""

    def simple_degree_centrality(self, net):
        """Compute naive degree centrality across all layers."""
        degrees = {}
        for node in net.get_nodes():
            degrees[node] = 0.0

        for edge in net.get_edges():
            u, v = edge[0], edge[1]
            if u in degrees:
                degrees[u] += 1.0
            if v in degrees:
                degrees[v] += 1.0
        return degrees

    def test_no_perturbation(self):
        """Test with p=0.0 perturbation so graph doesn't change."""
        net = build_small_network()

        result = centrality_robustness(
            network=net,
            centrality_fn=self.simple_degree_centrality,
            perturbation=EdgeDrop(p=0.0),
            n_samples=5,
            random_state=0,
        )

        assert "node_stats" in result
        assert "rank_stability" in result
        stats = result["node_stats"]

        # Mean centrality should equal baseline (within tiny tolerance)
        baseline = self.simple_degree_centrality(net)
        for node, s in stats.items():
            assert abs(s["mean"] - baseline[node]) < 1e-9

    def test_centrality_robustness_structure(self):
        """Test the structure of the returned result."""
        net = build_small_network()

        result = centrality_robustness(
            network=net,
            centrality_fn=self.simple_degree_centrality,
            perturbation=EdgeDrop(p=0.5),
            n_samples=5,
            random_state=0,
        )

        assert "samples" in result
        assert "node_stats" in result
        assert "rank_stability" in result
        assert len(result["samples"]) == 5

        for node, stats in result["node_stats"].items():
            assert "mean" in stats
            assert "std" in stats

        rank_stability = result["rank_stability"]
        assert "kendall_tau_mean" in rank_stability
        assert "kendall_tau_std" in rank_stability

    def test_invalid_n_samples(self):
        """Test that invalid n_samples raises ValueError."""
        net = build_small_network()

        with pytest.raises(ValueError):
            centrality_robustness(
                network=net,
                centrality_fn=self.simple_degree_centrality,
                perturbation=EdgeDrop(p=0.5),
                n_samples=0,
            )


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_full_workflow(self):
        """Test a full workflow as described in the docstrings."""
        net = build_small_network()

        perturb = compose(EdgeDrop(p=0.1), NodeDrop(p=0.05))

        result = estimate_metric_distribution(
            network=net,
            metric_fn=lambda n: float(count_edges(n)),
            perturbation=perturb,
            n_samples=20,
            random_state=42,
        )

        assert "samples" in result
        assert "summary" in result
        assert len(result["samples"]) == 20
