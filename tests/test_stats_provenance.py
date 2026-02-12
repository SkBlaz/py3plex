"""Tests for py3plex.stats.provenance module.

Tests provenance tracking for statistics computations.
"""

import pytest
from py3plex.stats.provenance import Provenance


class TestProvenanceCreation:
    """Test Provenance creation and attributes."""

    def test_create_minimal_provenance(self):
        """Test creating provenance with minimal fields."""
        prov = Provenance(
            algorithm="brandes",
            uncertainty_method="bootstrap"
        )
        assert prov.algorithm == "brandes"
        assert prov.uncertainty_method == "bootstrap"

    def test_create_provenance_with_params(self):
        """Test creating provenance with parameters."""
        prov = Provenance(
            algorithm="louvain",
            uncertainty_method="ensemble",
            parameters={"resolution": 1.0, "n_samples": 50}
        )
        assert prov.parameters["resolution"] == 1.0
        assert prov.parameters["n_samples"] == 50

    def test_create_provenance_with_seed(self):
        """Test creating provenance with seed."""
        prov = Provenance(
            algorithm="leiden",
            uncertainty_method="none",
            seed=42
        )
        assert prov.seed == 42

    def test_create_provenance_with_timestamp(self):
        """Test creating provenance with timestamp."""
        prov = Provenance(
            algorithm="degree",
            uncertainty_method="analytic",
            timestamp="2024-01-01T00:00:00Z"
        )
        assert prov.timestamp == "2024-01-01T00:00:00Z"

    def test_create_provenance_with_version(self):
        """Test creating provenance with library version."""
        prov = Provenance(
            algorithm="pagerank",
            uncertainty_method="delta",
            library_version="1.1.3"
        )
        assert prov.library_version == "1.1.3"

    def test_provenance_is_frozen(self):
        """Test that provenance is immutable (frozen dataclass)."""
        prov = Provenance(
            algorithm="test",
            uncertainty_method="none"
        )
        with pytest.raises(AttributeError):
            prov.algorithm = "modified"


class TestProvenanceSerialization:
    """Test Provenance serialization."""

    def test_to_json_dict_minimal(self):
        """Test serializing minimal provenance to dict."""
        prov = Provenance(
            algorithm="degree",
            uncertainty_method="none"
        )
        data = prov.to_json_dict()
        
        assert isinstance(data, dict)
        assert data["algorithm"] == "degree"
        assert data["uncertainty_method"] == "none"
        assert data["params"] == {}

    def test_to_json_dict_with_params(self):
        """Test serializing provenance with parameters."""
        prov = Provenance(
            algorithm="louvain",
            uncertainty_method="bootstrap",
            parameters={"resolution": 1.0, "n_samples": 100}
        )
        data = prov.to_json_dict()
        
        assert data["params"]["resolution"] == 1.0
        assert data["params"]["n_samples"] == 100

    def test_to_json_dict_with_seed(self):
        """Test serializing provenance with seed."""
        prov = Provenance(
            algorithm="leiden",
            uncertainty_method="ensemble",
            seed=42
        )
        data = prov.to_json_dict()
        
        assert data["seed"] == 42

    def test_to_json_dict_with_timestamp(self):
        """Test serializing provenance with timestamp."""
        prov = Provenance(
            algorithm="pagerank",
            uncertainty_method="delta",
            timestamp="2024-01-01T00:00:00Z"
        )
        data = prov.to_json_dict()
        
        assert data["timestamp"] == "2024-01-01T00:00:00Z"

    def test_to_json_dict_with_version(self):
        """Test serializing provenance with version."""
        prov = Provenance(
            algorithm="betweenness",
            uncertainty_method="bootstrap",
            library_version="1.1.3"
        )
        data = prov.to_json_dict()
        
        assert data["library_version"] == "1.1.3"

    def test_to_json_dict_excludes_none_values(self):
        """Test that None values are excluded from JSON dict."""
        prov = Provenance(
            algorithm="degree",
            uncertainty_method="none",
            seed=None,
            timestamp=None,
            library_version=None
        )
        data = prov.to_json_dict()
        
        # Should not include None values
        assert "seed" not in data
        assert "timestamp" not in data
        assert "library_version" not in data

    def test_from_json_dict_minimal(self):
        """Test deserializing minimal provenance from dict."""
        data = {
            "algorithm": "degree",
            "uncertainty_method": "none"
        }
        prov = Provenance.from_json_dict(data)
        
        assert prov.algorithm == "degree"
        assert prov.uncertainty_method == "none"

    def test_from_json_dict_with_params(self):
        """Test deserializing provenance with parameters."""
        data = {
            "algorithm": "louvain",
            "uncertainty_method": "bootstrap",
            "params": {"resolution": 1.0}
        }
        prov = Provenance.from_json_dict(data)
        
        assert prov.parameters["resolution"] == 1.0

    def test_from_json_dict_with_seed(self):
        """Test deserializing provenance with seed."""
        data = {
            "algorithm": "leiden",
            "uncertainty_method": "ensemble",
            "seed": 42
        }
        prov = Provenance.from_json_dict(data)
        
        assert prov.seed == 42

    def test_roundtrip_serialization(self):
        """Test that serialization is lossless."""
        original = Provenance(
            algorithm="betweenness",
            uncertainty_method="bootstrap",
            parameters={"n_samples": 100, "unit": "edges"},
            seed=42,
            timestamp="2024-01-01T00:00:00Z",
            library_version="1.1.3"
        )
        
        data = original.to_json_dict()
        reconstructed = Provenance.from_json_dict(data)
        
        assert reconstructed.algorithm == original.algorithm
        assert reconstructed.uncertainty_method == original.uncertainty_method
        assert reconstructed.parameters == original.parameters
        assert reconstructed.seed == original.seed
        assert reconstructed.timestamp == original.timestamp
        assert reconstructed.library_version == original.library_version


class TestProvenanceUsagePatterns:
    """Test typical usage patterns for provenance."""

    def test_provenance_for_deterministic_algorithm(self):
        """Test creating provenance for deterministic algorithm."""
        prov = Provenance(
            algorithm="degree",
            uncertainty_method="none"
        )
        assert prov.seed is None  # No seed needed for deterministic

    def test_provenance_for_stochastic_algorithm(self):
        """Test creating provenance for stochastic algorithm."""
        prov = Provenance(
            algorithm="louvain",
            uncertainty_method="ensemble",
            parameters={"resolution": 1.0},
            seed=42
        )
        assert prov.seed == 42  # Seed required for reproducibility

    def test_provenance_for_bootstrap_uq(self):
        """Test creating provenance for bootstrap UQ."""
        prov = Provenance(
            algorithm="betweenness",
            uncertainty_method="bootstrap",
            parameters={"n_samples": 100, "unit": "edges"},
            seed=42
        )
        assert prov.uncertainty_method == "bootstrap"
        assert prov.parameters["n_samples"] == 100
        assert prov.parameters["unit"] == "edges"

    def test_provenance_for_analytical_uq(self):
        """Test creating provenance for analytical UQ."""
        prov = Provenance(
            algorithm="pagerank",
            uncertainty_method="delta",
            parameters={"alpha": 0.85}
        )
        assert prov.uncertainty_method == "delta"
        assert prov.seed is None  # Analytical methods don't need seeds

    def test_provenance_equality(self):
        """Test that identical provenance objects are equal."""
        prov1 = Provenance(
            algorithm="leiden",
            uncertainty_method="bootstrap",
            seed=42
        )
        prov2 = Provenance(
            algorithm="leiden",
            uncertainty_method="bootstrap",
            seed=42
        )
        assert prov1 == prov2

    def test_provenance_inequality(self):
        """Test that different provenance objects are not equal."""
        prov1 = Provenance(
            algorithm="leiden",
            uncertainty_method="bootstrap",
            seed=42
        )
        prov2 = Provenance(
            algorithm="leiden",
            uncertainty_method="bootstrap",
            seed=43  # Different seed
        )
        assert prov1 != prov2
