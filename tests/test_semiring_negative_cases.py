"""Negative test cases for semiring validation and execution safety."""

import pytest
import math
from py3plex.semiring.core import (
    SemiringSpec,
    SemiringValidationError,
    SemiringExecutionError,
)
from py3plex.semiring import register_semiring, get_semiring
from py3plex.semiring.engine import semiring_paths, semiring_closure


class TestSemiringValidationErrors:
    """Test that validation catches invalid semiring specs."""
    
    def test_empty_name_rejected(self):
        """Test that empty semiring name is rejected."""
        spec = SemiringSpec(
            name="",
            zero=0,
            one=1,
            plus=lambda a, b: a + b,
            times=lambda a, b: a * b,
        )
        
        with pytest.raises(SemiringValidationError, match="name must be non-empty"):
            spec.validate()
    
    def test_none_zero_rejected(self):
        """Test that None zero is rejected."""
        spec = SemiringSpec(
            name="broken",
            zero=None,
            one=1,
            plus=lambda a, b: a + b,
            times=lambda a, b: a * b,
        )
        
        with pytest.raises(SemiringValidationError, match="zero must be provided"):
            spec.validate()
    
    def test_none_one_rejected(self):
        """Test that None one is rejected."""
        spec = SemiringSpec(
            name="broken",
            zero=0,
            one=None,
            plus=lambda a, b: a + b,
            times=lambda a, b: a * b,
        )
        
        with pytest.raises(SemiringValidationError, match="one must be provided"):
            spec.validate()
    
    def test_non_callable_plus_rejected(self):
        """Test that non-callable plus is rejected."""
        spec = SemiringSpec(
            name="broken",
            zero=0,
            one=1,
            plus=42,  # Not callable
            times=lambda a, b: a * b,
        )
        
        with pytest.raises(SemiringValidationError, match="plus must be callable"):
            spec.validate()
    
    def test_non_callable_times_rejected(self):
        """Test that non-callable times is rejected."""
        spec = SemiringSpec(
            name="broken",
            zero=0,
            one=1,
            plus=lambda a, b: a + b,
            times="not_callable",  # Not callable
        )
        
        with pytest.raises(SemiringValidationError, match="times must be callable"):
            spec.validate()
    
    def test_broken_associativity_plus_caught(self):
        """Test that broken associativity of ⊕ is caught."""
        def broken_plus(a, b):
            # Intentionally non-associative
            if a == 0:
                return b + 1
            return a + b
        
        spec = SemiringSpec(
            name="broken_assoc",
            zero=0,
            one=1,
            plus=broken_plus,
            times=lambda a, b: a * b,
            examples=(0, 1, 2),
        )
        
        with pytest.raises(SemiringValidationError, match="associativity"):
            spec.validate()
    
    def test_broken_identity_caught(self):
        """Test that broken identity is caught."""
        def broken_plus(a, b):
            return a + b + 1  # 0 is NOT identity
        
        spec = SemiringSpec(
            name="broken_id",
            zero=0,
            one=1,
            plus=broken_plus,
            times=lambda a, b: a * b,
            examples=(0, 1, 2),
        )
        
        with pytest.raises(SemiringValidationError, match="identity"):
            spec.validate()
    
    def test_duplicate_registration_rejected(self):
        """Test that duplicate registration without overwrite fails."""
        spec = SemiringSpec(
            name="test_duplicate",
            zero=0,
            one=1,
            plus=lambda a, b: max(a, b),
            times=lambda a, b: a + b,
        )
        
        # First registration should succeed
        register_semiring(spec, overwrite=True)
        
        # Second registration without overwrite should fail
        with pytest.raises(SemiringValidationError, match="already registered"):
            register_semiring(spec, overwrite=False)


class TestSemiringExecutionErrors:
    """Test that execution errors are caught properly."""
    
    def test_non_idempotent_without_max_hops_requires_warning(self):
        """Test that non-idempotent semiring without max_hops issues warning."""
        import warnings
        from py3plex.core import multinet
        
        # Create a simple network
        net = multinet.multi_layer_network()
        net.add_nodes([{'source': 'A', 'type': 'layer1'}, {'source': 'B', 'type': 'layer1'}])
        net.add_edges([{'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}])
        
        # Create non-idempotent semiring
        spec = SemiringSpec(
            name="non_idempotent_test",
            zero=math.inf,
            one=0.0,
            plus=lambda a, b: a + b,  # NOT idempotent (addition)
            times=lambda a, b: a + b,
            is_idempotent_plus=False,
            leq=lambda a, b: a <= b,
        )
        
        # Should issue a warning but use default max_hops
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = semiring_paths(net, spec, source='A', max_hops=None)
            
            # Check that warning was issued
            assert len(w) >= 1
            assert "max_hops" in str(w[0].message).lower()
    
    def test_non_idempotent_without_leq_requires_max_hops(self):
        """Test that non-idempotent semiring without leq requires explicit max_hops."""
        from py3plex.core import multinet
        
        net = multinet.multi_layer_network()
        net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        
        # Create non-idempotent semiring without leq
        spec = SemiringSpec(
            name="non_idempotent_no_leq",
            zero=0,
            one=1,
            plus=lambda a, b: a + b,
            times=lambda a, b: a * b,
            is_idempotent_plus=False,
            leq=None,  # No ordering!
        )
        
        # Should raise error
        with pytest.raises(SemiringExecutionError, match="max_hops parameter is required"):
            semiring_paths(net, spec, source='A', max_hops=None)
    
    def test_closure_large_network_without_max_hops(self):
        """Test that closure on large network without max_hops raises error."""
        from py3plex.core import multinet
        
        # Create a network exceeding threshold
        net = multinet.multi_layer_network()
        for i in range(150):  # > default threshold of 100
            net.add_nodes([{'source': f'node_{i}', 'type': 'layer1'}])
        
        spec = get_semiring("boolean")
        
        # Should raise error
        with pytest.raises(SemiringExecutionError, match="max_hops parameter required"):
            semiring_closure(net, spec, max_hops=None, size_threshold=100)
    
    def test_unknown_semiring_name(self):
        """Test that unknown semiring name raises helpful error."""
        with pytest.raises(SemiringValidationError, match="Unknown semiring.*nonexistent"):
            get_semiring("nonexistent_semiring")
        
        # Error should list available semirings
        try:
            get_semiring("nonexistent")
        except SemiringValidationError as e:
            assert "Available semirings" in str(e)
            assert "min_plus" in str(e)  # Should list built-ins
    
    def test_invalid_network_object(self):
        """Test that invalid network object raises clear error."""
        spec = get_semiring("min_plus")
        
        # Pass invalid network (no get_nodes method)
        invalid_network = {"not": "a network"}
        
        with pytest.raises(SemiringExecutionError, match="get_nodes.*get_edges"):
            semiring_paths(invalid_network, spec, source='A')


class TestCounterexampleReporting:
    """Test that validation errors include useful counterexamples."""
    
    def test_counterexample_in_error(self):
        """Test that validation error includes counterexample details."""
        def broken_distributivity_times(a, b):
            # Intentionally break distributivity
            if a == 2 and b == 1:
                return 999  # Wrong result
            return a * b
        
        spec = SemiringSpec(
            name="broken_dist",
            zero=0,
            one=1,
            plus=lambda a, b: max(a, b),
            times=broken_distributivity_times,
            examples=(0, 1, 2),
        )
        
        try:
            spec.validate()
            pytest.fail("Should have raised SemiringValidationError")
        except SemiringValidationError as e:
            # Check counterexample is present
            assert e.counterexample is not None
            assert 'property' in e.counterexample
            # Should mention distributivity
            assert 'distributivity' in e.counterexample['property'].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
