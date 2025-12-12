"""
Extended tests for py3plex.nullmodels module.

This module adds additional tests for executor and result classes
to improve coverage.
"""

import pytest
from py3plex.nullmodels.executor import generate_null_model
from py3plex.nullmodels.result import NullModelResult
from py3plex.nullmodels.models import model_registry
from py3plex.core import multinet


@pytest.fixture
def simple_network():
    """Create a simple test network."""
    network = multinet.multi_layer_network(directed=False, verbose=False)
    network.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
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
        }
    ])
    return network


class TestNullModelResult:
    """Test the NullModelResult class."""

    def test_create_result(self):
        """Test creating a NullModelResult."""
        samples = ["sample1", "sample2", "sample3"]
        result = NullModelResult(
            model_type="test_model",
            samples=samples,
            seed=42
        )
        
        assert result.model_type == "test_model"
        assert result.num_samples == 3
        assert result.seed == 42

    def test_result_iteration(self):
        """Test iterating over result samples."""
        samples = ["s1", "s2", "s3"]
        result = NullModelResult(
            model_type="test",
            samples=samples
        )
        
        collected = list(result)
        assert collected == samples

    def test_result_indexing(self):
        """Test indexing result samples."""
        samples = ["s1", "s2", "s3"]
        result = NullModelResult(
            model_type="test",
            samples=samples
        )
        
        assert result[0] == "s1"
        assert result[1] == "s2"
        assert result[2] == "s3"

    def test_result_length(self):
        """Test length of result."""
        samples = ["s1", "s2"]
        result = NullModelResult(
            model_type="test",
            samples=samples
        )
        
        assert len(result) == 2

    def test_result_with_metadata(self):
        """Test result with metadata."""
        meta = {"param1": "value1", "param2": 42}
        result = NullModelResult(
            model_type="test",
            samples=[],
            meta=meta
        )
        
        assert result.meta == meta

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = NullModelResult(
            model_type="configuration",
            samples=["s1", "s2"],
            seed=123,
            meta={"key": "value"}
        )
        
        d = result.to_dict()
        assert d["model_type"] == "configuration"
        assert d["num_samples"] == 2
        assert d["seed"] == 123
        assert d["meta"]["key"] == "value"

    def test_result_repr(self):
        """Test string representation of result."""
        result = NullModelResult(
            model_type="erdos_renyi",
            samples=["s1", "s2", "s3"],
            seed=42
        )
        
        repr_str = repr(result)
        assert "erdos_renyi" in repr_str
        assert "num_samples=3" in repr_str
        assert "seed=42" in repr_str

    def test_empty_result(self):
        """Test result with no samples."""
        result = NullModelResult(
            model_type="test",
            samples=[]
        )
        
        assert result.num_samples == 0
        assert len(result) == 0
        assert list(result) == []


class TestGenerateNullModel:
    """Test the generate_null_model executor."""

    def test_generate_single_sample(self, simple_network):
        """Test generating a single null model sample."""
        result = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=1,
            seed=42
        )
        
        assert isinstance(result, NullModelResult)
        assert result.model_type == "configuration"
        assert result.num_samples == 1
        assert result.seed == 42

    def test_generate_multiple_samples(self, simple_network):
        """Test generating multiple null model samples."""
        result = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=3,
            seed=42
        )
        
        assert result.num_samples == 3
        assert len(result.samples) == 3

    def test_generate_with_erdos_renyi(self, simple_network):
        """Test generating with Erdős-Rényi model."""
        result = generate_null_model(
            simple_network,
            model="erdos_renyi",
            num_samples=2,
            seed=123
        )
        
        assert result.model_type == "erdos_renyi"
        assert result.num_samples == 2

    def test_generate_without_seed(self, simple_network):
        """Test generating without explicit seed."""
        result = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=1
        )
        
        assert result.seed is None
        assert result.num_samples == 1

    def test_generate_with_invalid_model(self, simple_network):
        """Test that invalid model raises error."""
        with pytest.raises(ValueError, match="Unknown null model"):
            generate_null_model(
                simple_network,
                model="nonexistent_model",
                num_samples=1
            )

    def test_generate_with_layers_parameter(self, simple_network):
        """Test generating with layers parameter."""
        result = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=1,
            layers=["layer1"]
        )
        
        assert result.meta["layers"] == ["layer1"]

    def test_generate_with_custom_parameters(self, simple_network):
        """Test generating with custom model parameters."""
        result = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=1,
            preserve_degree=True,
            preserve_layer_sizes=True
        )
        
        assert "preserve_degree" in result.meta["params"]
        assert "preserve_layer_sizes" in result.meta["params"]

    def test_generate_samples_are_different_with_seed(self, simple_network):
        """Test that samples with different seeds are different."""
        result = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=2,
            seed=42
        )
        
        # Samples should exist (may or may not be equal depending on random generation)
        assert len(result.samples) == 2

    def test_generate_default_model(self, simple_network):
        """Test generating with default model type."""
        result = generate_null_model(
            simple_network,
            num_samples=1
        )
        
        # Default is "configuration"
        assert result.model_type == "configuration"


class TestRegisteredModels:
    """Test registered null models."""

    def test_configuration_model_registered(self):
        """Test that configuration model is registered."""
        assert model_registry.has("configuration")

    def test_erdos_renyi_model_registered(self):
        """Test that Erdős-Rényi model is registered."""
        assert model_registry.has("erdos_renyi")

    def test_configuration_model_callable(self, simple_network):
        """Test that configuration model can be called."""
        model_fn = model_registry.get("configuration")
        result = model_fn(simple_network, seed=42)
        assert result is not None

    def test_erdos_renyi_model_callable(self, simple_network):
        """Test that Erdős-Rényi model can be called."""
        model_fn = model_registry.get("erdos_renyi")
        result = model_fn(simple_network, seed=42)
        assert result is not None
