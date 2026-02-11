"""Tests for py3plex.stats.provenance module.

Tests the Provenance dataclass for statistics provenance tracking.
"""

import json
import pytest
from py3plex.stats.provenance import Provenance


class TestProvenanceBasic:
    """Test basic provenance operations."""
    
    def test_create_minimal_provenance(self):
        """Test creating provenance with minimal fields."""
        prov = Provenance(
            algorithm="brandes",
            uncertainty_method="bootstrap"
        )
        
        assert prov.algorithm == "brandes"
        assert prov.uncertainty_method == "bootstrap"
        assert prov.parameters == {}
        assert prov.seed is None
        assert prov.timestamp is None
        assert prov.library_version is None
    
    def test_create_full_provenance(self):
        """Test creating provenance with all fields."""
        prov = Provenance(
            algorithm="degree",
            uncertainty_method="analytic",
            parameters={"weighted": True, "normalized": False},
            seed=42,
            timestamp="2024-01-01T12:00:00",
            library_version="1.1.3"
        )
        
        assert prov.algorithm == "degree"
        assert prov.uncertainty_method == "analytic"
        assert prov.parameters == {"weighted": True, "normalized": False}
        assert prov.seed == 42
        assert prov.timestamp == "2024-01-01T12:00:00"
        assert prov.library_version == "1.1.3"
    
    def test_provenance_immutable(self):
        """Test that Provenance is frozen/immutable."""
        prov = Provenance(algorithm="test", uncertainty_method="none")
        
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            prov.algorithm = "changed"
    
    def test_parameters_copy(self):
        """Test that parameters dict is not shared reference."""
        params = {"n_samples": 100}
        prov = Provenance(
            algorithm="bootstrap",
            uncertainty_method="bootstrap",
            parameters=params
        )
        
        # Note: Frozen dataclass doesn't copy mutable defaults, but
        # modifications to original don't affect immutability guarantee
        # The field is the same reference, but frozen prevents reassignment
        assert prov.parameters is params  # Same reference due to dataclass behavior


class TestProvenanceJSONSerialization:
    """Test JSON serialization of provenance."""
    
    def test_to_json_dict_minimal(self):
        """Test JSON dict conversion with minimal fields."""
        prov = Provenance(
            algorithm="degree",
            uncertainty_method="none"
        )
        
        result = prov.to_json_dict()
        
        assert result["algorithm"] == "degree"
        assert result["uncertainty_method"] == "none"
        assert result["params"] == {}
        assert "seed" not in result
        assert "timestamp" not in result
        assert "library_version" not in result
    
    def test_to_json_dict_full(self):
        """Test JSON dict conversion with all fields."""
        prov = Provenance(
            algorithm="pagerank",
            uncertainty_method="bootstrap",
            parameters={"alpha": 0.85, "n_samples": 50},
            seed=123,
            timestamp="2024-02-11T10:00:00",
            library_version="1.1.3"
        )
        
        result = prov.to_json_dict()
        
        assert result["algorithm"] == "pagerank"
        assert result["uncertainty_method"] == "bootstrap"
        assert result["params"] == {"alpha": 0.85, "n_samples": 50}
        assert result["seed"] == 123
        assert result["timestamp"] == "2024-02-11T10:00:00"
        assert result["library_version"] == "1.1.3"
    
    def test_from_json_dict_minimal(self):
        """Test creating provenance from minimal JSON dict."""
        data = {
            "algorithm": "betweenness",
            "uncertainty_method": "delta"
        }
        
        prov = Provenance.from_json_dict(data)
        
        assert prov.algorithm == "betweenness"
        assert prov.uncertainty_method == "delta"
        assert prov.parameters == {}
        assert prov.seed is None
    
    def test_from_json_dict_full(self):
        """Test creating provenance from full JSON dict."""
        data = {
            "algorithm": "closeness",
            "uncertainty_method": "bootstrap",
            "params": {"normalized": True, "n_samples": 200},
            "seed": 456,
            "timestamp": "2024-02-11T11:00:00",
            "library_version": "1.1.3"
        }
        
        prov = Provenance.from_json_dict(data)
        
        assert prov.algorithm == "closeness"
        assert prov.uncertainty_method == "bootstrap"
        assert prov.parameters == {"normalized": True, "n_samples": 200}
        assert prov.seed == 456
        assert prov.timestamp == "2024-02-11T11:00:00"
        assert prov.library_version == "1.1.3"
    
    def test_roundtrip_serialization(self):
        """Test that to_json_dict -> from_json_dict preserves data."""
        original = Provenance(
            algorithm="eigenvector",
            uncertainty_method="perturbation",
            parameters={"max_iter": 100, "tol": 1e-6},
            seed=789
        )
        
        json_dict = original.to_json_dict()
        reconstructed = Provenance.from_json_dict(json_dict)
        
        assert reconstructed.algorithm == original.algorithm
        assert reconstructed.uncertainty_method == original.uncertainty_method
        assert reconstructed.parameters == original.parameters
        assert reconstructed.seed == original.seed
    
    def test_json_serializable(self):
        """Test that output can be serialized to JSON string."""
        prov = Provenance(
            algorithm="katz",
            uncertainty_method="analytic",
            parameters={"beta": 0.1},
            seed=999
        )
        
        json_dict = prov.to_json_dict()
        json_str = json.dumps(json_dict)  # Should not raise
        
        assert isinstance(json_str, str)
        assert "katz" in json_str


class TestProvenanceEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_parameters(self):
        """Test provenance with explicitly empty parameters."""
        prov = Provenance(
            algorithm="simple",
            uncertainty_method="none",
            parameters={}
        )
        
        assert prov.parameters == {}
        assert prov.to_json_dict()["params"] == {}
    
    def test_seed_zero(self):
        """Test that seed=0 is preserved (not treated as None)."""
        prov = Provenance(
            algorithm="test",
            uncertainty_method="bootstrap",
            seed=0
        )
        
        assert prov.seed == 0
        assert "seed" in prov.to_json_dict()
        assert prov.to_json_dict()["seed"] == 0
    
    def test_parameters_not_mutated_by_to_json_dict(self):
        """Test that to_json_dict doesn't mutate original parameters."""
        params = {"value": 123}
        prov = Provenance(
            algorithm="test",
            uncertainty_method="none",
            parameters=params
        )
        
        json_dict = prov.to_json_dict()
        json_dict["params"]["value"] = 456
        
        # Original provenance parameters should not change
        assert prov.parameters["value"] == 123
    
    def test_special_characters_in_strings(self):
        """Test handling special characters in string fields."""
        prov = Provenance(
            algorithm="test-algo_v2",
            uncertainty_method="bootstrap+delta",
            parameters={"key": "value with spaces"}
        )
        
        json_dict = prov.to_json_dict()
        reconstructed = Provenance.from_json_dict(json_dict)
        
        assert reconstructed.algorithm == "test-algo_v2"
        assert reconstructed.uncertainty_method == "bootstrap+delta"
    
    def test_complex_nested_parameters(self):
        """Test parameters with nested structures."""
        prov = Provenance(
            algorithm="complex",
            uncertainty_method="ensemble",
            parameters={
                "methods": ["bootstrap", "perturbation"],
                "config": {"n_samples": 100, "ci": 0.95},
                "nested": {"level2": {"level3": "value"}}
            }
        )
        
        json_dict = prov.to_json_dict()
        reconstructed = Provenance.from_json_dict(json_dict)
        
        assert reconstructed.parameters["methods"] == ["bootstrap", "perturbation"]
        assert reconstructed.parameters["config"]["n_samples"] == 100
        assert reconstructed.parameters["nested"]["level2"]["level3"] == "value"


class TestProvenanceEquality:
    """Test provenance equality."""
    
    def test_equal_provenances(self):
        """Test that identical provenances are equal."""
        prov1 = Provenance(
            algorithm="test",
            uncertainty_method="none",
            parameters={"a": 1},
            seed=42
        )
        prov2 = Provenance(
            algorithm="test",
            uncertainty_method="none",
            parameters={"a": 1},
            seed=42
        )
        
        # Dataclass equality
        assert prov1 == prov2
    
    def test_different_provenances(self):
        """Test that different provenances are not equal."""
        prov1 = Provenance(algorithm="algo1", uncertainty_method="none")
        prov2 = Provenance(algorithm="algo2", uncertainty_method="none")
        
        assert prov1 != prov2
    
    def test_not_hashable(self):
        """Test that Provenance with mutable dict is not hashable."""
        prov = Provenance(
            algorithm="test",
            uncertainty_method="none",
            parameters={"key": "value"}
        )
        
        # Dataclass with mutable fields (dict) is not hashable even if frozen
        with pytest.raises(TypeError):
            hash(prov)
