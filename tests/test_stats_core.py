"""Tests for core stats module (StatValue, Uncertainty models, Provenance).

This test module covers:
- Delta, Gaussian, Bootstrap, Empirical, Interval uncertainty models
- StatValue arithmetic with uncertainty propagation
- Provenance tracking
- Serialization
"""

import pytest
import numpy as np

from py3plex.stats import (
    StatValue,
    Delta,
    Gaussian,
    Bootstrap,
    Empirical,
    Interval,
    Provenance,
)


class TestDelta:
    """Tests for Delta uncertainty model."""
    
    def test_delta_zero(self):
        """Test perfect certainty (sigma=0)."""
        d = Delta(0.0)
        assert d.std() == 0.0
        assert d.ci() == (0.0, 0.0)
        samples = d.sample(10, seed=42)
        assert np.all(samples == 0.0)
    
    def test_delta_small(self):
        """Test small known error."""
        d = Delta(0.01)
        assert d.std() == 0.01
        low, high = d.ci(0.95)
        # For 95% CI, approximately ±1.96*sigma
        assert abs(low) < 0.02
        assert abs(high) < 0.02
    
    def test_delta_propagation_add(self):
        """Test addition propagation for Delta."""
        d1 = Delta(0.1)
        d2 = Delta(0.15)
        result = d1.propagate("+", d2)
        assert isinstance(result, Delta)
        # σ_sum = sqrt(0.1² + 0.15²) ≈ 0.180
        assert abs(result.std() - 0.180) < 0.01
    
    def test_delta_serialization(self):
        """Test JSON serialization."""
        d = Delta(0.05)
        json_dict = d.to_json_dict()
        assert json_dict["type"] == "delta"
        assert json_dict["sigma"] == 0.05


class TestGaussian:
    """Tests for Gaussian uncertainty model."""
    
    def test_gaussian_basic(self):
        """Test basic Gaussian properties."""
        g = Gaussian(mean=0.0, std_dev=0.1)
        assert g.std() == 0.1
        low, high = g.ci(0.95)
        # For N(0, 0.1), 95% CI ≈ (-0.196, 0.196)
        assert abs(low + 0.196) < 0.01
        assert abs(high - 0.196) < 0.01
    
    def test_gaussian_sampling(self):
        """Test Gaussian sampling."""
        g = Gaussian(mean=0.0, std_dev=0.1)
        samples = g.sample(1000, seed=42)
        assert len(samples) == 1000
        # Check mean and std are roughly correct
        assert abs(np.mean(samples)) < 0.02  # Should be close to 0
        assert abs(np.std(samples) - 0.1) < 0.02  # Should be close to 0.1
    
    def test_gaussian_propagation_add(self):
        """Test addition for Gaussian."""
        g1 = Gaussian(0.0, 0.1)
        g2 = Gaussian(0.0, 0.15)
        result = g1.propagate("+", g2)
        assert isinstance(result, Gaussian)
        expected_std = np.sqrt(0.1**2 + 0.15**2)
        assert abs(result.std() - expected_std) < 0.01
    
    def test_gaussian_propagation_sub(self):
        """Test subtraction for Gaussian."""
        g1 = Gaussian(0.0, 0.1)
        g2 = Gaussian(0.0, 0.15)
        result = g1.propagate("-", g2)
        assert isinstance(result, Gaussian)
        expected_std = np.sqrt(0.1**2 + 0.15**2)
        assert abs(result.std() - expected_std) < 0.01
    
    def test_gaussian_serialization(self):
        """Test JSON serialization."""
        g = Gaussian(0.0, 0.1)
        json_dict = g.to_json_dict()
        assert json_dict["type"] == "gaussian"
        assert json_dict["mean"] == 0.0
        assert json_dict["std"] == 0.1


class TestBootstrap:
    """Tests for Bootstrap uncertainty model."""
    
    def test_bootstrap_basic(self):
        """Test basic Bootstrap properties."""
        samples = np.array([0.1, -0.05, 0.15, 0.0, 0.08])
        b = Bootstrap(samples)
        assert b.std() > 0
        low, high = b.ci(0.95)
        assert low < high
    
    def test_bootstrap_ci_percentile(self):
        """Test percentile-based CI."""
        samples = np.linspace(-0.1, 0.1, 100)
        b = Bootstrap(samples)
        low, high = b.ci(0.95)
        # For uniform distribution, 95% CI should capture most of the range
        assert low < 0
        assert high > 0
    
    def test_bootstrap_resampling(self):
        """Test resampling from bootstrap samples."""
        samples = np.array([0.1, 0.2, 0.3])
        b = Bootstrap(samples)
        resampled = b.sample(10, seed=42)
        assert len(resampled) == 10
        # All resampled values should be in original samples
        assert all(v in samples for v in resampled)
    
    def test_bootstrap_serialization(self):
        """Test JSON serialization (without full samples)."""
        samples = np.array([0.1, -0.05, 0.15, 0.0, 0.08])
        b = Bootstrap(samples)
        json_dict = b.to_json_dict()
        assert json_dict["type"] == "bootstrap"
        assert json_dict["n"] == 5
        assert "std" in json_dict
        assert "ci95" in json_dict


class TestEmpirical:
    """Tests for Empirical uncertainty model."""
    
    def test_empirical_basic(self):
        """Test basic Empirical properties."""
        samples = np.array([0.1, 0.2, 0.15, 0.18, 0.12])
        e = Empirical(samples)
        assert e.std() > 0
        low, high = e.ci(0.95)
        assert low < high
    
    def test_empirical_serialization(self):
        """Test JSON serialization."""
        samples = np.array([0.1, 0.2, 0.15])
        e = Empirical(samples)
        json_dict = e.to_json_dict()
        assert json_dict["type"] == "empirical"
        assert json_dict["n"] == 3


class TestInterval:
    """Tests for Interval uncertainty model."""
    
    def test_interval_basic(self):
        """Test basic Interval properties."""
        i = Interval(-0.1, 0.15)
        low, high = i.ci()
        assert low == -0.1
        assert high == 0.15
    
    def test_interval_std(self):
        """Test std estimation (uniform assumption)."""
        i = Interval(-0.1, 0.1)
        # For uniform on [-0.1, 0.1], std = 0.2 / sqrt(12) ≈ 0.0577
        expected_std = 0.2 / np.sqrt(12)
        assert abs(i.std() - expected_std) < 0.01
    
    def test_interval_sampling(self):
        """Test uniform sampling from interval."""
        i = Interval(-0.1, 0.2)
        samples = i.sample(100, seed=42)
        assert len(samples) == 100
        assert all(-0.1 <= s <= 0.2 for s in samples)
    
    def test_interval_serialization(self):
        """Test JSON serialization."""
        i = Interval(-0.1, 0.15)
        json_dict = i.to_json_dict()
        assert json_dict["type"] == "interval"
        assert json_dict["low"] == -0.1
        assert json_dict["high"] == 0.15


class TestProvenance:
    """Tests for Provenance tracking."""
    
    def test_provenance_basic(self):
        """Test basic provenance creation."""
        p = Provenance(
            algorithm="brandes",
            uncertainty_method="bootstrap",
            parameters={"n_samples": 100},
            seed=42
        )
        assert p.algorithm == "brandes"
        assert p.uncertainty_method == "bootstrap"
        assert p.seed == 42
    
    def test_provenance_serialization(self):
        """Test JSON serialization."""
        p = Provenance(
            algorithm="degree",
            uncertainty_method="delta",
            parameters={},
            seed=None
        )
        json_dict = p.to_json_dict()
        assert json_dict["algorithm"] == "degree"
        assert json_dict["uncertainty_method"] == "delta"
        assert "seed" not in json_dict or json_dict["seed"] is None
    
    def test_provenance_deserialization(self):
        """Test round-trip serialization."""
        p = Provenance(
            algorithm="betweenness",
            uncertainty_method="analytic",
            parameters={"normalized": True},
            seed=123
        )
        json_dict = p.to_json_dict()
        p2 = Provenance.from_json_dict(json_dict)
        assert p2.algorithm == p.algorithm
        assert p2.uncertainty_method == p.uncertainty_method
        assert p2.seed == p.seed


class TestStatValue:
    """Tests for StatValue container."""
    
    def test_statvalue_deterministic(self):
        """Test deterministic StatValue."""
        sv = StatValue(
            value=0.42,
            uncertainty=Delta(0.0),
            provenance=Provenance("degree", "delta", {})
        )
        assert float(sv) == 0.42
        assert sv.std() == 0.0
        assert sv.robustness() == 1.0
    
    def test_statvalue_with_uncertainty(self):
        """Test StatValue with uncertainty."""
        sv = StatValue(
            value=0.5,
            uncertainty=Gaussian(0.0, 0.05),
            provenance=Provenance("betweenness", "analytic", {})
        )
        assert float(sv) == 0.5
        assert sv.std() == 0.05
        low, high = sv.ci(0.95)
        assert low < 0.5 < high
    
    def test_statvalue_add(self):
        """Test addition of StatValues."""
        sv1 = StatValue(0.3, Delta(0.0), Provenance("a", "delta", {}))
        sv2 = StatValue(0.2, Delta(0.0), Provenance("b", "delta", {}))
        result = sv1 + sv2
        assert float(result) == 0.5
        assert isinstance(result, StatValue)
    
    def test_statvalue_add_scalar(self):
        """Test addition with scalar."""
        sv = StatValue(0.3, Delta(0.0), Provenance("a", "delta", {}))
        result = sv + 0.2
        assert float(result) == 0.5
    
    def test_statvalue_sub(self):
        """Test subtraction of StatValues."""
        sv1 = StatValue(0.5, Delta(0.0), Provenance("a", "delta", {}))
        sv2 = StatValue(0.2, Delta(0.0), Provenance("b", "delta", {}))
        result = sv1 - sv2
        assert float(result) == 0.3
    
    def test_statvalue_mul(self):
        """Test multiplication of StatValues."""
        sv1 = StatValue(2.0, Delta(0.0), Provenance("a", "delta", {}))
        sv2 = StatValue(3.0, Delta(0.0), Provenance("b", "delta", {}))
        result = sv1 * sv2
        assert float(result) == 6.0
    
    def test_statvalue_mul_scalar(self):
        """Test multiplication with scalar."""
        sv = StatValue(2.0, Delta(0.0), Provenance("a", "delta", {}))
        result = sv * 3
        assert float(result) == 6.0
    
    def test_statvalue_div(self):
        """Test division of StatValues."""
        sv1 = StatValue(6.0, Delta(0.0), Provenance("a", "delta", {}))
        sv2 = StatValue(2.0, Delta(0.0), Provenance("b", "delta", {}))
        result = sv1 / sv2
        assert float(result) == 3.0
    
    def test_statvalue_div_scalar(self):
        """Test division by scalar."""
        sv = StatValue(6.0, Delta(0.0), Provenance("a", "delta", {}))
        result = sv / 2
        assert float(result) == 3.0
    
    def test_statvalue_neg(self):
        """Test negation."""
        sv = StatValue(0.5, Delta(0.0), Provenance("a", "delta", {}))
        result = -sv
        assert float(result) == -0.5
    
    def test_statvalue_propagation(self):
        """Test uncertainty propagation through arithmetic."""
        sv1 = StatValue(1.0, Gaussian(0.0, 0.1), Provenance("a", "gaussian", {}))
        sv2 = StatValue(2.0, Gaussian(0.0, 0.15), Provenance("b", "gaussian", {}))
        result = sv1 + sv2
        # Uncertainty should propagate
        assert result.std() > 0
        # For Gaussian addition, std = sqrt(0.1² + 0.15²) ≈ 0.180
        expected_std = np.sqrt(0.1**2 + 0.15**2)
        assert abs(result.std() - expected_std) < 0.01
    
    def test_statvalue_robustness(self):
        """Test robustness calculation."""
        # High robustness (low relative uncertainty)
        sv1 = StatValue(1.0, Gaussian(0.0, 0.01), Provenance("a", "gaussian", {}))
        assert sv1.robustness() > 0.9
        
        # Low robustness (high relative uncertainty)
        sv2 = StatValue(1.0, Gaussian(0.0, 1.0), Provenance("b", "gaussian", {}))
        assert sv2.robustness() < 0.6
    
    def test_statvalue_zero_handling(self):
        """Test robustness with zero value."""
        # Deterministic zero
        sv1 = StatValue(0.0, Delta(0.0), Provenance("a", "delta", {}))
        assert sv1.robustness() == 1.0
        
        # Uncertain zero
        sv2 = StatValue(0.0, Gaussian(0.0, 0.1), Provenance("b", "gaussian", {}))
        assert sv2.robustness() == 0.0
    
    def test_statvalue_serialization(self):
        """Test JSON serialization."""
        sv = StatValue(
            value=0.42,
            uncertainty=Delta(0.01),
            provenance=Provenance("degree", "delta", {"n": 100})
        )
        json_dict = sv.to_json_dict()
        assert json_dict["value"] == 0.42
        assert json_dict["uncertainty"]["type"] == "delta"
        assert json_dict["provenance"]["algorithm"] == "degree"
    
    def test_statvalue_backward_compat(self):
        """Test backward compatibility with float()."""
        sv = StatValue(0.42, Delta(0.0), Provenance("a", "delta", {}))
        # Old code expecting float should still work
        x = float(sv)
        assert x == 0.42
        assert isinstance(x, float)


class TestPropagationReproducibility:
    """Tests for seed reproducibility in MC propagation."""
    
    def test_mc_propagation_seed(self):
        """Test that MC propagation is reproducible with seed."""
        b1 = Bootstrap(np.array([0.1, 0.2, 0.3, 0.15, 0.25]))
        b2 = Bootstrap(np.array([0.05, 0.1, 0.08, 0.12, 0.09]))
        
        # Propagate with same seed twice
        result1 = b1.propagate("+", b2, seed=42)
        result2 = b1.propagate("+", b2, seed=42)
        
        # Results should be identical
        assert np.allclose(result1.sample(10, seed=1), result2.sample(10, seed=1))
    
    def test_mc_propagation_different_seed(self):
        """Test that different seeds give different results."""
        b1 = Bootstrap(np.array([0.1, 0.2, 0.3]))
        b2 = Bootstrap(np.array([0.05, 0.1, 0.08]))
        
        result1 = b1.propagate("+", b2, seed=42)
        result2 = b1.propagate("+", b2, seed=123)
        
        # Results should be different (statistically)
        samples1 = result1.sample(100, seed=1)
        samples2 = result2.sample(100, seed=1)
        # Check that distributions are different
        assert not np.allclose(samples1, samples2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
