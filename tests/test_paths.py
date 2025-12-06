"""Unit tests for the paths module.

This module tests path finding functionality including
PathRegistry, shortest_path, all_paths, random_walk, multilayer_flow,
and the find_paths executor.
"""

import pytest
import random
from py3plex.core import multinet
from py3plex.paths import (
    find_paths,
    shortest_path,
    all_paths,
    random_walk,
    multilayer_flow,
    PathRegistry,
    path_registry,
    PathResult,
)


# ============================================================================
# Test fixtures
# ============================================================================


@pytest.fixture
def simple_network():
    """Create a simple multilayer network for path testing."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["n1", "L1", "n2", "L1", 1.0],
        ["n2", "L1", "n3", "L1", 1.0],
        ["n1", "L2", "n3", "L2", 1.0],
        ["n2", "L2", "n3", "L2", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


@pytest.fixture
def chain_network():
    """Create a chain network for path testing."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["n1", "L1", "n2", "L1", 1.0],
        ["n2", "L1", "n3", "L1", 1.0],
        ["n3", "L1", "n4", "L1", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


@pytest.fixture
def empty_network():
    """Create an empty network for edge case testing."""
    return multinet.multi_layer_network(directed=False, verbose=False)


# ============================================================================
# PathRegistry Tests
# ============================================================================


class TestPathRegistry:
    """Unit tests for PathRegistry."""

    def test_create_registry(self):
        """Test creating a new PathRegistry."""
        registry = PathRegistry()
        assert registry is not None
        assert registry.list_algorithms() == []

    def test_register_algorithm(self):
        """Test registering a path algorithm."""
        registry = PathRegistry()

        @registry.register("test_path", description="Test algorithm")
        def test_path_fn(network, source, target, **kwargs):
            return {"paths": []}

        assert registry.has("test_path")
        assert "test_path" in registry.list_algorithms()

    def test_get_registered_algorithm(self):
        """Test retrieving a registered algorithm."""
        registry = PathRegistry()

        @registry.register("test_path")
        def test_path_fn(network, source, target, **kwargs):
            return {"paths": []}

        fn = registry.get("test_path")
        assert fn is not None
        assert callable(fn)

    def test_get_unknown_algorithm_raises_error(self):
        """Test that getting an unknown algorithm raises ValueError."""
        registry = PathRegistry()
        with pytest.raises(ValueError, match="Unknown path algorithm"):
            registry.get("nonexistent_algorithm")

    def test_has_algorithm(self):
        """Test checking if an algorithm exists."""
        registry = PathRegistry()

        @registry.register("test_path")
        def test_path_fn(network, source, target, **kwargs):
            return {"paths": []}

        assert registry.has("test_path")
        assert not registry.has("nonexistent")


# ============================================================================
# Global Registry Tests
# ============================================================================


class TestGlobalRegistry:
    """Tests for the global path_registry."""

    def test_global_registry_exists(self):
        """Test that global registry exists and has algorithms."""
        assert path_registry is not None
        algorithms = path_registry.list_algorithms()
        assert len(algorithms) > 0

    def test_shortest_path_registered(self):
        """Test that shortest path algorithm is registered."""
        assert path_registry.has("shortest")

    def test_all_paths_registered(self):
        """Test that all paths algorithm is registered."""
        assert path_registry.has("all")

    def test_random_walk_registered(self):
        """Test that random walk algorithm is registered."""
        assert path_registry.has("random_walk")

    def test_flow_registered(self):
        """Test that flow algorithm is registered."""
        assert path_registry.has("flow")


# ============================================================================
# Shortest Path Tests
# ============================================================================


class TestShortestPath:
    """Unit tests for shortest_path."""

    def test_shortest_path_basic(self, simple_network):
        """Test basic shortest path finding."""
        result = shortest_path(simple_network, source="n1", target="n3")
        assert result is not None
        assert "paths" in result

    def test_shortest_path_returns_path(self, chain_network):
        """Test that shortest path returns a valid path."""
        result = shortest_path(chain_network, source="n1", target="n4")
        assert "paths" in result
        if result["paths"]:
            path = result["paths"][0]
            assert len(path) >= 2  # At least source and target

    def test_shortest_path_empty_network(self, empty_network):
        """Test shortest path with empty network."""
        result = shortest_path(empty_network, source="n1", target="n2")
        assert "paths" in result
        assert result["paths"] == []

    def test_shortest_path_nonexistent_source(self, simple_network):
        """Test shortest path with nonexistent source."""
        result = shortest_path(simple_network, source="nonexistent", target="n1")
        assert "paths" in result
        assert result["paths"] == []

    def test_shortest_path_nonexistent_target(self, simple_network):
        """Test shortest path with nonexistent target."""
        result = shortest_path(simple_network, source="n1", target="nonexistent")
        assert "paths" in result
        assert result["paths"] == []


# ============================================================================
# All Paths Tests
# ============================================================================


class TestAllPaths:
    """Unit tests for all_paths."""

    def test_all_paths_basic(self, simple_network):
        """Test basic all paths finding."""
        result = all_paths(simple_network, source="n1", target="n3")
        assert result is not None
        assert "paths" in result

    def test_all_paths_with_limit(self, simple_network):
        """Test all paths with limit."""
        result = all_paths(simple_network, source="n1", target="n3", limit=1)
        assert "paths" in result
        if result["paths"]:
            assert len(result["paths"]) <= 1

    def test_all_paths_with_max_length(self, chain_network):
        """Test all paths with max_length."""
        result = all_paths(chain_network, source="n1", target="n4", max_length=3)
        assert "paths" in result
        # Paths should not exceed max_length (cutoff in nx.all_simple_paths)
        # cutoff is the maximum path length (number of edges), not nodes
        for path in result["paths"]:
            assert len(path) <= 4  # max_length=3 edges means 4 nodes max

    def test_all_paths_empty_network(self, empty_network):
        """Test all paths with empty network."""
        result = all_paths(empty_network, source="n1", target="n2")
        assert "paths" in result
        assert result["paths"] == []


# ============================================================================
# Random Walk Tests
# ============================================================================


class TestRandomWalk:
    """Unit tests for random_walk."""

    def test_random_walk_basic(self, simple_network):
        """Test basic random walk."""
        result = random_walk(simple_network, source="n1", steps=10, seed=42)
        assert result is not None
        assert "visit_frequency" in result
        assert "paths" in result

    def test_random_walk_returns_visit_frequency(self, simple_network):
        """Test that random walk returns visit frequency."""
        result = random_walk(simple_network, source="n1", steps=10, seed=42)
        assert isinstance(result["visit_frequency"], dict)

    def test_random_walk_with_teleport(self, simple_network):
        """Test random walk with teleportation."""
        result = random_walk(
            simple_network, source="n1", steps=20, teleport=0.2, seed=42
        )
        assert "visit_frequency" in result

    def test_random_walk_reproducible_with_seed(self, simple_network):
        """Test that random walk is reproducible with seed."""
        result1 = random_walk(simple_network, source="n1", steps=10, seed=123)
        result2 = random_walk(simple_network, source="n1", steps=10, seed=123)
        
        # Should produce same visit frequencies
        assert result1["visit_frequency"] == result2["visit_frequency"]

    def test_random_walk_empty_network(self, empty_network):
        """Test random walk with empty network."""
        result = random_walk(empty_network, source="n1", steps=10, seed=42)
        assert "visit_frequency" in result
        assert result["visit_frequency"] == {}


# ============================================================================
# Flow Tests
# ============================================================================


class TestMultilayerFlow:
    """Unit tests for multilayer_flow."""

    def test_flow_basic(self, simple_network):
        """Test basic flow computation."""
        result = multilayer_flow(simple_network, source="n1", target="n3")
        assert result is not None
        assert "flow_value" in result
        assert "flow_values" in result

    def test_flow_returns_numeric_value(self, simple_network):
        """Test that flow returns a numeric flow value."""
        result = multilayer_flow(simple_network, source="n1", target="n3")
        assert isinstance(result["flow_value"], (int, float))
        assert result["flow_value"] >= 0

    def test_flow_empty_network(self, empty_network):
        """Test flow with empty network."""
        result = multilayer_flow(empty_network, source="n1", target="n2")
        assert "flow_value" in result
        assert result["flow_value"] == 0

    def test_flow_nonexistent_nodes(self, simple_network):
        """Test flow with nonexistent nodes."""
        result = multilayer_flow(
            simple_network, source="nonexistent1", target="nonexistent2"
        )
        assert result["flow_value"] == 0


# ============================================================================
# PathResult Tests
# ============================================================================


class TestPathResult:
    """Unit tests for PathResult."""

    def test_create_result(self):
        """Test creating a PathResult."""
        paths = [[("n1", "L1"), ("n2", "L1")]]
        result = PathResult(
            path_type="shortest",
            source="n1",
            target="n2",
            paths=paths,
        )
        assert result.path_type == "shortest"
        assert result.source == "n1"
        assert result.target == "n2"
        assert len(result) == 1

    def test_result_iteration(self):
        """Test iterating over result paths."""
        paths = [["p1"], ["p2"], ["p3"]]
        result = PathResult(path_type="all", source="a", target="b", paths=paths)
        
        collected = list(result)
        assert collected == paths

    def test_result_indexing(self):
        """Test indexing result paths."""
        paths = [["p1"], ["p2"], ["p3"]]
        result = PathResult(path_type="all", source="a", target="b", paths=paths)
        
        assert result[0] == ["p1"]
        assert result[1] == ["p2"]
        assert result[2] == ["p3"]

    def test_result_num_paths(self):
        """Test num_paths property."""
        paths = [["p1"], ["p2"], ["p3"]]
        result = PathResult(path_type="all", source="a", target="b", paths=paths)
        
        assert result.num_paths == 3

    def test_result_shortest_path_length(self):
        """Test shortest_path_length property."""
        paths = [
            ["n1", "n2"],  # length 1
            ["n1", "n2", "n3"],  # length 2
            ["n1", "n2", "n3", "n4"],  # length 3
        ]
        result = PathResult(path_type="all", source="n1", target="n4", paths=paths)
        
        assert result.shortest_path_length == 1

    def test_result_shortest_path_length_empty(self):
        """Test shortest_path_length with no paths."""
        result = PathResult(path_type="shortest", source="n1", target="n2", paths=[])
        
        assert result.shortest_path_length is None

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        paths = [["n1", "n2"]]
        result = PathResult(
            path_type="shortest",
            source="n1",
            target="n2",
            paths=paths,
        )
        
        d = result.to_dict()
        assert d["path_type"] == "shortest"
        assert d["source"] == "n1"
        assert d["target"] == "n2"
        assert d["num_paths"] == 1

    def test_result_repr(self):
        """Test result string representation."""
        paths = [["n1", "n2"]]
        result = PathResult(
            path_type="shortest",
            source="n1",
            target="n2",
            paths=paths,
        )
        
        repr_str = repr(result)
        assert "shortest" in repr_str
        assert "n1" in repr_str
        assert "n2" in repr_str


# ============================================================================
# find_paths Tests
# ============================================================================


class TestFindPaths:
    """Unit tests for find_paths executor."""

    def test_find_paths_shortest(self, simple_network):
        """Test find_paths with shortest path."""
        result = find_paths(
            simple_network,
            source="n1",
            target="n3",
            path_type="shortest",
        )
        assert isinstance(result, PathResult)
        assert result.path_type == "shortest"

    def test_find_paths_all(self, simple_network):
        """Test find_paths with all paths."""
        result = find_paths(
            simple_network,
            source="n1",
            target="n3",
            path_type="all",
        )
        assert isinstance(result, PathResult)
        assert result.path_type == "all"

    def test_find_paths_random_walk(self, simple_network):
        """Test find_paths with random walk."""
        result = find_paths(
            simple_network,
            source="n1",
            target=None,
            path_type="random_walk",
            steps=10,
            seed=42,
        )
        assert isinstance(result, PathResult)
        assert result.path_type == "random_walk"

    def test_find_paths_flow(self, simple_network):
        """Test find_paths with flow."""
        result = find_paths(
            simple_network,
            source="n1",
            target="n3",
            path_type="flow",
        )
        assert isinstance(result, PathResult)
        assert result.path_type == "flow"

    def test_find_paths_with_limit(self, simple_network):
        """Test find_paths with limit."""
        result = find_paths(
            simple_network,
            source="n1",
            target="n3",
            path_type="all",
            limit=1,
        )
        assert len(result.paths) <= 1

    def test_find_paths_invalid_type(self, simple_network):
        """Test that invalid path_type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown path algorithm"):
            find_paths(
                simple_network,
                source="n1",
                target="n3",
                path_type="nonexistent_type",
            )

    def test_find_paths_all_types(self, simple_network):
        """Test all registered path types."""
        path_types = ["shortest", "all", "random_walk", "flow"]
        
        for path_type in path_types:
            result = find_paths(
                simple_network,
                source="n1",
                target="n3" if path_type != "random_walk" else None,
                path_type=path_type,
                seed=42 if path_type == "random_walk" else None,
                steps=10 if path_type == "random_walk" else None,
            )
            assert isinstance(result, PathResult)
            assert result.path_type == path_type
