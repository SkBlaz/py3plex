"""Property-based tests for the paths module.

This module tests invariants and properties of path finding algorithms
using hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import random

from py3plex.core import multinet
from py3plex.paths import (
    find_paths,
    shortest_path,
    all_paths,
    random_walk,
    multilayer_flow,
    PathResult,
)


# ============================================================================
# Helper functions
# ============================================================================


def build_test_network(
    num_nodes: int = 4,
    num_layers: int = 2,
    edges_per_layer: int = 3,
) -> multinet.multi_layer_network:
    """Build a test multilayer network for path testing."""
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
# Shortest Path Properties
# ============================================================================


class TestShortestPathProperties:
    """Property-based tests for shortest_path."""

    @given(st.integers(min_value=2, max_value=6))
    @settings(max_examples=10)
    def test_shortest_path_does_not_mutate_network(self, num_nodes: int):
        """shortest_path must not mutate the original network."""
        net = build_test_network(num_nodes=num_nodes)
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        _ = shortest_path(net, source="n0", target=f"n{num_nodes-1}")
        
        assert count_nodes(net) == original_nodes
        assert count_edges(net) == original_edges

    @given(st.integers(min_value=2, max_value=6))
    @settings(max_examples=10)
    def test_shortest_path_returns_dict(self, num_nodes: int):
        """shortest_path must return a dictionary with 'paths' key."""
        net = build_test_network(num_nodes=num_nodes)
        
        result = shortest_path(net, source="n0", target=f"n{num_nodes-1}")
        
        assert isinstance(result, dict)
        assert "paths" in result


# ============================================================================
# All Paths Properties
# ============================================================================


class TestAllPathsProperties:
    """Property-based tests for all_paths."""

    @given(st.integers(min_value=2, max_value=6))
    @settings(max_examples=10)
    def test_all_paths_does_not_mutate_network(self, num_nodes: int):
        """all_paths must not mutate the original network."""
        net = build_test_network(num_nodes=num_nodes)
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        _ = all_paths(net, source="n0", target=f"n{num_nodes-1}")
        
        assert count_nodes(net) == original_nodes
        assert count_edges(net) == original_edges

    @given(
        st.integers(min_value=2, max_value=6),
        st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=15)
    def test_all_paths_respects_limit(self, num_nodes: int, limit: int):
        """all_paths with limit should not exceed the limit."""
        net = build_test_network(num_nodes=num_nodes)
        
        result = all_paths(net, source="n0", target=f"n{num_nodes-1}", limit=limit)
        
        assert len(result["paths"]) <= limit


# ============================================================================
# Random Walk Properties
# ============================================================================


class TestRandomWalkProperties:
    """Property-based tests for random_walk."""

    @given(
        st.integers(min_value=2, max_value=6),
        st.integers(min_value=42, max_value=999),
    )
    @settings(max_examples=20)
    def test_random_walk_does_not_mutate_network(self, num_nodes: int, seed: int):
        """random_walk must not mutate the original network."""
        net = build_test_network(num_nodes=num_nodes)
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        _ = random_walk(net, source="n0", steps=10, seed=seed)
        
        assert count_nodes(net) == original_nodes
        assert count_edges(net) == original_edges

    @given(st.integers(min_value=42, max_value=999))
    @settings(max_examples=20)
    def test_random_walk_with_seed_is_reproducible(self, seed: int):
        """random_walk with same seed should produce same results."""
        net = build_test_network()
        
        result1 = random_walk(net, source="n0", steps=20, seed=seed)
        result2 = random_walk(net, source="n0", steps=20, seed=seed)
        
        assert result1["visit_frequency"] == result2["visit_frequency"]

    @given(
        st.integers(min_value=1, max_value=50),
        st.floats(min_value=0.0, max_value=0.5, allow_nan=False),
    )
    @settings(max_examples=15)
    def test_random_walk_visit_frequency_is_valid(self, steps: int, teleport: float):
        """random_walk visit frequency should be valid probabilities."""
        net = build_test_network()
        
        result = random_walk(net, source="n0", steps=steps, teleport=teleport, seed=42)
        
        frequencies = result["visit_frequency"]
        if frequencies:
            # All frequencies should be between 0 and 1
            for freq in frequencies.values():
                assert 0.0 <= freq <= 1.0


# ============================================================================
# Flow Properties
# ============================================================================


class TestFlowProperties:
    """Property-based tests for multilayer_flow."""

    @given(st.integers(min_value=2, max_value=6))
    @settings(max_examples=10)
    def test_flow_does_not_mutate_network(self, num_nodes: int):
        """multilayer_flow must not mutate the original network."""
        net = build_test_network(num_nodes=num_nodes)
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        _ = multilayer_flow(net, source="n0", target=f"n{num_nodes-1}")
        
        assert count_nodes(net) == original_nodes
        assert count_edges(net) == original_edges

    @given(st.integers(min_value=2, max_value=6))
    @settings(max_examples=10)
    def test_flow_value_is_non_negative(self, num_nodes: int):
        """Flow value must be non-negative."""
        net = build_test_network(num_nodes=num_nodes)
        
        result = multilayer_flow(net, source="n0", target=f"n{num_nodes-1}")
        
        assert result["flow_value"] >= 0


# ============================================================================
# PathResult Properties
# ============================================================================


class TestPathResultProperties:
    """Property-based tests for PathResult."""

    @given(st.lists(st.lists(st.text(), min_size=1), min_size=0, max_size=10))
    def test_result_length_equals_num_paths(self, paths: list):
        """PathResult length should equal num_paths."""
        result = PathResult(path_type="test", source="a", target="b", paths=paths)
        
        assert len(result) == len(paths)
        assert result.num_paths == len(paths)

    @given(st.lists(st.lists(st.text(), min_size=1), min_size=1, max_size=10))
    def test_result_iteration_preserves_order(self, paths: list):
        """Iterating over PathResult should preserve path order."""
        result = PathResult(path_type="test", source="a", target="b", paths=paths)
        
        collected = list(result)
        assert collected == paths

    @given(st.lists(st.lists(st.text(), min_size=1), min_size=1, max_size=10))
    def test_result_indexing(self, paths: list):
        """PathResult indexing should work correctly."""
        result = PathResult(path_type="test", source="a", target="b", paths=paths)
        
        for i in range(len(paths)):
            assert result[i] == paths[i]

    @given(st.lists(st.lists(st.integers(), min_size=1, max_size=10), min_size=1, max_size=10))
    def test_shortest_path_length_is_minimum(self, paths: list):
        """shortest_path_length should be the minimum path length minus 1."""
        result = PathResult(path_type="test", source="a", target="b", paths=paths)
        
        if paths:
            expected_min = min(len(p) - 1 for p in paths)
            assert result.shortest_path_length == expected_min


# ============================================================================
# find_paths Properties
# ============================================================================


class TestFindPathsProperties:
    """Property-based tests for find_paths executor."""

    @given(
        st.sampled_from(["shortest", "all", "flow"]),
        st.integers(min_value=2, max_value=6),
    )
    @settings(max_examples=20)
    def test_find_paths_returns_path_result(self, path_type: str, num_nodes: int):
        """find_paths should always return a PathResult."""
        net = build_test_network(num_nodes=num_nodes)
        
        result = find_paths(
            net,
            source="n0",
            target=f"n{num_nodes-1}",
            path_type=path_type,
        )
        
        assert isinstance(result, PathResult)
        assert result.path_type == path_type

    @given(
        st.sampled_from(["shortest", "all", "flow"]),
        st.integers(min_value=2, max_value=6),
    )
    @settings(max_examples=20)
    def test_find_paths_does_not_mutate_network(self, path_type: str, num_nodes: int):
        """find_paths must not mutate the original network."""
        net = build_test_network(num_nodes=num_nodes)
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        _ = find_paths(
            net,
            source="n0",
            target=f"n{num_nodes-1}",
            path_type=path_type,
        )
        
        assert count_nodes(net) == original_nodes
        assert count_edges(net) == original_edges

    @given(
        st.integers(min_value=1, max_value=5),
        st.integers(min_value=2, max_value=6),
    )
    @settings(max_examples=15)
    def test_find_paths_respects_limit(self, limit: int, num_nodes: int):
        """find_paths with limit should not exceed the limit."""
        net = build_test_network(num_nodes=num_nodes)
        
        result = find_paths(
            net,
            source="n0",
            target=f"n{num_nodes-1}",
            path_type="all",
            limit=limit,
        )
        
        assert len(result.paths) <= limit

    @given(st.integers(min_value=42, max_value=999))
    @settings(max_examples=10)
    def test_find_paths_random_walk_is_reproducible(self, seed: int):
        """find_paths with random_walk and same seed should be reproducible."""
        net = build_test_network()
        
        result1 = find_paths(
            net,
            source="n0",
            target=None,
            path_type="random_walk",
            steps=20,
            seed=seed,
        )
        result2 = find_paths(
            net,
            source="n0",
            target=None,
            path_type="random_walk",
            steps=20,
            seed=seed,
        )
        
        assert result1.visit_frequency == result2.visit_frequency


# ============================================================================
# Cross-algorithm Invariants
# ============================================================================


class TestCrossAlgorithmInvariants:
    """Test invariants that hold across all path algorithms."""

    @given(
        st.sampled_from(["shortest", "all", "flow"]),
        st.integers(min_value=2, max_value=6),
    )
    @settings(max_examples=20)
    def test_all_algorithms_preserve_network(self, algorithm: str, num_nodes: int):
        """All path algorithms must not mutate the original network."""
        net = build_test_network(num_nodes=num_nodes)
        original_nodes = count_nodes(net)
        original_edges = count_edges(net)
        
        _ = find_paths(
            net,
            source="n0",
            target=f"n{num_nodes-1}",
            path_type=algorithm,
        )
        
        assert count_nodes(net) == original_nodes
        assert count_edges(net) == original_edges

    @given(st.sampled_from(["shortest", "all", "flow"]))
    @settings(max_examples=10)
    def test_all_algorithms_return_path_result(self, algorithm: str):
        """All path algorithms should return PathResult."""
        net = build_test_network()
        
        result = find_paths(
            net,
            source="n0",
            target="n2",
            path_type=algorithm,
        )
        
        assert isinstance(result, PathResult)
        assert result.path_type == algorithm
