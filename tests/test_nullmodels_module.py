"""
Tests for py3plex.nullmodels.models module.

This module tests null model algorithms for multilayer networks.
"""

import pytest
from py3plex.nullmodels.models import ModelRegistry, model_registry, _copy_network
from py3plex.core import multinet


class TestModelRegistry:
    """Test the ModelRegistry class."""

    def test_register_model(self):
        """Test registering a model."""
        registry = ModelRegistry()
        
        @registry.register("test_model", "A test model")
        def test_fn(network):
            return network
        
        assert registry.has("test_model")
        assert "test_model" in registry.list_models()

    def test_register_without_description(self):
        """Test registering a model without description."""
        registry = ModelRegistry()
        
        @registry.register("simple_model")
        def simple_fn(network):
            return network
        
        assert registry.has("simple_model")

    def test_get_model(self):
        """Test retrieving a registered model."""
        registry = ModelRegistry()
        
        @registry.register("my_model")
        def my_fn(network):
            return "result"
        
        fn = registry.get("my_model")
        assert fn(None) == "result"

    def test_get_unknown_model_raises_error(self):
        """Test that getting unknown model raises ValueError."""
        registry = ModelRegistry()
        
        with pytest.raises(ValueError, match="Unknown null model"):
            registry.get("nonexistent")

    def test_list_models(self):
        """Test listing all models."""
        registry = ModelRegistry()
        
        @registry.register("model1")
        def fn1(network):
            pass
        
        @registry.register("model2")
        def fn2(network):
            pass
        
        models = registry.list_models()
        assert len(models) == 2
        assert "model1" in models
        assert "model2" in models

    def test_has_model(self):
        """Test checking if model exists."""
        registry = ModelRegistry()
        
        @registry.register("exists")
        def fn(network):
            pass
        
        assert registry.has("exists") is True
        assert registry.has("not_exists") is False


class TestCopyNetwork:
    """Test the _copy_network function."""

    def test_copy_simple_network(self):
        """Test copying a simple network."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([
            {'source': 'A', 'type': 'layer1'},
            {'source': 'B', 'type': 'layer1'},
        ])
        network.add_edges([
            {
                'source': 'A',
                'target': 'B',
                'source_type': 'layer1',
                'target_type': 'layer1'
            }
        ])
        
        copy = _copy_network(network)
        
        # Should be a different object
        assert copy is not network
        
        # Should have the same directed property
        assert copy.directed == network.directed

    def test_copy_empty_network(self):
        """Test copying an empty network."""
        network = multinet.multi_layer_network(directed=True)
        
        copy = _copy_network(network)
        
        assert copy is not network
        assert copy.directed == network.directed

    def test_copy_directed_network(self):
        """Test copying preserves directedness."""
        network = multinet.multi_layer_network(directed=True)
        copy = _copy_network(network)
        
        assert copy.directed is True

    def test_copy_undirected_network(self):
        """Test copying preserves undirectedness."""
        network = multinet.multi_layer_network(directed=False)
        copy = _copy_network(network)
        
        assert copy.directed is False


class TestGlobalRegistry:
    """Test the global model registry."""

    def test_global_registry_exists(self):
        """Test that global registry is available."""
        assert model_registry is not None
        assert isinstance(model_registry, ModelRegistry)

    def test_can_register_on_global_registry(self):
        """Test registering models on global registry."""
        # Store original models
        original_models = set(model_registry.list_models())
        
        @model_registry.register("test_global_model")
        def test_fn(network):
            return network
        
        try:
            assert model_registry.has("test_global_model")
        finally:
            # Clean up: remove the test model
            if hasattr(model_registry, '_models'):
                model_registry._models.pop("test_global_model", None)
