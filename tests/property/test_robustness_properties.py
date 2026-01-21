"""Property-based tests for the robustness module.

This module tests invariants and properties of perturbation classes
(EdgeDrop, NodeDrop, EdgeAdd, compose) and experiment functions
(estimate_metric_distribution, centrality_robustness).
"""

import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings

from py3plex.core import multinet
from py3plex.robustness import (
    EdgeDrop,
    EdgeAdd,
    NodeDrop,
    compose,
    estimate_metric_distribution,
    centrality_robustness,
)

from .strategies import (
    probabilities,
    layer_labels,
    node_names,
)


# ============================================================================
# Helper functions
# ============================================================================


def count_edges(net: multinet.multi_layer_network) -> int:
    """Count edges in a network."""
    return sum(1 for _ in net.get_edges())


def count_nodes(net: multinet.multi_layer_network) -> int:
    """Count nodes in a network."""
    return sum(1 for _ in net.get_nodes())


def build_multilayer_network(
    num_nodes: int = 4,
    num_layers: int = 2,
    edges_per_layer: int = 3,
) -> multinet.multi_layer_network:
    """Build a test multilayer network with specified structure."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = []
    layers = [f"L{i}" for i in range(num_layers)]

    for layer in layers:
        for i in range(min(edges_per_layer, num_nodes - 1)):
            edges.append([f"n{i}", layer, f"n{i+1}", layer, 1.0])

    if edges:
        net.add_edges(edges, input_type="list")
    return net


# ============================================================================
# EdgeDrop Properties
# ============================================================================


class TestEdgeDropProperties:
    """Property-based tests for EdgeDrop perturbation."""

    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    @settings(max_examples=3)
    def test_edge_drop_preserves_original_network(self, p: float):
        """EdgeDrop must not mutate the original network."""
        net = build_multilayer_network()
        original_edge_count = count_edges(net)
        original_node_count = count_nodes(net)
        rng = np.random.default_rng(42)

        edge_drop = EdgeDrop(p=p)
        _ = edge_drop.apply(net, rng)

        assert count_edges(net) == original_edge_count
        assert count_nodes(net) == original_node_count

    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    @settings(max_examples=3)
    def test_edge_drop_output_edge_count_leq_input(self, p: float):
        """EdgeDrop output should have at most as many edges as input."""
        net = build_multilayer_network()
        original_edge_count = count_edges(net)
        rng = np.random.default_rng(42)

        edge_drop = EdgeDrop(p=p)
        perturbed = edge_drop.apply(net, rng)

        assert count_edges(perturbed) <= original_edge_count

    def test_edge_drop_p_zero_no_change(self):
        """EdgeDrop with p=0.0 should not drop any edges."""
        net = build_multilayer_network()
        original_edge_count = count_edges(net)
        rng = np.random.default_rng(42)

        edge_drop = EdgeDrop(p=0.0)
        perturbed = edge_drop.apply(net, rng)

        assert count_edges(perturbed) == original_edge_count

    def test_edge_drop_p_one_removes_all_edges(self):
        """EdgeDrop with p=1.0 should remove all edges."""
        net = build_multilayer_network()
        rng = np.random.default_rng(42)

        edge_drop = EdgeDrop(p=1.0)
        perturbed = edge_drop.apply(net, rng)

        assert count_edges(perturbed) == 0

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        st.integers(min_value=0, max_value=1000),
    )
    @settings(max_examples=3)
    def test_edge_drop_reproducibility(self, p: float, seed: int):
        """EdgeDrop should be reproducible with same seed."""
        net = build_multilayer_network()

        rng1 = np.random.default_rng(seed)
        rng2 = np.random.default_rng(seed)

        edge_drop = EdgeDrop(p=p)
        perturbed1 = edge_drop.apply(net, rng1)
        perturbed2 = edge_drop.apply(net, rng2)

        assert count_edges(perturbed1) == count_edges(perturbed2)

    @given(st.floats(min_value=-10.0, max_value=-0.01, allow_nan=False))
    def test_edge_drop_rejects_negative_p(self, p: float):
        """EdgeDrop should reject negative probability values."""
        with pytest.raises(ValueError):
            EdgeDrop(p=p)

    @given(st.floats(min_value=1.01, max_value=10.0, allow_nan=False))
    def test_edge_drop_rejects_p_greater_than_one(self, p: float):
        """EdgeDrop should reject probability values > 1."""
        with pytest.raises(ValueError):
            EdgeDrop(p=p)


# ============================================================================
# NodeDrop Properties
# ============================================================================


class TestNodeDropProperties:
    """Property-based tests for NodeDrop perturbation."""

    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    @settings(max_examples=3)
    def test_node_drop_preserves_original_network(self, p: float):
        """NodeDrop must not mutate the original network."""
        net = build_multilayer_network()
        original_edge_count = count_edges(net)
        original_node_count = count_nodes(net)
        rng = np.random.default_rng(42)

        node_drop = NodeDrop(p=p)
        _ = node_drop.apply(net, rng)

        assert count_edges(net) == original_edge_count
        assert count_nodes(net) == original_node_count

    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    @settings(max_examples=3)
    def test_node_drop_output_node_count_leq_input(self, p: float):
        """NodeDrop output should have at most as many nodes as input."""
        net = build_multilayer_network()
        original_node_count = count_nodes(net)
        rng = np.random.default_rng(42)

        node_drop = NodeDrop(p=p)
        perturbed = node_drop.apply(net, rng)

        assert count_nodes(perturbed) <= original_node_count

    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    @settings(max_examples=3)
    def test_node_drop_output_edge_count_leq_input(self, p: float):
        """NodeDrop output should have at most as many edges as input."""
        net = build_multilayer_network()
        original_edge_count = count_edges(net)
        rng = np.random.default_rng(42)

        node_drop = NodeDrop(p=p)
        perturbed = node_drop.apply(net, rng)

        assert count_edges(perturbed) <= original_edge_count

    def test_node_drop_p_zero_no_change(self):
        """NodeDrop with p=0.0 should not drop any nodes."""
        net = build_multilayer_network()
        original_node_count = count_nodes(net)
        rng = np.random.default_rng(42)

        node_drop = NodeDrop(p=0.0)
        perturbed = node_drop.apply(net, rng)

        assert count_nodes(perturbed) == original_node_count

    def test_node_drop_p_one_removes_all(self):
        """NodeDrop with p=1.0 should remove all nodes and edges."""
        net = build_multilayer_network()
        rng = np.random.default_rng(42)

        node_drop = NodeDrop(p=1.0)
        perturbed = node_drop.apply(net, rng)

        assert count_nodes(perturbed) == 0
        assert count_edges(perturbed) == 0

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        st.integers(min_value=0, max_value=1000),
    )
    @settings(max_examples=3)
    def test_node_drop_reproducibility(self, p: float, seed: int):
        """NodeDrop should be reproducible with same seed."""
        net = build_multilayer_network()

        rng1 = np.random.default_rng(seed)
        rng2 = np.random.default_rng(seed)

        node_drop = NodeDrop(p=p)
        perturbed1 = node_drop.apply(net, rng1)
        perturbed2 = node_drop.apply(net, rng2)

        assert count_nodes(perturbed1) == count_nodes(perturbed2)
        assert count_edges(perturbed1) == count_edges(perturbed2)


# ============================================================================
# EdgeAdd Properties
# ============================================================================


class TestEdgeAddProperties:
    """Property-based tests for EdgeAdd perturbation."""

    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    @settings(max_examples=3)
    def test_edge_add_preserves_original_network(self, p: float):
        """EdgeAdd must not mutate the original network."""
        net = build_multilayer_network()
        original_edge_count = count_edges(net)
        original_node_count = count_nodes(net)
        rng = np.random.default_rng(42)

        edge_add = EdgeAdd(p=p)
        _ = edge_add.apply(net, rng)

        assert count_edges(net) == original_edge_count
        assert count_nodes(net) == original_node_count

    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    @settings(max_examples=3)
    def test_edge_add_output_edge_count_geq_input(self, p: float):
        """EdgeAdd output should have at least as many edges as input."""
        net = build_multilayer_network()
        original_edge_count = count_edges(net)
        rng = np.random.default_rng(42)

        edge_add = EdgeAdd(p=p)
        perturbed = edge_add.apply(net, rng)

        assert count_edges(perturbed) >= original_edge_count

    def test_edge_add_p_zero_no_change(self):
        """EdgeAdd with p=0.0 should not add any edges."""
        net = build_multilayer_network()
        original_edge_count = count_edges(net)
        rng = np.random.default_rng(42)

        edge_add = EdgeAdd(p=0.0)
        perturbed = edge_add.apply(net, rng)

        assert count_edges(perturbed) == original_edge_count

    @given(st.floats(min_value=-10.0, max_value=-0.01, allow_nan=False))
    def test_edge_add_rejects_negative_p(self, p: float):
        """EdgeAdd should reject negative probability values."""
        with pytest.raises(ValueError):
            EdgeAdd(p=p)


# ============================================================================
# Compose Properties
# ============================================================================


class TestComposeProperties:
    """Property-based tests for compose function."""

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=3)
    def test_compose_preserves_original_network(self, p1: float, p2: float):
        """Composed perturbations must not mutate the original network."""
        net = build_multilayer_network()
        original_edge_count = count_edges(net)
        original_node_count = count_nodes(net)
        rng = np.random.default_rng(42)

        composed = compose(EdgeDrop(p=p1), NodeDrop(p=p2))
        _ = composed.apply(net, rng)

        assert count_edges(net) == original_edge_count
        assert count_nodes(net) == original_node_count

    def test_compose_identity(self):
        """Composing p=0.0 perturbations should preserve the network."""
        net = build_multilayer_network()
        original_edge_count = count_edges(net)
        original_node_count = count_nodes(net)
        rng = np.random.default_rng(42)

        composed = compose(EdgeDrop(p=0.0), NodeDrop(p=0.0))
        perturbed = composed.apply(net, rng)

        assert count_edges(perturbed) == original_edge_count
        assert count_nodes(perturbed) == original_node_count

    @given(st.integers(min_value=1, max_value=5))
    @settings(max_examples=3)
    def test_compose_chain_length(self, num_perturbations: int):
        """Composing multiple perturbations should work."""
        net = build_multilayer_network()
        rng = np.random.default_rng(42)

        perturbations = [EdgeDrop(p=0.0) for _ in range(num_perturbations)]
        composed = compose(*perturbations)
        perturbed = composed.apply(net, rng)

        # With p=0, network should be unchanged
        assert count_edges(perturbed) == count_edges(net)


# ============================================================================
# estimate_metric_distribution Properties
# ============================================================================


class TestEstimateMetricDistributionProperties:
    """Property-based tests for estimate_metric_distribution function."""

    @given(st.integers(min_value=1, max_value=20))
    @settings(max_examples=3)
    def test_samples_count_equals_n_samples(self, n_samples: int):
        """Number of samples should equal n_samples parameter."""
        net = build_multilayer_network()

        def metric_fn(n):
            return float(count_edges(n))

        result = estimate_metric_distribution(
            network=net,
            metric_fn=metric_fn,
            perturbation=EdgeDrop(p=0.5),
            n_samples=n_samples,
            random_state=42,
        )

        assert len(result["samples"]) == n_samples

    @given(st.integers(min_value=1, max_value=20))
    @settings(max_examples=3)
    def test_summary_contains_required_keys(self, n_samples: int):
        """Summary should contain mean, std, and ci95."""
        net = build_multilayer_network()

        def metric_fn(n):
            return float(count_edges(n))

        result = estimate_metric_distribution(
            network=net,
            metric_fn=metric_fn,
            perturbation=EdgeDrop(p=0.5),
            n_samples=n_samples,
            random_state=42,
        )

        assert "mean" in result["summary"]
        assert "std" in result["summary"]
        assert "ci95" in result["summary"]

    @given(st.integers(min_value=0, max_value=1000))
    @settings(max_examples=3)
    def test_reproducibility_with_random_state(self, seed: int):
        """Results should be reproducible with same random_state."""
        net = build_multilayer_network()

        def metric_fn(n):
            return float(count_edges(n))

        result1 = estimate_metric_distribution(
            network=net,
            metric_fn=metric_fn,
            perturbation=EdgeDrop(p=0.5),
            n_samples=5,
            random_state=seed,
        )

        result2 = estimate_metric_distribution(
            network=net,
            metric_fn=metric_fn,
            perturbation=EdgeDrop(p=0.5),
            n_samples=5,
            random_state=seed,
        )

        assert result1["samples"] == result2["samples"]

    @given(st.integers(min_value=-100, max_value=0))
    def test_rejects_invalid_n_samples(self, n_samples: int):
        """Should reject n_samples <= 0."""
        net = build_multilayer_network()

        def metric_fn(n):
            return float(count_edges(n))

        with pytest.raises(ValueError):
            estimate_metric_distribution(
                network=net,
                metric_fn=metric_fn,
                perturbation=EdgeDrop(p=0.5),
                n_samples=n_samples,
            )

    def test_dict_metric_preserves_keys(self):
        """Dict-returning metric should have all keys in summary."""
        net = build_multilayer_network()

        def multi_metric(n):
            return {
                "edges": float(count_edges(n)),
                "nodes": float(count_nodes(n)),
            }

        result = estimate_metric_distribution(
            network=net,
            metric_fn=multi_metric,
            perturbation=EdgeDrop(p=0.5),
            n_samples=5,
            random_state=42,
        )

        assert "edges" in result["summary"]
        assert "nodes" in result["summary"]


# ============================================================================
# centrality_robustness Properties
# ============================================================================


class TestCentralityRobustnessProperties:
    """Property-based tests for centrality_robustness function."""

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

    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=3)
    def test_samples_count_equals_n_samples(self, n_samples: int):
        """Number of samples should equal n_samples parameter."""
        net = build_multilayer_network()

        result = centrality_robustness(
            network=net,
            centrality_fn=self.simple_degree_centrality,
            perturbation=EdgeDrop(p=0.5),
            n_samples=n_samples,
            random_state=42,
        )

        assert len(result["samples"]) == n_samples

    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=3)
    def test_result_contains_required_keys(self, n_samples: int):
        """Result should contain samples, node_stats, and rank_stability."""
        net = build_multilayer_network()

        result = centrality_robustness(
            network=net,
            centrality_fn=self.simple_degree_centrality,
            perturbation=EdgeDrop(p=0.5),
            n_samples=n_samples,
            random_state=42,
        )

        assert "samples" in result
        assert "node_stats" in result
        assert "rank_stability" in result

    @given(st.integers(min_value=0, max_value=1000))
    @settings(max_examples=3)
    def test_reproducibility_with_random_state(self, seed: int):
        """Results should be reproducible with same random_state."""
        net = build_multilayer_network()

        result1 = centrality_robustness(
            network=net,
            centrality_fn=self.simple_degree_centrality,
            perturbation=EdgeDrop(p=0.5),
            n_samples=3,
            random_state=seed,
        )

        result2 = centrality_robustness(
            network=net,
            centrality_fn=self.simple_degree_centrality,
            perturbation=EdgeDrop(p=0.5),
            n_samples=3,
            random_state=seed,
        )

        # Check that samples have the same keys
        assert set(result1["node_stats"].keys()) == set(result2["node_stats"].keys())

    def test_no_perturbation_stable_centrality(self):
        """With p=0.0, centrality values should be stable."""
        net = build_multilayer_network()

        result = centrality_robustness(
            network=net,
            centrality_fn=self.simple_degree_centrality,
            perturbation=EdgeDrop(p=0.0),
            n_samples=5,
            random_state=42,
        )

        # Standard deviation should be zero when no perturbation
        for node, stats in result["node_stats"].items():
            assert stats["std"] < 1e-9

    @given(st.integers(min_value=-100, max_value=0))
    def test_rejects_invalid_n_samples(self, n_samples: int):
        """Should reject n_samples <= 0."""
        net = build_multilayer_network()

        with pytest.raises(ValueError):
            centrality_robustness(
                network=net,
                centrality_fn=self.simple_degree_centrality,
                perturbation=EdgeDrop(p=0.5),
                n_samples=n_samples,
            )

