"""Property-based tests for the nullmodels module.

This module tests invariants and properties of null model generation
using hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import numpy as np

from py3plex.core import multinet
from py3plex.nullmodels import (
    generate_null_model,
    configuration_model,
    erdos_renyi_model,
    layer_shuffle_model,
    edge_swap_model,
    NullModelResult,
)


# ============================================================================
# Helper functions
# ============================================================================


def build_test_network(
    num_nodes: int = 4,
    num_layers: int = 2,
    edges_per_layer: int = 3,
) -> multinet.multi_layer_network:
    """Build a test multilayer network for null model testing."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = []
    layers = [f"L{i}" for i in range(num_layers)]

    for layer in layers:
        for i in range(min(edges_per_layer, num_nodes - 1)):
            edges.append([f"n{i}", layer, f"n{i+1}", layer, 1.0])

    if edges:
        net.add_edges(edges, input_type="list")
    return net


def count_nodes(net: multinet.multi_layer_network) -> int:
    """Count nodes in a network."""
    return sum(1 for _ in net.get_nodes())


def count_edges(net: multinet.multi_layer_network) -> int:
    """Count edges in a network."""
    return sum(1 for _ in net.get_edges())


# ============================================================================
# Configuration Model Properties
# ============================================================================


class TestConfigurationModelProperties:
    """Property-based tests for configuration_model."""

    @given(st.integers(min_value=42, max_value=9999))
    @settings(max_examples=3)
    def test_configuration_model_preserves_node_count(self, seed: int):
        """Configuration model must preserve node count."""
        net = build_test_network()
        original_count = count_nodes(net)
        
        random_net = configuration_model(net, seed=seed)
        assert count_nodes(random_net) == original_count

    @given(st.integers(min_value=42, max_value=9999))
    @settings(max_examples=3)
    def test_configuration_model_does_not_mutate_original(self, seed: int):
        """Configuration model must not mutate the original network."""
        net = build_test_network()
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        _ = configuration_model(net, seed=seed)
        
        assert count_nodes(net) == original_nodes
        assert count_edges(net) == original_edges

    def test_configuration_model_with_seed_is_reproducible(self):
        """Configuration model with same seed should be reproducible."""
        net = build_test_network()
        
        net1 = configuration_model(net, seed=12345)
        net2 = configuration_model(net, seed=12345)
        
        # Should produce same number of edges (degree sequence preserved)
        assert count_edges(net1) == count_edges(net2)


# ============================================================================
# Erdős-Rényi Model Properties
# ============================================================================


class TestErdosRenyiModelProperties:
    """Property-based tests for erdos_renyi_model."""

    @given(st.integers(min_value=42, max_value=9999))
    @settings(max_examples=3)
    def test_erdos_renyi_preserves_node_count(self, seed: int):
        """Erdős-Rényi model must preserve node count."""
        net = build_test_network()
        original_count = count_nodes(net)
        
        random_net = erdos_renyi_model(net, seed=seed)
        assert count_nodes(random_net) == original_count

    @given(st.integers(min_value=42, max_value=9999))
    @settings(max_examples=3)
    def test_erdos_renyi_does_not_mutate_original(self, seed: int):
        """Erdős-Rényi model must not mutate the original network."""
        net = build_test_network()
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        _ = erdos_renyi_model(net, seed=seed)
        
        assert count_nodes(net) == original_nodes
        assert count_edges(net) == original_edges

    def test_erdos_renyi_with_seed_is_reproducible(self):
        """Erdős-Rényi model with same seed should be reproducible."""
        net = build_test_network()
        
        net1 = erdos_renyi_model(net, seed=12345)
        net2 = erdos_renyi_model(net, seed=12345)
        
        # Should produce exactly same edges
        edges1 = set(net1.get_edges())
        edges2 = set(net2.get_edges())
        assert edges1 == edges2


# ============================================================================
# Layer Shuffle Model Properties
# ============================================================================


class TestLayerShuffleModelProperties:
    """Property-based tests for layer_shuffle_model."""

    @given(st.integers(min_value=42, max_value=9999))
    @settings(max_examples=3)
    def test_layer_shuffle_preserves_node_count(self, seed: int):
        """Layer shuffle must preserve node count."""
        net = build_test_network()
        original_count = count_nodes(net)
        
        random_net = layer_shuffle_model(net, seed=seed)
        assert count_nodes(random_net) == original_count

    @given(st.integers(min_value=42, max_value=9999))
    @settings(max_examples=3)
    def test_layer_shuffle_preserves_edge_count(self, seed: int):
        """Layer shuffle must preserve edge count."""
        net = build_test_network()
        original_count = count_edges(net)
        
        random_net = layer_shuffle_model(net, seed=seed)
        assert count_edges(random_net) == original_count

    @given(st.integers(min_value=42, max_value=9999))
    @settings(max_examples=3)
    def test_layer_shuffle_does_not_mutate_original(self, seed: int):
        """Layer shuffle must not mutate the original network."""
        net = build_test_network()
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        _ = layer_shuffle_model(net, seed=seed)
        
        assert count_nodes(net) == original_nodes
        assert count_edges(net) == original_edges


# ============================================================================
# Edge Swap Model Properties
# ============================================================================


class TestEdgeSwapModelProperties:
    """Property-based tests for edge_swap_model."""

    @given(st.integers(min_value=42, max_value=9999))
    @settings(max_examples=3)
    def test_edge_swap_preserves_node_count(self, seed: int):
        """Edge swap must preserve node count."""
        net = build_test_network()
        original_count = count_nodes(net)
        
        random_net = edge_swap_model(net, seed=seed, num_swaps=5)
        assert count_nodes(random_net) == original_count

    @given(st.integers(min_value=42, max_value=9999))
    @settings(max_examples=3)
    def test_edge_swap_preserves_edge_count(self, seed: int):
        """Edge swap must preserve edge count."""
        net = build_test_network()
        original_count = count_edges(net)
        
        random_net = edge_swap_model(net, seed=seed, num_swaps=5)
        assert count_edges(random_net) == original_count

    @given(st.integers(min_value=42, max_value=9999))
    @settings(max_examples=3)
    def test_edge_swap_does_not_mutate_original(self, seed: int):
        """Edge swap must not mutate the original network."""
        net = build_test_network()
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        _ = edge_swap_model(net, seed=seed, num_swaps=5)
        
        assert count_nodes(net) == original_nodes
        assert count_edges(net) == original_edges

    @given(
        st.integers(min_value=1, max_value=20),
        st.integers(min_value=42, max_value=9999),
    )
    @settings(max_examples=3)
    def test_edge_swap_with_different_swap_counts(self, num_swaps: int, seed: int):
        """Edge swap with different swap counts preserves structure."""
        net = build_test_network()
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        random_net = edge_swap_model(net, num_swaps=num_swaps, seed=seed)
        
        assert count_nodes(random_net) == original_nodes
        assert count_edges(random_net) == original_edges


# ============================================================================
# NullModelResult Properties
# ============================================================================


class TestNullModelResultProperties:
    """Property-based tests for NullModelResult."""

    @given(st.lists(st.integers(), min_size=0, max_size=20))
    def test_result_length_equals_num_samples(self, samples: list):
        """NullModelResult length should equal num_samples."""
        result = NullModelResult(model_type="test", samples=samples)
        
        assert len(result) == len(samples)
        assert result.num_samples == len(samples)

    @given(st.lists(st.integers(), min_size=1, max_size=10))
    def test_result_iteration_preserves_order(self, samples: list):
        """Iterating over NullModelResult should preserve sample order."""
        result = NullModelResult(model_type="test", samples=samples)
        
        collected = list(result)
        assert collected == samples

    @given(
        st.lists(st.text(), min_size=1, max_size=10),
    )
    def test_result_indexing(self, samples: list):
        """NullModelResult indexing should work correctly."""
        result = NullModelResult(model_type="test", samples=samples)
        
        # Test valid indices
        for i in range(len(samples)):
            assert result[i] == samples[i]


# ============================================================================
# generate_null_model Properties
# ============================================================================


class TestGenerateNullModelProperties:
    """Property-based tests for generate_null_model executor."""

    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=3)
    def test_generate_produces_requested_num_samples(self, num_samples: int):
        """generate_null_model should produce requested number of samples."""
        net = build_test_network()
        
        result = generate_null_model(
            net,
            model="configuration",
            num_samples=num_samples,
            seed=42,
        )
        
        assert len(result) == num_samples
        assert result.num_samples == num_samples

    @given(
        st.sampled_from(["configuration", "erdos_renyi", "layer_shuffle", "edge_swap"]),
        st.integers(min_value=42, max_value=9999),
    )
    @settings(max_examples=3)
    def test_generate_all_models_work(self, model: str, seed: int):
        """All registered null models should work with generate_null_model."""
        net = build_test_network()
        
        result = generate_null_model(
            net,
            model=model,
            num_samples=1,
            seed=seed,
        )
        
        assert isinstance(result, NullModelResult)
        assert len(result) == 1
        assert result.model_type == model

    @given(st.integers(min_value=1, max_value=5))
    @settings(max_examples=3)
    def test_generate_does_not_mutate_original_network(self, num_samples: int):
        """generate_null_model must not mutate the original network."""
        net = build_test_network()
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        _ = generate_null_model(
            net,
            model="configuration",
            num_samples=num_samples,
            seed=42,
        )
        
        assert count_nodes(net) == original_nodes
        assert count_edges(net) == original_edges

    def test_generate_with_same_seed_is_reproducible(self):
        """generate_null_model with same seed should be reproducible."""
        net = build_test_network()
        
        result1 = generate_null_model(
            net,
            model="erdos_renyi",
            num_samples=2,
            seed=54321,
        )
        result2 = generate_null_model(
            net,
            model="erdos_renyi",
            num_samples=2,
            seed=54321,
        )
        
        # Should produce same number of samples
        assert len(result1) == len(result2)
        
        # Each sample should have same structure
        for s1, s2 in zip(result1, result2):
            assert count_nodes(s1) == count_nodes(s2)


# ============================================================================
# Cross-model Invariants
# ============================================================================


class TestCrossModelInvariants:
    """Test invariants that hold across all null models."""

    @given(
        st.sampled_from(["configuration", "erdos_renyi", "layer_shuffle", "edge_swap"]),
        st.integers(min_value=42, max_value=999),
    )
    @settings(max_examples=3)
    def test_all_models_preserve_node_count(self, model: str, seed: int):
        """All null models must preserve node count."""
        net = build_test_network()
        original_count = count_nodes(net)
        
        result = generate_null_model(net, model=model, num_samples=1, seed=seed)
        random_net = result[0]
        
        assert count_nodes(random_net) == original_count

    @given(
        st.sampled_from(["configuration", "erdos_renyi", "layer_shuffle", "edge_swap"]),
        st.integers(min_value=42, max_value=999),
    )
    @settings(max_examples=3)
    def test_all_models_do_not_mutate_original(self, model: str, seed: int):
        """All null models must not mutate the original network."""
        net = build_test_network()
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        _ = generate_null_model(net, model=model, num_samples=1, seed=seed)
        
        assert count_nodes(net) == original_nodes
        assert count_edges(net) == original_edges

    @given(st.sampled_from(["layer_shuffle", "edge_swap"]))
    @settings(max_examples=3)
    def test_structure_preserving_models_preserve_edges(self, model: str):
        """Structure-preserving models (layer_shuffle, edge_swap) preserve edge count."""
        net = build_test_network()
        original_edges = count_edges(net)
        
        result = generate_null_model(net, model=model, num_samples=1, seed=42)
        random_net = result[0]
        
        assert count_edges(random_net) == original_edges
