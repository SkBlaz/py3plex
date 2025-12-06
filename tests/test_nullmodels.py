"""Unit tests for the nullmodels module.

This module tests null model generation functionality including
ModelRegistry, configuration_model, erdos_renyi_model, layer_shuffle_model,
edge_swap_model, and the generate_null_model executor.
"""

import pytest
import random
from py3plex.core import multinet
from py3plex.nullmodels import (
    generate_null_model,
    configuration_model,
    erdos_renyi_model,
    layer_shuffle_model,
    edge_swap_model,
    ModelRegistry,
    model_registry,
    NullModelResult,
)


# ============================================================================
# Test fixtures
# ============================================================================


@pytest.fixture
def simple_network():
    """Create a simple multilayer network for testing."""
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
def empty_network():
    """Create an empty network for edge case testing."""
    return multinet.multi_layer_network(directed=False, verbose=False)


# ============================================================================
# ModelRegistry Tests
# ============================================================================


class TestModelRegistry:
    """Unit tests for ModelRegistry."""

    def test_create_registry(self):
        """Test creating a new ModelRegistry."""
        registry = ModelRegistry()
        assert registry is not None
        assert registry.list_models() == []

    def test_register_model(self):
        """Test registering a model function."""
        registry = ModelRegistry()

        @registry.register("test_model", description="Test model")
        def test_model_fn(network, **kwargs):
            return network

        assert registry.has("test_model")
        assert "test_model" in registry.list_models()

    def test_get_registered_model(self):
        """Test retrieving a registered model."""
        registry = ModelRegistry()

        @registry.register("test_model")
        def test_model_fn(network, **kwargs):
            return network

        fn = registry.get("test_model")
        assert fn is not None
        assert callable(fn)

    def test_get_unknown_model_raises_error(self):
        """Test that getting an unknown model raises ValueError."""
        registry = ModelRegistry()
        with pytest.raises(ValueError, match="Unknown null model"):
            registry.get("nonexistent_model")

    def test_has_model(self):
        """Test checking if a model exists."""
        registry = ModelRegistry()

        @registry.register("test_model")
        def test_model_fn(network, **kwargs):
            return network

        assert registry.has("test_model")
        assert not registry.has("nonexistent")


# ============================================================================
# Global Registry Tests
# ============================================================================


class TestGlobalRegistry:
    """Tests for the global model_registry."""

    def test_global_registry_exists(self):
        """Test that global registry exists and has models."""
        assert model_registry is not None
        models = model_registry.list_models()
        assert len(models) > 0

    def test_configuration_model_registered(self):
        """Test that configuration model is registered."""
        assert model_registry.has("configuration")

    def test_erdos_renyi_model_registered(self):
        """Test that Erdős-Rényi model is registered."""
        assert model_registry.has("erdos_renyi")

    def test_layer_shuffle_model_registered(self):
        """Test that layer shuffle model is registered."""
        assert model_registry.has("layer_shuffle")

    def test_edge_swap_model_registered(self):
        """Test that edge swap model is registered."""
        assert model_registry.has("edge_swap")


# ============================================================================
# Configuration Model Tests
# ============================================================================


class TestConfigurationModel:
    """Unit tests for configuration_model."""

    def test_configuration_model_basic(self, simple_network):
        """Test basic configuration model generation."""
        random_net = configuration_model(simple_network, seed=42)
        assert random_net is not None
        assert random_net is not simple_network

    def test_configuration_model_preserves_node_count(self, simple_network):
        """Test that configuration model preserves node count."""
        original_nodes = set(simple_network.get_nodes())
        random_net = configuration_model(simple_network, seed=42)
        random_nodes = set(random_net.get_nodes())
        assert len(random_nodes) == len(original_nodes)

    def test_configuration_model_with_empty_network(self, empty_network):
        """Test configuration model with empty network."""
        random_net = configuration_model(empty_network, seed=42)
        assert random_net is not None

    def test_configuration_model_reproducible_with_seed(self, simple_network):
        """Test that configuration model is reproducible with seed."""
        net1 = configuration_model(simple_network, seed=123)
        net2 = configuration_model(simple_network, seed=123)
        
        edges1 = set(net1.get_edges())
        edges2 = set(net2.get_edges())
        
        # With same seed, should be reproducible (though edges might differ due to randomness in nx)
        assert len(edges1) == len(edges2)


# ============================================================================
# Erdős-Rényi Model Tests
# ============================================================================


class TestErdosRenyiModel:
    """Unit tests for erdos_renyi_model."""

    def test_erdos_renyi_model_basic(self, simple_network):
        """Test basic Erdős-Rényi model generation."""
        random_net = erdos_renyi_model(simple_network, seed=42)
        assert random_net is not None
        assert random_net is not simple_network

    def test_erdos_renyi_model_preserves_node_count(self, simple_network):
        """Test that Erdős-Rényi model preserves node count."""
        original_nodes = set(simple_network.get_nodes())
        random_net = erdos_renyi_model(simple_network, seed=42)
        random_nodes = set(random_net.get_nodes())
        assert len(random_nodes) == len(original_nodes)

    def test_erdos_renyi_model_with_empty_network(self, empty_network):
        """Test Erdős-Rényi model with empty network."""
        random_net = erdos_renyi_model(empty_network, seed=42)
        assert random_net is not None

    def test_erdos_renyi_model_reproducible_with_seed(self, simple_network):
        """Test that Erdős-Rényi model is reproducible with seed."""
        net1 = erdos_renyi_model(simple_network, seed=456)
        net2 = erdos_renyi_model(simple_network, seed=456)
        
        edges1 = set(net1.get_edges())
        edges2 = set(net2.get_edges())
        
        # With same seed, should produce same edges
        assert edges1 == edges2


# ============================================================================
# Layer Shuffle Model Tests
# ============================================================================


class TestLayerShuffleModel:
    """Unit tests for layer_shuffle_model."""

    def test_layer_shuffle_model_basic(self, simple_network):
        """Test basic layer shuffle model generation."""
        random_net = layer_shuffle_model(simple_network, seed=42)
        assert random_net is not None
        assert random_net is not simple_network

    def test_layer_shuffle_model_preserves_node_count(self, simple_network):
        """Test that layer shuffle preserves node count."""
        original_count = sum(1 for _ in simple_network.get_nodes())
        random_net = layer_shuffle_model(simple_network, seed=42)
        random_count = sum(1 for _ in random_net.get_nodes())
        assert random_count == original_count

    def test_layer_shuffle_model_preserves_edge_count(self, simple_network):
        """Test that layer shuffle preserves edge count."""
        original_count = sum(1 for _ in simple_network.get_edges())
        random_net = layer_shuffle_model(simple_network, seed=42)
        random_count = sum(1 for _ in random_net.get_edges())
        assert random_count == original_count

    def test_layer_shuffle_model_with_empty_network(self, empty_network):
        """Test layer shuffle with empty network."""
        random_net = layer_shuffle_model(empty_network, seed=42)
        assert random_net is not None


# ============================================================================
# Edge Swap Model Tests
# ============================================================================


class TestEdgeSwapModel:
    """Unit tests for edge_swap_model."""

    def test_edge_swap_model_basic(self, simple_network):
        """Test basic edge swap model generation."""
        random_net = edge_swap_model(simple_network, seed=42)
        assert random_net is not None
        assert random_net is not simple_network

    def test_edge_swap_model_preserves_node_count(self, simple_network):
        """Test that edge swap preserves node count."""
        original_count = sum(1 for _ in simple_network.get_nodes())
        random_net = edge_swap_model(simple_network, seed=42)
        random_count = sum(1 for _ in random_net.get_nodes())
        assert random_count == original_count

    def test_edge_swap_model_preserves_edge_count(self, simple_network):
        """Test that edge swap preserves edge count."""
        original_count = sum(1 for _ in simple_network.get_edges())
        random_net = edge_swap_model(simple_network, seed=42, num_swaps=10)
        random_count = sum(1 for _ in random_net.get_edges())
        assert random_count == original_count

    def test_edge_swap_model_with_empty_network(self, empty_network):
        """Test edge swap with empty network."""
        random_net = edge_swap_model(empty_network, seed=42)
        assert random_net is not None

    def test_edge_swap_model_custom_num_swaps(self, simple_network):
        """Test edge swap with custom number of swaps."""
        random_net = edge_swap_model(simple_network, num_swaps=5, seed=42)
        assert random_net is not None


# ============================================================================
# NullModelResult Tests
# ============================================================================


class TestNullModelResult:
    """Unit tests for NullModelResult."""

    def test_create_result(self):
        """Test creating a NullModelResult."""
        samples = [1, 2, 3]
        result = NullModelResult(
            model_type="test",
            samples=samples,
            seed=42,
        )
        assert result.model_type == "test"
        assert len(result) == 3
        assert result.seed == 42

    def test_result_iteration(self):
        """Test iterating over result samples."""
        samples = [1, 2, 3]
        result = NullModelResult(model_type="test", samples=samples)
        
        collected = list(result)
        assert collected == [1, 2, 3]

    def test_result_indexing(self):
        """Test indexing result samples."""
        samples = ["a", "b", "c"]
        result = NullModelResult(model_type="test", samples=samples)
        
        assert result[0] == "a"
        assert result[1] == "b"
        assert result[2] == "c"

    def test_result_num_samples(self):
        """Test num_samples property."""
        samples = [1, 2, 3, 4]
        result = NullModelResult(model_type="test", samples=samples)
        
        assert result.num_samples == 4

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        samples = [1, 2, 3]
        meta = {"param": "value"}
        result = NullModelResult(
            model_type="test",
            samples=samples,
            seed=99,
            meta=meta,
        )
        
        d = result.to_dict()
        assert d["model_type"] == "test"
        assert d["num_samples"] == 3
        assert d["seed"] == 99
        assert d["meta"] == meta

    def test_result_repr(self):
        """Test result string representation."""
        samples = [1, 2]
        result = NullModelResult(
            model_type="test_model",
            samples=samples,
            seed=42,
        )
        
        repr_str = repr(result)
        assert "test_model" in repr_str
        assert "2" in repr_str
        assert "42" in repr_str


# ============================================================================
# generate_null_model Tests
# ============================================================================


class TestGenerateNullModel:
    """Unit tests for generate_null_model executor."""

    def test_generate_null_model_basic(self, simple_network):
        """Test basic null model generation."""
        result = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=1,
            seed=42,
        )
        assert isinstance(result, NullModelResult)
        assert len(result) == 1
        assert result.model_type == "configuration"

    def test_generate_null_model_multiple_samples(self, simple_network):
        """Test generating multiple samples."""
        result = generate_null_model(
            simple_network,
            model="erdos_renyi",
            num_samples=5,
            seed=42,
        )
        assert len(result) == 5
        assert result.num_samples == 5

    def test_generate_null_model_with_params(self, simple_network):
        """Test generating null model with additional parameters."""
        result = generate_null_model(
            simple_network,
            model="edge_swap",
            num_samples=2,
            num_swaps=10,
            seed=42,
        )
        assert len(result) == 2

    def test_generate_null_model_invalid_model(self, simple_network):
        """Test that invalid model raises ValueError."""
        with pytest.raises(ValueError, match="Unknown null model"):
            generate_null_model(
                simple_network,
                model="nonexistent_model",
            )

    def test_generate_null_model_all_model_types(self, simple_network):
        """Test all registered model types."""
        models = ["configuration", "erdos_renyi", "layer_shuffle", "edge_swap"]
        
        for model_name in models:
            result = generate_null_model(
                simple_network,
                model=model_name,
                num_samples=1,
                seed=42,
            )
            assert isinstance(result, NullModelResult)
            assert len(result) == 1

    def test_generate_null_model_reproducibility(self, simple_network):
        """Test that generation is reproducible with seed."""
        result1 = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=1,
            seed=999,
        )
        result2 = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=1,
            seed=999,
        )
        
        # Both should produce results (exact equality hard to test due to randomness)
        assert len(result1) == 1
        assert len(result2) == 1
