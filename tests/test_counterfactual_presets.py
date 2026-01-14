"""Additional tests for counterfactual presets module.

This test suite covers edge cases and functions not tested in the main
test_counterfactual.py file.
"""

import pytest
from py3plex.counterfactual import (
    get_preset,
    list_presets,
    RemoveEdgesSpec,
    RewireDegreePreservingSpec,
    ShuffleWeightsSpec,
    PRESET_QUICK,
    PRESET_DEGREE_SAFE,
    PRESET_LAYER_SAFE,
    PRESET_WEIGHT_ONLY,
    PRESET_TARGETED,
)
from py3plex.counterfactual.presets import get_default_preset


class TestPresetEdgeCases:
    """Test edge cases for preset configurations."""
    
    def test_layer_safe_preset(self):
        """Test layer_safe preset returns ShuffleWeightsSpec."""
        spec = get_preset("layer_safe", strength="medium")
        
        assert isinstance(spec, ShuffleWeightsSpec)
        assert spec.preserve_layer is True
    
    def test_weight_only_preset(self):
        """Test weight_only preset returns ShuffleWeightsSpec."""
        spec = get_preset("weight_only", strength="light")
        
        assert isinstance(spec, ShuffleWeightsSpec)
        assert spec.preserve_layer is True
    
    def test_targeted_preset_without_targets(self):
        """Test targeted preset without targets uses targeted mode."""
        spec = get_preset("targeted", strength="heavy")
        
        assert isinstance(spec, RemoveEdgesSpec)
        assert spec.mode == "targeted"
        assert spec.proportion == 0.30  # heavy = 30%
    
    def test_targeted_preset_with_targets(self):
        """Test targeted preset with targets uses random mode."""
        spec = get_preset("targeted", strength="medium", targets=["node1", "node2"])
        
        assert isinstance(spec, RemoveEdgesSpec)
        assert spec.mode == "random"
        assert spec.on == ["node1", "node2"]
    
    def test_get_default_preset(self):
        """Test that default preset returns degree_safe."""
        spec = get_default_preset()
        
        assert isinstance(spec, RewireDegreePreservingSpec)
    
    def test_get_default_preset_with_strength(self):
        """Test default preset with different strengths."""
        light = get_default_preset(strength="light")
        medium = get_default_preset(strength="medium")
        heavy = get_default_preset(strength="heavy")
        
        assert light.n_swaps == 50
        assert medium.n_swaps == 200
        assert heavy.n_swaps == 500
    
    def test_all_presets_have_descriptions(self):
        """Test that all preset constants have descriptions."""
        presets = list_presets()
        
        assert PRESET_QUICK in presets
        assert PRESET_DEGREE_SAFE in presets
        assert PRESET_LAYER_SAFE in presets
        assert PRESET_WEIGHT_ONLY in presets
        assert PRESET_TARGETED in presets
    
    def test_quick_preset_strength_variations(self):
        """Test quick preset returns correct proportions for all strengths."""
        light = get_preset("quick", strength="light")
        medium = get_preset("quick", strength="medium")
        heavy = get_preset("quick", strength="heavy")
        
        assert light.proportion == 0.02
        assert medium.proportion == 0.05
        assert heavy.proportion == 0.10
    
    def test_degree_safe_preset_strength_variations(self):
        """Test degree_safe preset returns correct n_swaps for all strengths."""
        light = get_preset("degree_safe", strength="light")
        medium = get_preset("degree_safe", strength="medium")
        heavy = get_preset("degree_safe", strength="heavy")
        
        assert light.n_swaps == 50
        assert medium.n_swaps == 200
        assert heavy.n_swaps == 500
    
    def test_targeted_preset_strength_variations(self):
        """Test targeted preset returns correct proportions for all strengths."""
        light = get_preset("targeted", strength="light")
        medium = get_preset("targeted", strength="medium")
        heavy = get_preset("targeted", strength="heavy")
        
        assert light.proportion == 0.05
        assert medium.proportion == 0.15
        assert heavy.proportion == 0.30
    
    def test_preset_with_targets_parameter(self):
        """Test that presets accept targets parameter."""
        targets = ["node1", "node2"]
        
        # Test with quick preset
        spec = get_preset("quick", strength="medium", targets=targets)
        assert spec.on == targets
        
        # Test with degree_safe preset
        spec = get_preset("degree_safe", strength="medium", targets=targets)
        assert spec.on == targets
    
    def test_list_presets_returns_dict(self):
        """Test that list_presets returns a dictionary."""
        presets = list_presets()
        
        assert isinstance(presets, dict)
        assert len(presets) == 5  # All 5 presets
        
        # Check all values are strings (descriptions)
        for value in presets.values():
            assert isinstance(value, str)
            assert len(value) > 0


class TestPresetHashability:
    """Test that preset specs are hashable and immutable."""
    
    def test_quick_preset_is_hashable(self):
        """Test that quick preset creates hashable spec."""
        spec = get_preset("quick", strength="medium")
        
        # Should be able to hash it
        hash_val = hash(spec.spec_hash())
        assert isinstance(hash_val, int)
    
    def test_degree_safe_preset_is_hashable(self):
        """Test that degree_safe preset creates hashable spec."""
        spec = get_preset("degree_safe", strength="light")
        
        hash_val = hash(spec.spec_hash())
        assert isinstance(hash_val, int)
    
    def test_same_preset_same_hash(self):
        """Test that same presets produce same hash."""
        spec1 = get_preset("quick", strength="medium")
        spec2 = get_preset("quick", strength="medium")
        
        assert spec1.spec_hash() == spec2.spec_hash()
    
    def test_different_preset_different_hash(self):
        """Test that different presets produce different hashes."""
        spec1 = get_preset("quick", strength="light")
        spec2 = get_preset("quick", strength="heavy")
        
        assert spec1.spec_hash() != spec2.spec_hash()


class TestPresetSerialization:
    """Test preset serialization."""
    
    def test_quick_preset_serializable(self):
        """Test that quick preset can be serialized."""
        spec = get_preset("quick", strength="medium")
        
        data = spec.to_dict()
        assert isinstance(data, dict)
        assert "type" in data
        assert data["type"] == "remove_edges"
    
    def test_degree_safe_preset_serializable(self):
        """Test that degree_safe preset can be serialized."""
        spec = get_preset("degree_safe", strength="heavy")
        
        data = spec.to_dict()
        assert isinstance(data, dict)
        assert "type" in data
        assert data["type"] == "rewire_degree_preserving"
    
    def test_weight_only_preset_serializable(self):
        """Test that weight_only preset can be serialized."""
        spec = get_preset("weight_only", strength="light")
        
        data = spec.to_dict()
        assert isinstance(data, dict)
        assert "type" in data
        assert data["type"] == "shuffle_weights"
