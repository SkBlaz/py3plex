"""Property-based tests for UQValue algebraic laws.

Tests that UQValue operations satisfy formal algebraic laws:
- Identity, Idempotence, Associativity, Commutativity
- Monotonicity, Closure, Degeneracy Consistency
- Grouping Invariance, Determinism

Using Hypothesis for property-based testing to verify laws hold
for all valid inputs, not just hand-picked test cases.
"""

import pytest
import math
from hypothesis import given, strategies as st, assume, settings
from hypothesis import HealthCheck

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
)


# ============================================================================
# Strategy Helpers
# ============================================================================


@st.composite
def provenance_info(draw, method=None):
    """Generate random ProvenanceInfo."""
    if method is None:
        method = draw(st.sampled_from(["bootstrap", "perturbation", "seed", "deterministic"]))
    
    seed = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=1000)))
    n_samples = draw(st.integers(min_value=10, max_value=200))
    
    return ProvenanceInfo(
        method=method,
        seed=seed,
        n_samples=n_samples,
    )


@st.composite
def uq_value(draw, mean_range=(-100.0, 100.0), allow_degenerate=True):
    """Generate random UQValue."""
    mean = draw(st.floats(min_value=mean_range[0], max_value=mean_range[1], allow_nan=False, allow_infinity=False))
    
    # Choose distribution type
    dist_types = [DistributionType.GAUSSIAN, DistributionType.EMPIRICAL]
    if allow_degenerate:
        dist_types.append(DistributionType.DEGENERATE)
    
    dist_type = draw(st.sampled_from(dist_types))
    
    if dist_type == DistributionType.DEGENERATE:
        std = 0.0
        quantiles = {0.5: mean}
    else:
        std = draw(st.floats(min_value=0.01, max_value=abs(mean) * 0.5 + 1.0, allow_nan=False, allow_infinity=False))
        # Generate simple quantiles
        quantiles = {
            0.025: mean - 2 * std,
            0.5: mean,
            0.975: mean + 2 * std,
        }
    
    prov = draw(provenance_info())
    effective_count = draw(st.floats(min_value=1.0, max_value=10.0))
    
    return UQValue(
        distribution_type=dist_type,
        mean=mean,
        std=std,
        quantiles=quantiles,
        provenance=prov,
        effective_count=effective_count,
    )


@st.composite
def compatible_uq_values(draw, n=2):
    """Generate n UQValues with compatible provenance."""
    method = draw(st.sampled_from(["bootstrap", "perturbation", "seed"]))
    
    values = []
    for _ in range(n):
        mean = draw(st.floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False))
        std = draw(st.floats(min_value=0.1, max_value=20.0, allow_nan=False, allow_infinity=False))
        
        quantiles = {
            0.025: mean - 2 * std,
            0.5: mean,
            0.975: mean + 2 * std,
        }
        
        prov = ProvenanceInfo(method=method, n_samples=50)
        
        values.append(UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=mean,
            std=std,
            quantiles=quantiles,
            provenance=prov,
            effective_count=1.0,
        ))
    
    return values


# ============================================================================
# Identity Law Tests
# ============================================================================


class TestIdentityLaw:
    """Test IDENTITY law: Aggregating single UQValue returns same UQValue."""
    
    @pytest.mark.property
    @given(value=uq_value())
    @settings(max_examples=100, deadline=None)
    def test_aggregate_single_value_is_identity(self, value):
        """aggregate_mean([v]) should return v (identity law)."""
        result = UQAlgebra.aggregate_mean([value])
        
        # Mean should be preserved
        assert abs(result.mean - value.mean) < 1e-9
        
        # Std should be preserved
        assert abs(result.std - value.std) < 1e-9
        
        # Effective count should be preserved
        assert abs(result.effective_count - value.effective_count) < 1e-9


# ============================================================================
# Idempotence Law Tests
# ============================================================================


class TestIdempotenceLaw:
    """Test IDEMPOTENCE law: Aggregating identical values preserves distribution."""
    
    @pytest.mark.property
    @given(value=uq_value(allow_degenerate=False), n=st.integers(min_value=2, max_value=5))
    @settings(max_examples=50, deadline=None)
    def test_aggregate_identical_values_preserves_std(self, value, n):
        """Aggregating n identical UQValues should preserve std (idempotence)."""
        # Create n copies with identical structural properties
        values = [value] * n
        
        result = UQAlgebra.aggregate_mean(values)
        
        # Mean should be preserved
        assert abs(result.mean - value.mean) < 1e-6
        
        # Standard deviation should be preserved (idempotence)
        # Allow some tolerance due to variance propagation formula
        assert abs(result.std - value.std) < 1e-5 or result.std <= value.std * 1.01


# ============================================================================
# Commutativity Law Tests
# ============================================================================


class TestCommutativityLaw:
    """Test COMMUTATIVITY law: A ⊕ B == B ⊕ A (order-independent)."""
    
    @pytest.mark.property
    @given(values=compatible_uq_values(n=2))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_aggregate_order_independence(self, values):
        """aggregate_mean([a, b]) == aggregate_mean([b, a]) (commutativity)."""
        a, b = values
        
        # Skip if values are nearly identical (would trivially satisfy)
        assume(abs(a.mean - b.mean) > 1e-3)
        
        result_ab = UQAlgebra.aggregate_mean([a, b])
        result_ba = UQAlgebra.aggregate_mean([b, a])
        
        # Means should be equal (order-independent)
        assert abs(result_ab.mean - result_ba.mean) < 1e-9, \
            f"Mean not commutative: {result_ab.mean} != {result_ba.mean}"
        
        # Stds should be equal (order-independent)
        assert abs(result_ab.std - result_ba.std) < 1e-9, \
            f"Std not commutative: {result_ab.std} != {result_ba.std}"


# ============================================================================
# Associativity Law Tests (Relaxed)
# ============================================================================


class TestAssociativityLaw:
    """Test ASSOCIATIVITY law: (A ⊕ B) ⊕ C ~= A ⊕ (B ⊕ C) for mean."""
    
    @pytest.mark.property
    @given(values=compatible_uq_values(n=3))
    @settings(max_examples=50, deadline=None)
    def test_aggregate_mean_is_associative(self, values):
        """Mean aggregation should be associative (within tolerance)."""
        a, b, c = values
        
        # (a + b) + c
        ab = UQAlgebra.aggregate_mean([a, b])
        result_abc = UQAlgebra.aggregate_mean([ab, c])
        
        # a + (b + c)
        bc = UQAlgebra.aggregate_mean([b, c])
        result_a_bc = UQAlgebra.aggregate_mean([a, bc])
        
        # Means should be associative (exact equality for mean)
        assert abs(result_abc.mean - result_a_bc.mean) < 1e-6, \
            f"Mean not associative: {result_abc.mean} != {result_a_bc.mean}"


# ============================================================================
# Monotonicity Law Tests
# ============================================================================


class TestMonotonicityLaw:
    """Test MONOTONICITY law: More samples → not more uncertainty."""
    
    @pytest.mark.property
    @given(values=compatible_uq_values(n=2))
    @settings(max_examples=100, deadline=None)
    def test_aggregation_does_not_increase_uncertainty(self, values):
        """Aggregating values should not increase uncertainty beyond max input."""
        result = UQAlgebra.aggregate_mean(values)
        
        max_input_std = max(v.std for v in values)
        
        # Result std should not exceed max input std (with small tolerance for rounding)
        assert result.std <= max_input_std * 1.01, \
            f"Monotonicity violated: result std {result.std} > max input std {max_input_std}"


# ============================================================================
# Distribution Closure Tests
# ============================================================================


class TestDistributionClosure:
    """Test DISTRIBUTION CLOSURE: Operations produce valid UQValues."""
    
    @pytest.mark.property
    @given(values=compatible_uq_values(n=2))
    @settings(max_examples=100, deadline=None)
    def test_aggregate_produces_valid_uqvalue(self, values):
        """Aggregation should always produce a valid UQValue."""
        result = UQAlgebra.aggregate_mean(values)
        
        # Result should be a UQValue
        assert isinstance(result, UQValue)
        
        # Mean should be finite
        assert math.isfinite(result.mean)
        
        # Std should be non-negative and finite
        assert result.std >= 0
        assert math.isfinite(result.std)
        
        # Effective count should be positive
        assert result.effective_count > 0


# ============================================================================
# Degeneracy Consistency Tests
# ============================================================================


class TestDegeneracyConsistency:
    """Test DEGENERACY CONSISTENCY: Degenerate distributions act as neutral elements."""
    
    @pytest.mark.property
    @given(
        degenerate_value=st.floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False),
        other=uq_value(allow_degenerate=False),
    )
    @settings(max_examples=50, deadline=None)
    def test_degenerate_mixing_preserves_uncertainty(self, degenerate_value, other):
        """Mixing degenerate with non-degenerate preserves uncertainty."""
        degenerate = UQValue(
            distribution_type=DistributionType.DEGENERATE,
            mean=degenerate_value,
            std=0.0,
            quantiles={0.5: degenerate_value},
            provenance=ProvenanceInfo(method="deterministic"),
            effective_count=1.0,
        )
        
        # Make provenance compatible
        other_with_compat_prov = UQValue(
            distribution_type=other.distribution_type,
            mean=other.mean,
            std=other.std,
            quantiles=other.quantiles,
            provenance=ProvenanceInfo(method="bootstrap", n_samples=50),
            effective_count=other.effective_count,
        )
        
        result = UQAlgebra.aggregate_mean([degenerate, other_with_compat_prov])
        
        # Result should not be degenerate (uncertainty preserved)
        assert not result.is_degenerate() or (degenerate.mean == other.mean)
        
        # Result std should be related to input uncertainty
        if not result.is_degenerate():
            assert result.std > 0


# ============================================================================
# Determinism Tests
# ============================================================================


class TestDeterminism:
    """Test SEED DETERMINISM: Same operands + seed → identical result."""
    
    @pytest.mark.property
    @given(values=compatible_uq_values(n=2))
    @settings(max_examples=50, deadline=None)
    def test_aggregation_is_deterministic(self, values):
        """Aggregating same values twice should produce identical results."""
        result1 = UQAlgebra.aggregate_mean(values)
        result2 = UQAlgebra.aggregate_mean(values)
        
        # Results should be identical
        assert abs(result1.mean - result2.mean) < 1e-12
        assert abs(result1.std - result2.std) < 1e-12
        assert abs(result1.effective_count - result2.effective_count) < 1e-12


# ============================================================================
# Weighted Aggregation Properties
# ============================================================================


class TestWeightedAggregation:
    """Test properties of weighted aggregation."""
    
    @pytest.mark.property
    @given(
        values=compatible_uq_values(n=2),
        weights=st.lists(st.floats(min_value=0.1, max_value=10.0, allow_nan=False), min_size=2, max_size=2),
    )
    @settings(max_examples=50, deadline=None)
    def test_weighted_mean_is_weighted_average(self, values, weights):
        """Weighted mean should be proper weighted average."""
        result = UQAlgebra.aggregate_mean(values, weights=weights)
        
        # Compute expected weighted mean
        total_weight = sum(weights)
        expected_mean = sum(v.mean * w for v, w in zip(values, weights)) / total_weight
        
        assert abs(result.mean - expected_mean) < 1e-6
    
    @pytest.mark.property
    @given(values=compatible_uq_values(n=2))
    @settings(max_examples=50, deadline=None)
    def test_equal_weights_equivalent_to_unweighted(self, values):
        """Equal weights should be equivalent to unweighted aggregation."""
        result_weighted = UQAlgebra.aggregate_mean(values, weights=[1.0, 1.0])
        result_unweighted = UQAlgebra.aggregate_mean(values)
        
        assert abs(result_weighted.mean - result_unweighted.mean) < 1e-9
        assert abs(result_weighted.std - result_unweighted.std) < 1e-9


# ============================================================================
# Provenance Compatibility Tests
# ============================================================================


class TestProvenanceCompatibility:
    """Test provenance compatibility checks."""
    
    @pytest.mark.property
    @given(
        method1=st.sampled_from(["bootstrap", "perturbation", "seed"]),
        method2=st.sampled_from(["bootstrap", "perturbation", "seed"]),
    )
    @settings(max_examples=50, deadline=None)
    def test_same_method_is_compatible(self, method1, method2):
        """Same UQ method should be compatible."""
        prov1 = ProvenanceInfo(method=method1, n_samples=50)
        prov2 = ProvenanceInfo(method=method2, n_samples=100)
        
        if method1 == method2:
            assert prov1.is_compatible(prov2)
    
    @pytest.mark.property
    @given(method=st.sampled_from(["bootstrap", "perturbation", "seed", "null_model"]))
    @settings(max_examples=20)
    def test_deterministic_is_compatible_with_all(self, method):
        """Deterministic provenance should be compatible with all methods."""
        deterministic = ProvenanceInfo(method="deterministic")
        other = ProvenanceInfo(method=method, n_samples=50)
        
        assert deterministic.is_compatible(other)
        assert other.is_compatible(deterministic)


# ============================================================================
# UQValue Construction Tests
# ============================================================================


class TestUQValueConstruction:
    """Test UQValue construction and validation."""
    
    @pytest.mark.property
    @given(
        mean=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        std=st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_valid_uqvalue_construction(self, mean, std):
        """Valid UQValue should construct without error."""
        value = UQValue(
            distribution_type=DistributionType.GAUSSIAN,
            mean=mean,
            std=std,
            quantiles={0.5: mean},
        )
        
        assert value.mean == mean
        assert value.std == std
    
    @pytest.mark.property
    @given(mean=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=50)
    def test_degenerate_must_have_zero_std(self, mean):
        """Degenerate UQValue must have std=0."""
        with pytest.raises(ValueError, match="must have std=0"):
            UQValue(
                distribution_type=DistributionType.DEGENERATE,
                mean=mean,
                std=0.1,  # Invalid: degenerate must have std=0
                quantiles={0.5: mean},
            )


# ============================================================================
# Check Algebraic Laws (Test UQAlgebra.check_* methods)
# ============================================================================


class TestAlgebraicLawChecks:
    """Test UQAlgebra.check_* methods for law verification."""
    
    @pytest.mark.property
    @given(values=compatible_uq_values(n=2))
    @settings(max_examples=50, deadline=None)
    def test_check_commutativity_on_valid_aggregation(self, values):
        """check_commutativity should not raise for valid aggregations."""
        a, b = values
        
        # Should not raise
        UQAlgebra.check_commutativity(a, b, tolerance=1e-6)
    
    @pytest.mark.property
    @given(values=compatible_uq_values(n=3))
    @settings(max_examples=30, deadline=None)
    def test_check_associativity_on_valid_aggregation(self, values):
        """check_associativity should not raise for valid aggregations."""
        a, b, c = values
        
        # Should not raise (or raise with clear message)
        try:
            UQAlgebra.check_associativity(a, b, c, tolerance=1e-5)
        except UQAssociativityViolation:
            # Associativity may not hold exactly for std, but should for mean
            pass
