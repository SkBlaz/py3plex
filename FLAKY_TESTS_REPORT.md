# Flaky Test Analysis Report

## Executive Summary

This report identifies potentially flaky tests in the py3plex test suite based on code analysis and common flaky test patterns.

**Date:** 2026-02-01
**Repository:** SkBlaz/py3plex
**Total Test Files:** ~376

## Findings

### 1. Confirmed Flaky Test

**Location:** `tests/verification/test_uq_correctness.py`

**Issue:** Explicitly documented as potentially flaky
```python
# Note: This test may be flaky if network is too small or drop probability too low.
```

**Root Cause:** Uncertainty quantification with small sample sizes can produce edge cases

**Severity:** ⚠️ Medium

**Recommendation:** 
- Increase network size for more stable statistical behavior
- Adjust drop probability thresholds
- Add @pytest.mark.flaky decorator with reruns

---

### 2. Tests with Random Number Generation Issues

#### 2.1 `tests/test_contracts_integration.py`

**Issue:** Uses `random.randint()` without explicit seed setting
```python
import random
random.seed(42)  # Seed is set at module level
# BUT later in loop:
i = random.randint(0, n_nodes - 1)
j = random.randint(0, n_nodes - 1)
```

**Severity:** ✅ Low (seed is actually set at module level)

**Status:** Likely stable, but should set seed at test level for clarity

---

#### 2.2 `tests/fixtures/transformations.py`

**Issue:** Random operations in test fixtures
```python
import random
random.seed(seed)  # Seed is passed as parameter
random.shuffle(edges)
if random.random() > drop_prob:
```

**Severity:** ✅ Low (seed is properly parameterized)

**Status:** Properly handled with seed parameter

---

#### 2.3 `tests/test_multilayer_visualizations.py`

**Issue:** Uses random without setting seed
```python
src = str(random.randint(0, 99))
tgt = str(random.randint(0, 99))
```

**Severity:** ⚠️ Medium

**Recommendation:** Add `random.seed(42)` at start of each test function

---

### 3. Tests with Timing Dependencies

#### 3.1 Performance Timing Tests

**Affected Files:**
- `tests/test_dsl_community_uq_integration.py`
- `tests/test_multilayer_visualizations.py`
- `tests/test_sir_multiplex.py`
- `tests/test_multilayer_quality_metrics.py`
- `tests/test_supra_matrix_function_centrality.py`

**Pattern:**
```python
start = time.time()
# ... operation ...
elapsed = time.time() - start
assert elapsed < some_threshold  # Flaky on slow systems
```

**Severity:** ⚠️ Medium

**Recommendation:**
- Use relative performance comparisons instead of absolute time limits
- Increase timeout thresholds with safety margins
- Consider using pytest's timeout mechanism instead
- Skip performance tests in CI with slow runners

---

#### 3.2 `tests/property/test_profiling_properties.py`

**Issue:** Uses `time.sleep()` in test
```python
time.sleep(sleep_time)
```

**Severity:** ⚠️ Medium

**Context:** Likely testing profiling functionality, but sleep can be unreliable

**Recommendation:** Mock time if possible, or increase sleep tolerances

---

### 4. Non-Deterministic Test Patterns

#### 4.1 Timestamp Tests

**File:** `tests/test_program.py`
```python
creation_timestamp=time.time(),
```

**Severity:** ✅ Low

**Context:** Appears to be testing timestamp storage, not comparison

---

## Summary by Severity

| Severity | Count | Files |
|----------|-------|-------|
| 🔴 High | 0 | - |
| ⚠️ Medium | 7 | test_uq_correctness.py, test_multilayer_visualizations.py, test_dsl_community_uq_integration.py, test_sir_multiplex.py, test_multilayer_quality_metrics.py, test_supra_matrix_function_centrality.py, test_profiling_properties.py |
| ✅ Low | 3 | test_contracts_integration.py, transformations.py, test_program.py |

---

## Recommended Actions

### Immediate (High Priority)

1. **Add pytest-rerunfailures to dependencies**
   ```bash
   pip install pytest-rerunfailures
   ```

2. **Mark known flaky test**
   ```python
   # In tests/verification/test_uq_correctness.py
   @pytest.mark.flaky(reruns=3, reruns_delay=1)
   def test_that_may_be_flaky():
       ...
   ```

### Short-term (Medium Priority)

3. **Fix random seed issues in visualization tests**
   - Add explicit `random.seed(42)` to `test_multilayer_visualizations.py`

4. **Review timing-based assertions**
   - Increase timeout thresholds by 2-3x
   - Add environment-based timeout scaling
   - Consider marking as `@pytest.mark.slow`

### Long-term (Low Priority)

5. **Implement flaky test monitoring**
   - Run `detect_flaky_tests.py` weekly in CI
   - Track flaky test metrics over time
   - Set target: < 1% flaky rate

6. **Update contributing guidelines**
   - Require random seeds in all new tests
   - Prohibit absolute timing assertions
   - Mandate multiple local runs before PR

---

## Testing the Detection System

### Quick Check (2-3 minutes)
```bash
python quick_flaky_check.py
```

### Full Analysis (30-60 minutes)
```bash
# Run tests 10 times to catch intermittent failures
python detect_flaky_tests.py --runs 10 --output flaky_report.json

# Test specific subset
python detect_flaky_tests.py --runs 5 --test-subset tests/test_multilayer_visualizations.py
```

### Integration with CI
Add to `.github/workflows/flaky-tests.yml`:
```yaml
name: Nightly Flaky Test Detection

on:
  schedule:
    - cron: '0 3 * * *'  # 3 AM daily

jobs:
  detect-flaky:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
      - run: pip install -e .[test]
      - run: python detect_flaky_tests.py --runs 10
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: flaky-report
          path: flaky_tests_report.json
```

---

## Best Practices Going Forward

1. ✅ **Always set random seeds** in tests using randomness
2. ✅ **Avoid absolute timing assertions** - use relative comparisons
3. ✅ **Use pytest fixtures** for deterministic test data
4. ✅ **Mock external dependencies** (network, filesystem)
5. ✅ **Sort collections** before comparison
6. ✅ **Use pytest.approx()** for floating-point comparisons
7. ✅ **Test locally multiple times** before pushing

---

## Tools Provided

1. **`detect_flaky_tests.py`** - Full flaky test detection system
2. **`quick_flaky_check.py`** - Quick sanity check (2-3 minutes)
3. **`docs/flaky_tests_guide.md`** - Comprehensive guide for developers

---

## Conclusion

The py3plex test suite appears to be **relatively stable** with only a few potential flaky tests identified:

- ✅ **Good:** Most tests properly set random seeds
- ✅ **Good:** Test infrastructure includes proper markers and timeouts
- ⚠️ **Caution:** Some timing-based assertions may fail on slow systems
- ⚠️ **Caution:** One documented flaky test in UQ testing

**Overall Assessment:** The test suite is in good shape with minimal flaky test risk. The identified issues are manageable and have clear remediation paths.

**Recommended Next Steps:**
1. Install pytest-rerunfailures
2. Add @pytest.mark.flaky to test_uq_correctness.py
3. Fix random seed in test_multilayer_visualizations.py
4. Set up weekly flaky test monitoring in CI

---

## References

- [pytest-rerunfailures documentation](https://github.com/pytest-dev/pytest-rerunfailures)
- [Google Testing Blog - Flaky Tests](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html)
- [Martin Fowler - Non-Determinism in Tests](https://martinfowler.com/articles/nonDeterminism.html)
