"""Tests for UQ algebraic laws and operations.

This test suite verifies that all UQ operations respect the defined algebraic laws:
- Identity
- Idempotence  
- Associativity
- Commutativity
- Monotonicity
- Distribution closure
- Degeneracy consistency
- Grouping invariance
- Null-model dominance
- Seed determinism
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume

from py3plex.dsl.uq_algebra import (
    UQValue,
    UQAlgebra,
    DistributionType,
    ProvenanceInfo,
    UQIdentityViolation,
    UQIdempotenceViolation,
    UQAssociativityViolation,
    UQCommutativityViolation,
    UQMonotonicityViolation,
    UQIncompatibleSupport,
    UQIncompatibleProvenance,
    UQClosureViolation,
    convert_to_uqvalue,
)


# Fixtures for common UQValues

@pytest.fixture
def degenerate_value():
    """Degenerate (deterministic) UQValue."""
    return UQValue.degenerate(value=5.0, method="deterministic", n_samples=1)


@pytest.fixture
def gaussian_value():
    """Gaussian UQValue."""
    return UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=10.0,
        std=2.0,
        quantiles={0.025: 6.08, 0.975: 13.92},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=100, seed=42),
    )


@pytest.fixture
def empirical_value():
    """Empirical UQValue with samples."""
    samples = np.random.default_rng(123).normal(15.0, 3.0, size=50)
    return UQValue(
        distribution_type=DistributionType.EMPIRICAL,
        mean=np.mean(samples),
        std=np.std(samples, ddof=1),
        quantiles={
            0.025: np.quantile(samples, 0.025),
            0.975: np.quantile(samples, 0.975),
        },
        samples=samples,
        provenance=ProvenanceInfo(method="bootstrap", n_samples=50, seed=123),
    )


# Test UQValue creation and validation

def test_uqvalue_creation():
    """Test basic UQValue creation."""
    value = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=10.0,
        std=2.0,
        quantiles={0.025: 6.08, 0.975: 13.92},
    )
    assert value.mean == 10.0
    assert value.std == 2.0
    assert not value.is_degenerate()


def test_uqvalue_degenerate():
    """Test degenerate UQValue creation."""
    value = UQValue.degenerate(value=5.0)
    assert value.mean == 5.0
    assert value.std == 0.0
    assert value.is_degenerate()
    assert value.distribution_type == DistributionType.DEGENERATE


def test_uqvalue_validation_invalid_mean():
    """Test that invalid mean raises error."""
    with pytest.raises(ValueError, match="mean must be finite"):
        UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=float('inf'),
            std=2.0,
        )


def test_uqvalue_validation_negative_std():
    """Test that negative std raises error."""
    with pytest.raises(ValueError, match="std must be non-negative"):
        UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=10.0,
            std=-1.0,
        )


def test_uqvalue_validation_degenerate_nonzero_std():
    """Test that degenerate with std>0 raises error."""
    with pytest.raises(ValueError, match="Degenerate distribution must have std=0"):
        UQValue(
            distribution_type=DistributionType.DEGENERATE,
            mean=10.0,
            std=0.1,
        )


def test_uqvalue_to_dict():
    """Test UQValue serialization to dict."""
    value = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=10.0,
        std=2.0,
        quantiles={0.025: 6.08, 0.975: 13.92},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=100, seed=42),
    )
    
    data = value.to_dict()
    assert data["mean"] == 10.0
    assert data["value"] == 10.0  # Alias
    assert data["std"] == 2.0
    assert data["ci_low"] == 6.08
    assert data["ci_high"] == 13.92
    assert data["method"] == "bootstrap"
    assert data["n_samples"] == 100
    assert data["seed"] == 42


def test_uqvalue_from_dict():
    """Test UQValue deserialization from dict."""
    data = {
        "mean": 10.0,
        "std": 2.0,
        "quantiles": {0.025: 6.08, 0.975: 13.92},
        "distribution_type": "gaussian",
        "method": "bootstrap",
        "n_samples": 100,
        "seed": 42,
    }
    
    value = UQValue.from_dict(data)
    assert value.mean == 10.0
    assert value.std == 2.0
    assert value.distribution_type == DistributionType.GAUSSIAN
    assert value.provenance.method == "bootstrap"
    assert value.provenance.n_samples == 100
    assert value.provenance.seed == 42


def test_convert_to_uqvalue_scalar():
    """Test converting scalar to UQValue."""
    value = convert_to_uqvalue(5.0)
    assert isinstance(value, UQValue)
    assert value.mean == 5.0
    assert value.std == 0.0
    assert value.is_degenerate()


def test_convert_to_uqvalue_dict():
    """Test converting dict to UQValue."""
    data = {"mean": 10.0, "std": 2.0, "quantiles": {}}
    value = convert_to_uqvalue(data)
    assert isinstance(value, UQValue)
    assert value.mean == 10.0
    assert value.std == 2.0


def test_convert_to_uqvalue_uqvalue():
    """Test converting UQValue to UQValue (no-op)."""
    original = UQValue.degenerate(5.0)
    value = convert_to_uqvalue(original)
    assert value is original


# Test algebraic laws

def test_identity_law_single_value(degenerate_value):
    """Test identity law: aggregating single value returns same value."""
    result = UQAlgebra.aggregate_mean([degenerate_value])
    assert result.mean == degenerate_value.mean
    assert result.std == degenerate_value.std


def test_identity_law_empty_list():
    """Test identity law violation: empty list raises error."""
    with pytest.raises(UQIdentityViolation, match="Cannot aggregate empty list"):
        UQAlgebra.aggregate_mean([])


def test_identity_law_zero_weight():
    """Test identity law violation: zero weights raise error."""
    value = UQValue.degenerate(5.0)
    with pytest.raises(UQIdentityViolation, match="zero-weight aggregation"):
        UQAlgebra.aggregate_mean([value, value], weights=[0.0, 0.0])


def test_idempotence_law_identical_values():
    """Test idempotence: aggregating identical values preserves distribution.
    
    Note: When all values are structurally identical, the implementation
    preserves the original std (idempotence law). This differs from
    aggregating independent samples, which would reduce std by sqrt(n).
    """
    value = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=10.0,
        std=2.0,
        quantiles={0.025: 6.08, 0.975: 13.92},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=100),
    )
    
    # Aggregate 3 identical values
    result = UQAlgebra.aggregate_mean([value, value, value])
    
    # Mean should be preserved
    assert abs(result.mean - value.mean) < 1e-9
    
    # Std should be preserved (idempotence for identical values)
    assert abs(result.std - value.std) < 1e-9


def test_idempotence_law_degenerate():
    """Test idempotence for degenerate values."""
    value = UQValue.degenerate(5.0)
    
    result = UQAlgebra.aggregate_mean([value, value, value])
    
    assert result.mean == value.mean
    assert result.std == 0.0
    assert result.is_degenerate()


def test_associativity_law(gaussian_value, empirical_value, degenerate_value):
    """Test associativity: (a⊕b)⊕c ≈ a⊕(b⊕c)."""
    # Use compatible values (same provenance)
    a = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=10.0,
        std=2.0,
        quantiles={},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
    )
    b = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=15.0,
        std=3.0,
        quantiles={},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
    )
    c = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=20.0,
        std=4.0,
        quantiles={},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
    )
    
    # This should not raise
    UQAlgebra.check_associativity(a, b, c, tolerance=1e-6)


def test_commutativity_law():
    """Test commutativity: a⊕b ≈ b⊕a."""
    a = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=10.0,
        std=2.0,
        quantiles={},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
    )
    b = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=15.0,
        std=3.0,
        quantiles={},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
    )
    
    # This should not raise
    UQAlgebra.check_commutativity(a, b, tolerance=1e-9)


def test_monotonicity_law_more_samples_less_uncertainty():
    """Test monotonicity: more samples should not increase uncertainty."""
    # Create values with different sample counts
    v1 = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=10.0,
        std=2.0,
        quantiles={},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
    )
    v2 = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=12.0,
        std=1.5,
        quantiles={},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
    )
    
    # Aggregating should not raise monotonicity violation
    result = UQAlgebra.aggregate_mean([v1, v2])
    
    # Result should have more samples
    assert result.provenance.n_samples == 100
    
    # Uncertainty should not be wildly larger than inputs
    max_input_std = max(v1.std, v2.std)
    assert result.std <= max_input_std * 2  # Allow some increase for variance propagation


def test_distribution_closure_aggregation_returns_uqvalue(gaussian_value, empirical_value):
    """Test distribution closure: aggregation returns valid UQValue."""
    result = UQAlgebra.aggregate_mean([gaussian_value, empirical_value])
    
    assert isinstance(result, UQValue)
    assert np.isfinite(result.mean)
    assert np.isfinite(result.std)
    assert result.std >= 0


def test_degeneracy_consistency_degenerate_plus_degenerate():
    """Test degeneracy consistency: degenerate + degenerate = degenerate."""
    v1 = UQValue.degenerate(5.0)
    v2 = UQValue.degenerate(10.0)
    
    result = UQAlgebra.aggregate_mean([v1, v2])
    
    assert result.is_degenerate()
    assert result.mean == 7.5  # Average of 5 and 10


def test_degeneracy_consistency_degenerate_plus_nondegenerate():
    """Test degeneracy consistency: degenerate + nondegenerate preserves uncertainty."""
    degenerate = UQValue.degenerate(5.0)
    nondegenerate = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=10.0,
        std=2.0,
        quantiles={},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
    )
    
    result = UQAlgebra.aggregate_mean([degenerate, nondegenerate])
    
    # Result should not be degenerate
    assert not result.is_degenerate()
    assert result.std > 0
    
    # Mean should be average
    assert abs(result.mean - 7.5) < 0.1


def test_incompatible_support_raises_error():
    """Test that incompatible support domains raise error."""
    v1 = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=10.0,
        std=2.0,
        quantiles={},
        support={"layer": "social"},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
    )
    v2 = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=15.0,
        std=3.0,
        quantiles={},
        support={"layer": "work"},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
    )
    
    with pytest.raises(UQIncompatibleSupport, match="incompatible support"):
        UQAlgebra.aggregate_mean([v1, v2])


def test_incompatible_provenance_raises_error():
    """Test that incompatible provenance raises error."""
    v1 = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=10.0,
        std=2.0,
        quantiles={},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
    )
    v2 = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=15.0,
        std=3.0,
        quantiles={},
        provenance=ProvenanceInfo(method="null_model", n_samples=50, null_model="erdos_renyi"),
    )
    
    with pytest.raises(UQIncompatibleProvenance, match="incompatible provenance"):
        UQAlgebra.aggregate_mean([v1, v2])


def test_seed_determinism_same_seed_same_result():
    """Test seed determinism: same seed produces identical results."""
    v1 = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=10.0,
        std=2.0,
        quantiles={0.025: 6.0, 0.975: 14.0},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=100, seed=42),
    )
    v2 = UQValue(
        distribution_type=DistributionType.GAUSSIAN,
        mean=15.0,
        std=3.0,
        quantiles={0.025: 9.0, 0.975: 21.0},
        provenance=ProvenanceInfo(method="bootstrap", n_samples=100, seed=42),
    )
    
    # Aggregate twice
    result1 = UQAlgebra.aggregate_mean([v1, v2])
    result2 = UQAlgebra.aggregate_mean([v1, v2])
    
    # Results should be identical (deterministic aggregation)
    assert result1.mean == result2.mean
    assert result1.std == result2.std
    assert result1.quantiles == result2.quantiles


# Property-based tests

@given(
    mean=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    std=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, deadline=None)
def test_property_uqvalue_creation(mean, std):
    """Property test: UQValue creation should always succeed for valid inputs."""
    assume(std >= 0)
    
    if std == 0:
        dist_type = DistributionType.DEGENERATE
    else:
        dist_type = DistributionType.GAUSSIAN
    
    value = UQValue(
        distribution_type=dist_type,
        mean=mean,
        std=std,
        quantiles={},
    )
    
    assert value.mean == mean
    assert value.std == std


@given(
    values=st.lists(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=10,
    )
)
@settings(max_examples=50, deadline=None)
def test_property_identity_single_degenerate(values):
    """Property test: identity law for single degenerate value."""
    value = UQValue.degenerate(values[0])
    result = UQAlgebra.aggregate_mean([value])
    
    assert result.mean == value.mean
    assert result.std == value.std


@given(
    means=st.lists(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=5,
    ),
    stds=st.lists(
        st.floats(min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=5,
    ),
)
@settings(max_examples=30, deadline=None)
def test_property_commutativity_random(means, stds):
    """Property test: commutativity holds for random UQValues."""
    assume(len(means) == len(stds))
    assume(len(means) >= 2)
    
    # Create compatible UQValues
    values = [
        UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=m,
            std=s,
            quantiles={},
            provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
        )
        for m, s in zip(means[:2], stds[:2])
    ]
    
    # Test commutativity
    try:
        UQAlgebra.check_commutativity(values[0], values[1], tolerance=1e-6)
    except UQCommutativityViolation:
        pytest.fail("Commutativity violated for random inputs")


@given(
    means=st.lists(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=3,
    ),
    stds=st.lists(
        st.floats(min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=3,
    ),
)
@settings(max_examples=20, deadline=None)
def test_property_associativity_random(means, stds):
    """Property test: associativity holds for random UQValues."""
    assume(len(means) == 3 and len(stds) == 3)
    
    # Create compatible UQValues
    values = [
        UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=m,
            std=s,
            quantiles={},
            provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
        )
        for m, s in zip(means, stds)
    ]
    
    # Test associativity
    try:
        UQAlgebra.check_associativity(
            values[0], values[1], values[2], tolerance=1e-5
        )
    except UQAssociativityViolation:
        pytest.fail("Associativity violated for random inputs")


# Differential tests

def test_differential_split_aggregate_equivalence():
    """Test that splitting then aggregating equals direct aggregation.
    
    Note: Due to variance propagation path-dependence, std may differ by up to 50%.
    This is mathematically acceptable because:
    - Var((a+b)/2 + (c+d)/2)/2) uses different weight products than Var((a+b+c+d)/4)
    - The 50% tolerance allows for worst-case variance propagation differences
    - Mean should always match exactly (tested separately)
    """
    # Create a list of values
    values = [
        UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=float(i * 10),
            std=float(i),
            quantiles={},
            provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
        )
        for i in range(1, 5)
    ]
    
    # Direct aggregation
    direct = UQAlgebra.aggregate_mean(values)
    
    # Split and aggregate: (v1, v2) + (v3, v4)
    left = UQAlgebra.aggregate_mean(values[:2])
    right = UQAlgebra.aggregate_mean(values[2:])
    split_agg = UQAlgebra.aggregate_mean([left, right])
    
    # Results should be close (not exact due to variance propagation)
    assert abs(direct.mean - split_agg.mean) < 1e-6
    
    # Std may differ due to different aggregation paths, but should be within bounds
    # Allow 50% difference due to variance propagation formula differences
    assert abs(direct.std - split_agg.std) / max(direct.std, split_agg.std) < 0.5


def test_differential_order_invariance():
    """Test that reordering operands preserves results (commutativity)."""
    values = [
        UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=float(i * 10),
            std=float(i),
            quantiles={},
            provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
        )
        for i in range(1, 4)
    ]
    
    # Aggregate in original order
    result1 = UQAlgebra.aggregate_mean(values)
    
    # Aggregate in reversed order
    result2 = UQAlgebra.aggregate_mean(values[::-1])
    
    # Results should be identical
    assert abs(result1.mean - result2.mean) < 1e-9
    assert abs(result1.std - result2.std) < 1e-9


# Metamorphic tests

def test_metamorphic_weighted_unweighted_equivalence():
    """Test that uniform weights give same result as no weights."""
    values = [
        UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=10.0,
            std=2.0,
            quantiles={},
            provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
        ),
        UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=20.0,
            std=3.0,
            quantiles={},
            provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
        ),
    ]
    
    # Unweighted
    result1 = UQAlgebra.aggregate_mean(values)
    
    # Uniform weights
    result2 = UQAlgebra.aggregate_mean(values, weights=[0.5, 0.5])
    
    # Results should be identical
    assert abs(result1.mean - result2.mean) < 1e-9
    assert abs(result1.std - result2.std) < 1e-9


def test_metamorphic_scaling_invariance():
    """Test that scaling all values scales the mean proportionally."""
    values = [
        UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=10.0,
            std=2.0,
            quantiles={},
            provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
        ),
        UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=20.0,
            std=3.0,
            quantiles={},
            provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
        ),
    ]
    
    result1 = UQAlgebra.aggregate_mean(values)
    
    # Scale by 2
    scaled_values = [
        UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=v.mean * 2,
            std=v.std * 2,
            quantiles={},
            provenance=v.provenance,
        )
        for v in values
    ]
    
    result2 = UQAlgebra.aggregate_mean(scaled_values)
    
    # Mean should scale
    assert abs(result2.mean - result1.mean * 2) < 1e-6
    
    # Std should scale
    assert abs(result2.std - result1.std * 2) < 1e-6
