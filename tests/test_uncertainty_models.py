"""Tests for uncertainty.models module (UncertainValue)."""

import numpy as np
import pytest

from py3plex.uncertainty.models import UncertainValue


class TestUncertainValueDeterministic:
    """Test deterministic UncertainValue."""
    
    def test_create_deterministic(self):
        """Test creating a deterministic value."""
        v = UncertainValue(kind="deterministic", params={"value": 5.0})
        assert v.kind == "deterministic"
        assert v.mean() == 5.0
        assert v.var() == 0.0
        assert v.std() == 0.0
        assert v.is_deterministic()
    
    def test_deterministic_sample(self):
        """Test sampling from deterministic value."""
        v = UncertainValue(kind="deterministic", params={"value": 3.0})
        rng = np.random.default_rng(42)
        samples = v.sample(rng, n=10)
        assert len(samples) == 10
        assert np.all(samples == 3.0)
    
    def test_deterministic_to_dict(self):
        """Test serialization of deterministic value."""
        v = UncertainValue(kind="deterministic", params={"value": 2.5})
        d = v.to_dict()
        assert d == {"kind": "deterministic", "params": {"value": 2.5}}
    
    def test_deterministic_float_conversion(self):
        """Test converting to float."""
        v = UncertainValue(kind="deterministic", params={"value": 7.5})
        assert float(v) == 7.5
    
    def test_deterministic_repr(self):
        """Test string representation."""
        v = UncertainValue(kind="deterministic", params={"value": 1.0})
        assert "1.0" in repr(v)


class TestUncertainValueBernoulli:
    """Test Bernoulli UncertainValue."""
    
    def test_create_bernoulli(self):
        """Test creating a Bernoulli value."""
        v = UncertainValue(kind="bernoulli", params={"p": 0.7})
        assert v.kind == "bernoulli"
        assert v.mean() == 0.7
        assert np.isclose(v.var(), 0.7 * 0.3)
        assert not v.is_deterministic()
    
    def test_bernoulli_sample(self):
        """Test sampling from Bernoulli distribution."""
        v = UncertainValue(kind="bernoulli", params={"p": 0.5})
        rng = np.random.default_rng(42)
        samples = v.sample(rng, n=1000)
        assert len(samples) == 1000
        # All samples should be 0 or 1
        assert np.all((samples == 0) | (samples == 1))
        # Mean should be close to p (with large n)
        assert np.isclose(np.mean(samples), 0.5, atol=0.1)
    
    def test_bernoulli_edge_cases(self):
        """Test Bernoulli edge cases (p=0 and p=1)."""
        v0 = UncertainValue(kind="bernoulli", params={"p": 0.0})
        assert v0.mean() == 0.0
        assert v0.var() == 0.0
        assert v0.is_deterministic()  # p=0 is deterministic
        
        v1 = UncertainValue(kind="bernoulli", params={"p": 1.0})
        assert v1.mean() == 1.0
        assert v1.var() == 0.0
        assert v1.is_deterministic()  # p=1 is deterministic
    
    def test_bernoulli_invalid_p(self):
        """Test that invalid p values are rejected."""
        with pytest.raises(ValueError, match="p must be in"):
            UncertainValue(kind="bernoulli", params={"p": 1.5})
        
        with pytest.raises(ValueError, match="p must be in"):
            UncertainValue(kind="bernoulli", params={"p": -0.1})
    
    def test_bernoulli_repr(self):
        """Test string representation."""
        v = UncertainValue(kind="bernoulli", params={"p": 0.8})
        assert "Bernoulli" in repr(v)
        assert "0.8" in repr(v)


class TestUncertainValueNormal:
    """Test Normal/Gaussian UncertainValue."""
    
    def test_create_normal(self):
        """Test creating a Normal value."""
        v = UncertainValue(kind="normal", params={"mu": 10.0, "sigma": 2.0})
        assert v.kind == "normal"
        assert v.mean() == 10.0
        assert v.var() == 4.0
        assert v.std() == 2.0
        assert not v.is_deterministic()
    
    def test_normal_sample(self):
        """Test sampling from Normal distribution."""
        v = UncertainValue(kind="normal", params={"mu": 0.0, "sigma": 1.0})
        rng = np.random.default_rng(42)
        samples = v.sample(rng, n=1000)
        assert len(samples) == 1000
        # Check mean and std are close to expected (with large n)
        assert np.isclose(np.mean(samples), 0.0, atol=0.15)
        assert np.isclose(np.std(samples), 1.0, atol=0.15)
    
    def test_normal_zero_sigma(self):
        """Test Normal with sigma=0 (deterministic)."""
        v = UncertainValue(kind="normal", params={"mu": 5.0, "sigma": 0.0})
        assert v.mean() == 5.0
        assert v.var() == 0.0
        assert v.is_deterministic()
        
        rng = np.random.default_rng(42)
        samples = v.sample(rng, n=10)
        assert np.all(samples == 5.0)
    
    def test_normal_invalid_sigma(self):
        """Test that negative sigma is rejected."""
        with pytest.raises(ValueError, match="sigma must be >= 0"):
            UncertainValue(kind="normal", params={"mu": 0.0, "sigma": -1.0})
    
    def test_normal_repr(self):
        """Test string representation."""
        v = UncertainValue(kind="normal", params={"mu": 5.0, "sigma": 1.0})
        assert "Normal" in repr(v)
        assert "5.0" in repr(v)
        assert "1.0" in repr(v)


class TestUncertainValueEmpirical:
    """Test Empirical UncertainValue."""
    
    def test_create_empirical(self):
        """Test creating an Empirical value."""
        samples = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        v = UncertainValue(kind="empirical", params={"samples": samples})
        assert v.kind == "empirical"
        assert v.mean() == 3.0
        assert np.isclose(v.var(), 2.0)  # variance of [1,2,3,4,5]
    
    def test_empirical_sample(self):
        """Test resampling from empirical distribution."""
        samples = np.array([1.0, 2.0, 3.0])
        v = UncertainValue(kind="empirical", params={"samples": samples})
        rng = np.random.default_rng(42)
        new_samples = v.sample(rng, n=100)
        assert len(new_samples) == 100
        # All samples should be from original set
        assert np.all(np.isin(new_samples, samples))
    
    def test_empirical_from_list(self):
        """Test creating empirical from Python list."""
        samples_list = [1.0, 2.0, 3.0, 4.0]
        v = UncertainValue(kind="empirical", params={"samples": samples_list})
        # Should convert to numpy array
        assert isinstance(v.params["samples"], np.ndarray)
        assert v.mean() == 2.5
    
    def test_empirical_to_dict(self):
        """Test serialization of empirical value."""
        samples = np.array([1.0, 2.0, 3.0])
        v = UncertainValue(kind="empirical", params={"samples": samples})
        d = v.to_dict()
        assert d["kind"] == "empirical"
        assert d["params"]["samples"] == [1.0, 2.0, 3.0]  # converted to list
    
    def test_empirical_repr(self):
        """Test string representation."""
        samples = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        v = UncertainValue(kind="empirical", params={"samples": samples})
        assert "Empirical" in repr(v)
        assert "5" in repr(v)  # number of samples


class TestUncertainValueValidation:
    """Test validation and error handling."""
    
    def test_invalid_kind(self):
        """Test that invalid kind is rejected."""
        with pytest.raises(ValueError, match="Invalid kind"):
            UncertainValue(kind="invalid", params={})
    
    def test_missing_params_deterministic(self):
        """Test that missing 'value' for deterministic is rejected."""
        with pytest.raises(ValueError, match="requires 'value'"):
            UncertainValue(kind="deterministic", params={})
    
    def test_missing_params_bernoulli(self):
        """Test that missing 'p' for bernoulli is rejected."""
        with pytest.raises(ValueError, match="requires 'p'"):
            UncertainValue(kind="bernoulli", params={})
    
    def test_missing_params_normal(self):
        """Test that missing params for normal is rejected."""
        with pytest.raises(ValueError, match="requires 'mu' and 'sigma'"):
            UncertainValue(kind="normal", params={"mu": 0.0})
        
        with pytest.raises(ValueError, match="requires 'mu' and 'sigma'"):
            UncertainValue(kind="normal", params={"sigma": 1.0})
    
    def test_missing_params_empirical(self):
        """Test that missing 'samples' for empirical is rejected."""
        with pytest.raises(ValueError, match="requires 'samples'"):
            UncertainValue(kind="empirical", params={})


class TestUncertainValueConversion:
    """Test conversion methods."""
    
    def test_from_dict(self):
        """Test creating from dictionary."""
        d = {"kind": "normal", "params": {"mu": 5.0, "sigma": 1.0}}
        v = UncertainValue.from_dict(d)
        assert v.kind == "normal"
        assert v.mean() == 5.0
        assert v.std() == 1.0
    
    def test_from_value_scalar(self):
        """Test creating from scalar value."""
        v = UncertainValue.from_value(3.5)
        assert v.kind == "deterministic"
        assert v.mean() == 3.5
        assert v.is_deterministic()
    
    def test_from_value_int(self):
        """Test creating from integer."""
        v = UncertainValue.from_value(10)
        assert v.kind == "deterministic"
        assert v.mean() == 10.0
    
    def test_from_value_uncertain(self):
        """Test that from_value preserves UncertainValue."""
        v1 = UncertainValue(kind="normal", params={"mu": 1.0, "sigma": 0.5})
        v2 = UncertainValue.from_value(v1)
        assert v2 is v1  # Should be same object
    
    def test_roundtrip_to_from_dict(self):
        """Test roundtrip conversion to/from dict."""
        v1 = UncertainValue(kind="bernoulli", params={"p": 0.7})
        d = v1.to_dict()
        v2 = UncertainValue.from_dict(d)
        assert v2.kind == v1.kind
        assert v2.params == v1.params
        assert v2.mean() == v1.mean()


class TestUncertainValueComparison:
    """Test comparisons between different kinds."""
    
    def test_different_distributions_same_mean(self):
        """Test different distributions with same mean."""
        v1 = UncertainValue(kind="deterministic", params={"value": 5.0})
        v2 = UncertainValue(kind="normal", params={"mu": 5.0, "sigma": 1.0})
        v3 = UncertainValue(kind="bernoulli", params={"p": 1.0})  # mean = 1.0
        
        assert v1.mean() == v2.mean()
        assert v1.var() < v2.var()  # deterministic has zero variance
        assert v1.is_deterministic()
        assert not v2.is_deterministic()
        
        # Bernoulli with p=1 should be deterministic
        assert v3.is_deterministic()
