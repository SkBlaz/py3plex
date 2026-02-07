#!/usr/bin/env python3
"""Property-based tests for the _parallel module.

This module tests properties of parallel execution utilities, seed spawning,
and deterministic parallel computation using hypothesis.

Key properties tested:
- Seed spawning is deterministic and produces unique seeds
- Parallel execution produces same results as serial execution
- Seed spawning with None produces None seeds
- parallel_map preserves order
- parallel_map handles empty inputs correctly
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import note
import numpy as np

# Import parallel module
try:
    from py3plex._parallel import spawn_seeds, parallel_map
    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False
    pytest.skip("Parallel module not available", allow_module_level=True)


# ============================================================================
# Helper Strategies
# ============================================================================

@st.composite
def positive_seed(draw):
    """Generate a positive seed value."""
    return draw(st.integers(min_value=0, max_value=2**31 - 1))


@st.composite
def small_positive_int(draw):
    """Generate a small positive integer for n_jobs or counts."""
    return draw(st.integers(min_value=1, max_value=10))


# ============================================================================
# Property Tests: Seed Spawning
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(base_seed=positive_seed(), n=st.integers(min_value=1, max_value=20))
def test_spawn_seeds_deterministic(base_seed, n):
    """Property: Spawning seeds with same base_seed gives same children."""
    # Spawn twice with same base seed
    seeds1 = spawn_seeds(base_seed, n)
    seeds2 = spawn_seeds(base_seed, n)
    
    # Should be identical
    assert len(seeds1) == n
    assert len(seeds2) == n
    assert seeds1 == seeds2, f"Seeds should be deterministic: {seeds1} != {seeds2}"


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(base_seed=positive_seed(), n=st.integers(min_value=2, max_value=20))
def test_spawn_seeds_unique(base_seed, n):
    """Property: Spawned seeds are all unique (no duplicates)."""
    seeds = spawn_seeds(base_seed, n)
    
    # All seeds should be different
    assert len(seeds) == n
    assert len(set(seeds)) == n, f"Seeds should be unique, got duplicates in {seeds}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=1, max_value=20))
def test_spawn_seeds_none_base(n):
    """Property: Spawning with None base seed returns all None."""
    seeds = spawn_seeds(None, n)
    
    assert len(seeds) == n
    assert all(s is None for s in seeds), f"Expected all None, got {seeds}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(base_seed1=positive_seed(), base_seed2=positive_seed())
def test_different_base_seeds_produce_different_children(base_seed1, base_seed2):
    """Property: Different base seeds produce different children."""
    assume(base_seed1 != base_seed2)
    
    seeds1 = spawn_seeds(base_seed1, 5)
    seeds2 = spawn_seeds(base_seed2, 5)
    
    # At least one child should be different
    assert seeds1 != seeds2, "Different base seeds should produce different children"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(base_seed=positive_seed(), n=st.integers(min_value=1, max_value=10))
def test_spawn_seeds_returns_integers(base_seed, n):
    """Property: Spawned seeds are integers (not None)."""
    seeds = spawn_seeds(base_seed, n)
    
    assert all(isinstance(s, int) for s in seeds), \
        f"All spawned seeds should be integers, got {seeds}"


# ============================================================================
# Property Tests: parallel_map
# ============================================================================

def identity(x):
    """Identity function for testing."""
    return x


def square(x):
    """Square function for testing."""
    return x * x


def add_one(x):
    """Add one function for testing."""
    return x + 1


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(items=st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=20))
def test_parallel_map_preserves_order(items):
    """Property: parallel_map preserves input order (serial and parallel)."""
    # Serial execution
    result_serial = parallel_map(identity, items, n_jobs=1)
    
    # Parallel execution (2 workers)
    result_parallel = parallel_map(identity, items, n_jobs=2)
    
    # Both should preserve order
    assert result_serial == items, "Serial execution should preserve order"
    assert result_parallel == items, "Parallel execution should preserve order"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(items=st.lists(st.integers(min_value=-50, max_value=50), min_size=1, max_size=15))
def test_parallel_map_serial_equals_parallel(items):
    """Property: Serial and parallel execution produce identical results."""
    # Compute with serial execution
    result_serial = parallel_map(square, items, n_jobs=1)
    
    # Compute with parallel execution (2 workers)
    result_parallel = parallel_map(square, items, n_jobs=2)
    
    # Results should be identical
    assert result_serial == result_parallel, \
        f"Serial and parallel should give same results:\nSerial: {result_serial}\nParallel: {result_parallel}"


@pytest.mark.property
def test_parallel_map_empty_input():
    """Property: parallel_map handles empty input gracefully."""
    result = parallel_map(square, [], n_jobs=1)
    assert result == [], "Empty input should give empty output"
    
    result_parallel = parallel_map(square, [], n_jobs=2)
    assert result_parallel == [], "Empty input should give empty output (parallel)"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(items=st.lists(st.integers(min_value=0, max_value=20), min_size=1, max_size=10))
def test_parallel_map_applies_function_correctly(items):
    """Property: parallel_map correctly applies function to all items."""
    result = parallel_map(add_one, items, n_jobs=1)
    
    expected = [x + 1 for x in items]
    assert result == expected, f"Function not applied correctly: {result} != {expected}"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(items=st.lists(st.integers(min_value=1, max_value=10), min_size=1, max_size=10))
def test_parallel_map_length_preserved(items):
    """Property: parallel_map output has same length as input."""
    result_serial = parallel_map(square, items, n_jobs=1)
    result_parallel = parallel_map(square, items, n_jobs=2)
    
    assert len(result_serial) == len(items), "Serial: output length != input length"
    assert len(result_parallel) == len(items), "Parallel: output length != input length"


# ============================================================================
# Property Tests: Deterministic Parallel Execution
# ============================================================================

def random_from_seed(seed):
    """Generate random value from seed (for determinism testing)."""
    if seed is None:
        return np.random.rand()
    rng = np.random.default_rng(seed)
    return float(rng.random())


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(base_seed=positive_seed(), n_tasks=st.integers(min_value=2, max_value=10))
def test_parallel_execution_with_seeds_is_deterministic(base_seed, n_tasks):
    """Property: Parallel execution with seeds is deterministic."""
    # Spawn child seeds
    seeds = spawn_seeds(base_seed, n_tasks)
    
    # Execute twice with same seeds
    result1 = parallel_map(random_from_seed, seeds, n_jobs=1)
    result2 = parallel_map(random_from_seed, seeds, n_jobs=1)
    
    # Results should be identical
    assert len(result1) == len(result2) == n_tasks
    for i, (r1, r2) in enumerate(zip(result1, result2)):
        assert abs(r1 - r2) < 1e-10, f"Results differ at index {i}: {r1} != {r2}"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(base_seed=positive_seed(), n_tasks=st.integers(min_value=2, max_value=8))
def test_parallel_execution_serial_vs_parallel_with_seeds(base_seed, n_tasks):
    """Property: Serial and parallel execution with seeds give same results."""
    seeds = spawn_seeds(base_seed, n_tasks)
    
    # Serial execution
    result_serial = parallel_map(random_from_seed, seeds, n_jobs=1)
    
    # Parallel execution
    result_parallel = parallel_map(random_from_seed, seeds, n_jobs=2)
    
    # Results should match (deterministic with seeds)
    assert len(result_serial) == len(result_parallel) == n_tasks
    for i, (r_s, r_p) in enumerate(zip(result_serial, result_parallel)):
        assert abs(r_s - r_p) < 1e-10, \
            f"Serial and parallel differ at index {i}: {r_s} != {r_p}"


# ============================================================================
# Property Tests: n_jobs Parameter
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    items=st.lists(st.integers(min_value=1, max_value=100), min_size=5, max_size=15),
    n_jobs=st.integers(min_value=1, max_value=4)
)
def test_parallel_map_different_njobs_same_result(items, n_jobs):
    """Property: Different n_jobs values produce same results."""
    result1 = parallel_map(square, items, n_jobs=1)
    result2 = parallel_map(square, items, n_jobs=n_jobs)
    
    assert result1 == result2, f"Different n_jobs should give same results"


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(items=st.lists(st.integers(), min_size=1, max_size=10))
def test_parallel_map_njobs_minus_one_works(items):
    """Property: n_jobs=-1 (use all CPUs) works correctly."""
    result = parallel_map(identity, items, n_jobs=-1)
    assert result == items, "n_jobs=-1 should work correctly"


# ============================================================================
# Property Tests: Spawn Behavior
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    base_seed=positive_seed(),
    n1=st.integers(min_value=1, max_value=10),
    n2=st.integers(min_value=1, max_value=10)
)
def test_spawn_seeds_different_n_gives_different_first_seeds(base_seed, n1, n2):
    """Property: Spawning different counts may give different first seeds."""
    assume(n1 != n2)
    
    seeds1 = spawn_seeds(base_seed, n1)
    seeds2 = spawn_seeds(base_seed, n2)
    
    # Both should be valid and deterministic
    assert len(seeds1) == n1
    assert len(seeds2) == n2
    
    # First seeds might differ (depends on SeedSequence implementation)
    # We just verify they're both deterministic
    seeds1_again = spawn_seeds(base_seed, n1)
    assert seeds1 == seeds1_again


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(base_seed=positive_seed())
def test_spawn_single_seed(base_seed):
    """Property: Spawning a single seed works correctly."""
    seeds = spawn_seeds(base_seed, 1)
    
    assert len(seeds) == 1
    assert isinstance(seeds[0], int)
    
    # Should be deterministic
    seeds_again = spawn_seeds(base_seed, 1)
    assert seeds == seeds_again


# ============================================================================
# Property Tests: Edge Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(item=st.integers())
def test_parallel_map_single_item(item):
    """Property: parallel_map works with single item."""
    result = parallel_map(square, [item], n_jobs=1)
    assert result == [item * item]
    
    result_parallel = parallel_map(square, [item], n_jobs=2)
    assert result_parallel == [item * item]


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(items=st.lists(st.integers(min_value=0, max_value=100), min_size=1, max_size=10))
def test_parallel_map_backend_multiprocessing(items):
    """Property: Backend='multiprocessing' works correctly."""
    result = parallel_map(square, items, n_jobs=1, backend="multiprocessing")
    expected = [x * x for x in items]
    assert result == expected


# ============================================================================
# Property Tests: None Seed Handling
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(n=st.integers(min_value=1, max_value=10))
def test_spawn_seeds_none_produces_correct_count(n):
    """Property: spawn_seeds(None, n) produces exactly n None values."""
    seeds = spawn_seeds(None, n)
    
    assert len(seeds) == n
    assert seeds == [None] * n


@pytest.mark.property
def test_parallel_map_with_none_seeds_works():
    """Property: parallel_map works when seeds are None."""
    # This tests that the system doesn't crash with None seeds
    # Results will be non-deterministic but should complete
    seeds = spawn_seeds(None, 3)
    result = parallel_map(random_from_seed, seeds, n_jobs=1)
    
    assert len(result) == 3
    assert all(isinstance(r, float) for r in result)
    assert all(0.0 <= r <= 1.0 for r in result)
