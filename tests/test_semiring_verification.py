"""Algebraic law verification tests for semirings.

These tests perform bounded verification of semiring laws using sample values.
They are NOT universal proofs but provide high confidence through systematic testing.
"""

import pytest
import math
from py3plex.semiring import get_semiring, list_semirings
from py3plex.semiring.core import SemiringValidationError


class TestSemiringAlgebraicLaws:
    """Test algebraic laws for built-in semirings."""
    
    def test_all_built_ins_validate(self):
        """Verify all built-in semirings pass validation."""
        for name in list_semirings():
            spec = get_semiring(name)
            # This should not raise
            spec.validate()
    
    def test_min_plus_associativity_plus(self):
        """Test associativity of ⊕ for min_plus."""
        spec = get_semiring("min_plus")
        samples = [0.0, 1.0, 2.0, 5.0, math.inf]
        
        for a in samples:
            for b in samples:
                for c in samples:
                    left = spec.plus(spec.plus(a, b), c)
                    right = spec.plus(a, spec.plus(b, c))
                    assert math.isclose(left, right, rel_tol=1e-9) or (math.isinf(left) and math.isinf(right))
    
    def test_min_plus_associativity_times(self):
        """Test associativity of ⊗ for min_plus."""
        spec = get_semiring("min_plus")
        samples = [0.0, 1.0, 2.0, 5.0]  # Avoid inf for times
        
        for a in samples:
            for b in samples:
                for c in samples:
                    left = spec.times(spec.times(a, b), c)
                    right = spec.times(a, spec.times(b, c))
                    assert math.isclose(left, right, rel_tol=1e-9)
    
    def test_min_plus_identity_plus(self):
        """Test identity for ⊕ in min_plus."""
        spec = get_semiring("min_plus")
        samples = [0.0, 1.0, 2.0, 5.0, math.inf]
        
        for a in samples:
            assert spec.plus(a, spec.zero) == a or (math.isinf(a) and math.isinf(spec.plus(a, spec.zero)))
            assert spec.plus(spec.zero, a) == a or (math.isinf(a) and math.isinf(spec.plus(spec.zero, a)))
    
    def test_min_plus_identity_times(self):
        """Test identity for ⊗ in min_plus."""
        spec = get_semiring("min_plus")
        samples = [0.0, 1.0, 2.0, 5.0, 10.0]
        
        for a in samples:
            left = spec.times(a, spec.one)
            right = spec.times(spec.one, a)
            assert math.isclose(left, a, rel_tol=1e-9)
            assert math.isclose(right, a, rel_tol=1e-9)
    
    def test_min_plus_distributivity(self):
        """Test distributivity for min_plus."""
        spec = get_semiring("min_plus")
        samples = [0.0, 1.0, 2.0, 5.0, 10.0]
        
        for a in samples:
            for b in samples:
                for c in samples:
                    # a ⊗ (b ⊕ c) = (a ⊗ b) ⊕ (a ⊗ c)
                    left = spec.times(a, spec.plus(b, c))
                    right = spec.plus(spec.times(a, b), spec.times(a, c))
                    assert math.isclose(left, right, rel_tol=1e-9)
    
    def test_min_plus_absorption(self):
        """Test absorption for min_plus."""
        spec = get_semiring("min_plus")
        samples = [0.0, 1.0, 2.0, 5.0, 10.0]
        
        for a in samples:
            left = spec.times(spec.zero, a)
            right = spec.times(a, spec.zero)
            assert math.isinf(left)
            assert math.isinf(right)
    
    def test_min_plus_commutativity_plus(self):
        """Test commutativity of ⊕ for min_plus (required by strict=True)."""
        spec = get_semiring("min_plus")
        samples = [0.0, 1.0, 2.0, 5.0, math.inf]
        
        for a in samples:
            for b in samples:
                assert spec.plus(a, b) == spec.plus(b, a)
    
    def test_boolean_all_laws(self):
        """Test all laws for boolean semiring."""
        spec = get_semiring("boolean")
        samples = [True, False]
        
        # Associativity plus
        for a in samples:
            for b in samples:
                for c in samples:
                    assert spec.plus(spec.plus(a, b), c) == spec.plus(a, spec.plus(b, c))
        
        # Associativity times
        for a in samples:
            for b in samples:
                for c in samples:
                    assert spec.times(spec.times(a, b), c) == spec.times(a, spec.times(b, c))
        
        # Identity
        for a in samples:
            assert spec.plus(a, spec.zero) == a
            assert spec.times(a, spec.one) == a
        
        # Absorption
        for a in samples:
            assert spec.times(spec.zero, a) == spec.zero
            assert spec.times(a, spec.zero) == spec.zero
        
        # Distributivity
        for a in samples:
            for b in samples:
                for c in samples:
                    left = spec.times(a, spec.plus(b, c))
                    right = spec.plus(spec.times(a, b), spec.times(a, c))
                    assert left == right
    
    def test_max_times_all_laws(self):
        """Test all laws for max_times semiring."""
        spec = get_semiring("max_times")
        samples = [0.0, 0.1, 0.5, 0.9, 1.0]
        
        # Associativity plus
        for a in samples:
            for b in samples:
                for c in samples:
                    assert math.isclose(
                        spec.plus(spec.plus(a, b), c),
                        spec.plus(a, spec.plus(b, c)),
                        rel_tol=1e-9
                    )
        
        # Identity times
        for a in samples:
            assert math.isclose(spec.times(a, spec.one), a, rel_tol=1e-9)
            assert math.isclose(spec.times(spec.one, a), a, rel_tol=1e-9)
        
        # Absorption
        for a in samples:
            assert math.isclose(spec.times(spec.zero, a), 0.0, abs_tol=1e-9)
            assert math.isclose(spec.times(a, spec.zero), 0.0, abs_tol=1e-9)


class TestSemiringValidation:
    """Test semiring validation catches broken specifications."""
    
    def test_invalid_plus_not_callable(self):
        """Test validation fails when plus is not callable."""
        from py3plex.semiring.core import SemiringSpec
        
        spec = SemiringSpec(
            name="broken",
            zero=0,
            one=1,
            plus="not_callable",  # Invalid
            times=lambda a, b: a + b,
        )
        
        with pytest.raises(SemiringValidationError, match="plus must be callable"):
            spec.validate()
    
    def test_invalid_absorption_caught(self):
        """Test validation catches absorption violations."""
        from py3plex.semiring.core import SemiringSpec
        
        # Create a broken semiring where 0 ⊗ a != 0
        def broken_times(a, b):
            if a == 0:
                return 1  # Wrong! Should return 0
            return a * b
        
        spec = SemiringSpec(
            name="broken_absorption",
            zero=0,
            one=1,
            plus=lambda a, b: max(a, b),
            times=broken_times,
            examples=(0, 1, 2),
        )
        
        with pytest.raises(SemiringValidationError, match="absorption"):
            spec.validate()
    
    def test_strict_mode_catches_non_commutative_plus(self):
        """Test strict mode catches non-commutative ⊕."""
        from py3plex.semiring.core import SemiringSpec
        
        # Non-commutative plus
        def non_commutative_plus(a, b):
            return a  # Always return first argument
        
        spec = SemiringSpec(
            name="non_commutative",
            zero=0,
            one=1,
            plus=non_commutative_plus,
            times=lambda a, b: a + b,
            strict=True,
            examples=(0, 1, 2),
        )
        
        with pytest.raises(SemiringValidationError, match="commutativity"):
            spec.validate()


@pytest.mark.property
class TestSemiringPropertiesHypothesis:
    """Property-based tests using Hypothesis (if available)."""
    
    @pytest.mark.skipif(
        not pytest.importorskip("hypothesis", minversion="6.0"),
        reason="Requires hypothesis"
    )
    def test_min_plus_laws_with_hypothesis(self):
        """Use Hypothesis to generate test cases for min_plus."""
        from hypothesis import given, strategies as st
        
        spec = get_semiring("min_plus")
        
        @given(
            a=st.floats(min_value=0.0, max_value=100.0),
            b=st.floats(min_value=0.0, max_value=100.0),
            c=st.floats(min_value=0.0, max_value=100.0),
        )
        def test_distributivity(a, b, c):
            left = spec.times(a, spec.plus(b, c))
            right = spec.plus(spec.times(a, b), spec.times(a, c))
            assert math.isclose(left, right, rel_tol=1e-9)
        
        test_distributivity()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
