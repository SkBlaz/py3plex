# Flaky Tests Guide

## What are Flaky Tests?

Flaky tests are tests that sometimes pass and sometimes fail, without any changes to the code. They are one of the most frustrating issues in software development because they:
- Erode trust in the test suite
- Waste developer time investigating false failures
- Block CI/CD pipelines unnecessarily
- Make it harder to catch real bugs

## Common Causes of Flakiness

### 1. Random Number Generation

**Problem:** Tests that use random values without setting seeds
```python
#  BAD - Will produce different results each run
import random
def test_random_selection():
    value = random.randint(1, 100)
    assert value < 50  # Will fail ~50% of the time
```

**Solution:** Always set seeds
```python
#  GOOD - Deterministic behavior
import random
def test_random_selection():
    random.seed(42)
    value = random.randint(1, 100)
    assert value == 51  # Will always pass
```

### 2. Timing Dependencies

**Problem:** Tests that rely on execution speed or timing
```python
#  BAD - Will fail on slow systems
import time
def test_performance():
    start = time.time()
    expensive_operation()
    elapsed = time.time() - start
    assert elapsed < 1.0  # Might fail on CI runners
```

**Solution:** Use relative comparisons or mock time
```python
#  GOOD - Tests relative performance
def test_performance():
    start = time.time()
    fast_operation()
    fast_time = time.time() - start
    
    start = time.time()
    slow_operation()
    slow_time = time.time() - start
    
    # Test that slow is actually slower, not absolute time
    assert slow_time > fast_time
```

## Handling Flaky Tests

### 1. Mark Known Flaky Tests

Use `@pytest.mark.flaky` to automatically retry failing tests:

```python
import pytest

@pytest.mark.flaky(reruns=3, reruns_delay=1)
def test_might_be_flaky():
    """This test has known flakiness."""
    # Test that occasionally fails due to statistical variance
    assert statistical_test_with_randomness()
```

### 2. Best Practices

 **DO:**
- Always set random seeds
- Use pytest fixtures for test data
- Sort collections before comparison
- Use pytest.approx() for floats
- Mock external dependencies
- Test locally multiple times before pushing

 **DON'T:**
- Don't use time.sleep() in tests
- Don't test absolute performance
- Don't ignore flaky tests
- Don't assume dict/set ordering
- Don't test with production data
- Don't merge code with new flaky tests

## py3plex Flaky Tests

### Identified Flaky Tests

1. **`tests/verification/test_uq_correctness.py::test_perturbation_produces_variance`**
   - **Cause:** Statistical test with small network can produce edge cases
   - **Status:** Marked with `@pytest.mark.flaky(reruns=3, reruns_delay=1)`
   - **Issue:** Network too small or drop probability too low for reliable variance detection

### Tests with Timing Dependencies

These tests use timing assertions and may fail on slow systems:
- `tests/test_dsl_community_uq_integration.py`
- `tests/test_multilayer_visualizations.py`
- `tests/test_sir_multiplex.py`
- `tests/test_multilayer_quality_metrics.py`
- `tests/test_supra_matrix_function_centrality.py`

**Note:** All timing assertions use generous thresholds (20-30 seconds) to accommodate slow CI runners.

## Resources

- [pytest-rerunfailures](https://github.com/pytest-dev/pytest-rerunfailures) - Automatic retry plugin
- [Google Testing Blog](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html)
- [Martin Fowler](https://martinfowler.com/articles/nonDeterminism.html) - Non-determinism in tests

---

**Last Updated:** 2026-02-01
