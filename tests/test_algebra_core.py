"""Tests for semiring algebra core components."""

import pytest
import math
from py3plex.algebra import (
    BooleanSemiring,
    MinPlusSemiring,
    MaxPlusSemiring,
    MaxTimesSemiring,
    get_semiring,
    list_semirings,
    register_semiring,
    WeightLiftSpec,
    lift_edge_value,
)
from py3plex.exceptions import Py3plexException


class TestSemiringLaws:
    """Test semiring identity laws and basic properties."""
    
    def test_boolean_semiring_identities(self):
        """Test Boolean semiring satisfies semiring laws."""
        sr = BooleanSemiring()
        
        # Additive identity: a ⊕ 0 = a
        assert sr.add(True, sr.zero()) == True
        assert sr.add(False, sr.zero()) == False
        
        # Multiplicative identity: a ⊗ 1 = a
        assert sr.mul(True, sr.one()) == True
        assert sr.mul(False, sr.one()) == False
        
        # Zero annihilator: a ⊗ 0 = 0
        assert sr.mul(True, sr.zero()) == sr.zero()
        assert sr.mul(False, sr.zero()) == sr.zero()
        
        # Idempotence: a ⊕ a = a
        assert sr.add(True, True) == True
        assert sr.add(False, False) == False
    
    def test_min_plus_semiring_identities(self):
        """Test min-plus semiring satisfies semiring laws."""
        sr = MinPlusSemiring()
        
        # Additive identity: min(a, ∞) = a
        assert sr.add(5.0, sr.zero()) == 5.0
        assert sr.add(0.0, sr.zero()) == 0.0
        
        # Multiplicative identity: a + 0 = a
        assert sr.mul(5.0, sr.one()) == 5.0
        assert sr.mul(-2.0, sr.one()) == -2.0
        
        # Zero annihilator: a + ∞ = ∞
        assert math.isinf(sr.mul(5.0, sr.zero()))
        
        # Idempotence: min(a, a) = a
        assert sr.add(5.0, 5.0) == 5.0
    
    def test_max_plus_semiring_identities(self):
        """Test max-plus semiring satisfies semiring laws."""
        sr = MaxPlusSemiring()
        
        # Additive identity: max(a, -∞) = a
        assert sr.add(5.0, sr.zero()) == 5.0
        assert sr.add(-10.0, sr.zero()) == -10.0
        
        # Multiplicative identity: a + 0 = a
        assert sr.mul(5.0, sr.one()) == 5.0
        assert sr.mul(-2.0, sr.one()) == -2.0
    
    def test_max_times_semiring_identities(self):
        """Test max-times semiring satisfies semiring laws."""
        sr = MaxTimesSemiring()
        
        # Additive identity: max(a, 0) = a (for a >= 0)
        assert sr.add(0.8, sr.zero()) == 0.8
        assert sr.add(0.0, sr.zero()) == 0.0
        
        # Multiplicative identity: a * 1 = a
        assert sr.mul(0.8, sr.one()) == 0.8
        assert sr.mul(0.5, sr.one()) == 0.5
        
        # Zero annihilator: a * 0 = 0
        assert sr.mul(0.9, sr.zero()) == 0.0


class TestSemiringRegistry:
    """Test semiring registry functionality."""
    
    def test_list_semirings_deterministic(self):
        """Test that list_semirings returns sorted list."""
        semirings = list_semirings()
        assert semirings == sorted(semirings)
        # Check built-ins are present
        assert "boolean" in semirings
        assert "min_plus" in semirings
        assert "max_plus" in semirings
        assert "max_times" in semirings
    
    def test_get_semiring(self):
        """Test getting semirings by name."""
        sr = get_semiring("min_plus")
        assert sr.name == "min_plus"
        assert sr.zero() == math.inf
        assert sr.one() == 0.0
    
    def test_get_unknown_semiring(self):
        """Test error for unknown semiring."""
        with pytest.raises(Py3plexException, match="Unknown semiring"):
            get_semiring("unknown_semiring_xyz")
    
    def test_register_duplicate_without_overwrite(self):
        """Test that registering duplicate without overwrite raises error."""
        sr = MinPlusSemiring()
        with pytest.raises(Py3plexException, match="already registered"):
            register_semiring("min_plus", sr, overwrite=False)
    
    def test_register_with_overwrite(self):
        """Test that overwrite=True allows replacing semiring."""
        sr = MinPlusSemiring()
        # Should not raise
        register_semiring("min_plus", sr, overwrite=True)


class TestWeightLiftSpec:
    """Test weight lifting specifications."""
    
    def test_simple_attribute_extraction(self):
        """Test extracting attribute from edge."""
        spec = WeightLiftSpec(attr="weight", default=1.0)
        attrs = {"weight": 2.5, "label": "A"}
        
        value = lift_edge_value(attrs, spec)
        assert value == 2.5
    
    def test_missing_attribute_with_default(self):
        """Test default value when attribute missing."""
        spec = WeightLiftSpec(attr="cost", default=1.0, on_missing="default")
        attrs = {"weight": 2.5}
        
        value = lift_edge_value(attrs, spec)
        assert value == 1.0
    
    def test_missing_attribute_fail(self):
        """Test exception when attribute missing and on_missing='fail'."""
        spec = WeightLiftSpec(attr="cost", on_missing="fail")
        attrs = {"weight": 2.5}
        
        with pytest.raises(Py3plexException, match="not found"):
            lift_edge_value(attrs, spec)
    
    def test_missing_attribute_drop(self):
        """Test None returned when attribute missing and on_missing='drop'."""
        spec = WeightLiftSpec(attr="cost", on_missing="drop")
        attrs = {"weight": 2.5}
        
        value = lift_edge_value(attrs, spec)
        assert value is None
    
    def test_log_transformation(self):
        """Test log transformation."""
        spec = WeightLiftSpec(attr="p", transform="log", default=1.0)
        attrs = {"p": math.e}
        
        value = lift_edge_value(attrs, spec)
        assert abs(value - 1.0) < 1e-10
    
    def test_log_transformation_nonpositive(self):
        """Test log transformation with non-positive value."""
        spec = WeightLiftSpec(attr="p", transform="log")
        attrs = {"p": 0.0}
        
        value = lift_edge_value(attrs, spec)
        assert value == -math.inf
    
    def test_custom_transformation(self):
        """Test custom transformation function."""
        spec = WeightLiftSpec(
            attr="reliability",
            transform=lambda x: 1.0 - x,
            default=0.5
        )
        attrs = {"reliability": 0.8}
        
        value = lift_edge_value(attrs, spec)
        assert abs(value - 0.2) < 1e-10
    
    def test_no_attribute_uses_default(self):
        """Test that attr=None uses default value."""
        spec = WeightLiftSpec(attr=None, default=3.0)
        attrs = {"weight": 2.5}
        
        value = lift_edge_value(attrs, spec)
        assert value == 3.0
    
    def test_invalid_on_missing(self):
        """Test exception for invalid on_missing value."""
        with pytest.raises(Py3plexException, match="Invalid on_missing"):
            WeightLiftSpec(attr="weight", on_missing="invalid")
    
    def test_invalid_transform(self):
        """Test exception for invalid transform."""
        with pytest.raises(Py3plexException, match="Invalid transform"):
            WeightLiftSpec(attr="weight", transform=123)


class TestSemiringBehavior:
    """Test semiring-specific behaviors."""
    
    def test_min_plus_better(self):
        """Test min_plus better() ordering."""
        sr = MinPlusSemiring()
        assert sr.better(2.0, 5.0) == True
        assert sr.better(5.0, 2.0) == False
        assert sr.better(3.0, 3.0) == False
    
    def test_max_times_better(self):
        """Test max_times better() ordering."""
        sr = MaxTimesSemiring()
        assert sr.better(0.9, 0.5) == True
        assert sr.better(0.5, 0.9) == False
        assert sr.better(0.7, 0.7) == False
    
    def test_boolean_better(self):
        """Test boolean better() ordering."""
        sr = BooleanSemiring()
        assert sr.better(True, False) == True
        assert sr.better(False, True) == False
        assert sr.better(True, True) == False
    
    def test_semiring_properties(self):
        """Test that semirings expose props metadata."""
        sr = MinPlusSemiring()
        props = sr.props
        
        assert props["idempotent_add"] == True
        assert props["monotone"] == True
        assert props["commutative_add"] == True
