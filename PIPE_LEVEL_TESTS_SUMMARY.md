# DSL Pipe-Level Test Coverage Summary

## Overview

This document summarizes the comprehensive pipe-level test coverage added for the py3plex DSL (Domain-Specific Language) builder API in response to issue "test coverage for dsl - more involved tests missing, pipe level".

## What Are "Pipe-Level" Tests?

Pipe-level tests refer to tests that validate complex method chaining (piping) scenarios in the DSL builder API. The DSL builder API allows users to construct queries by chaining methods like:

```python
result = (
    Q.nodes()
     .from_layers(L["social"] + L["work"])
     .where(degree__gt=5)
     .compute("betweenness_centrality", alias="bc")
     .order_by("-bc")
     .limit(20)
     .execute(network)
)
```

While basic chaining was tested, complex multi-step pipelines with various combinations and edge cases were not comprehensively covered.

## Test File Added

**File:** `tests/test_dsl_pipes.py`

**Total Tests:** 38 comprehensive test cases across 11 test classes

## Test Classes and Coverage

### 1. TestLongPipes (5 tests)
Tests progressively longer pipelines from 5 to 9 chained methods:
- 5-step: `from_layers → where → compute → order_by → limit`
- 6-step: Multiple `compute()` calls
- 7-step: Multiple `where()` calls
- 8-step: Parameterized queries with `Param.int()`
- 9-step: Complex layer algebra with multiple ordering

### 2. TestLayerAlgebraInPipes (4 tests)
Tests layer algebra operations combined with other pipe operations:
- Layer union (`L["social"] + L["work"]`) with filtering and compute
- Layer difference (`L["social"] - L["hobby"]`) with ordering
- Layer intersection (`L["social"] & L["work"]`) with multiple conditions
- Complex nested layer expressions: `(L["social"] + L["work"]) & L["hobby"]`

### 3. TestMultipleMethodCalls (3 tests)
Tests calling the same method multiple times in a chain:
- Multiple `where()` calls (should AND conditions together)
- Multiple `compute()` calls (should accumulate measures)
- Multiple `order_by()` calls (multi-key sorting)

### 4. TestQueryReusability (4 tests)
Tests reusing and composing query builders:
- Reusing a base query with different extensions
- Building queries incrementally (step by step)
- Converting partial queries to AST
- Converting partial queries to DSL strings

### 5. TestExportMethodsInPipes (3 tests)
Tests export methods integrated into query pipelines:
- `to_pandas()` export after complex query
- `to_dict()` export after filtering and computation
- `to_networkx()` export after node selection

### 6. TestExplainInPipes (2 tests)
Tests EXPLAIN mode with complex pipelines:
- Simple pipeline execution plan
- Complex pipeline with layer algebra and multiple operations

### 7. TestEdgeCasesInPipes (4 tests)
Tests edge cases and error scenarios:
- Pipelines that return empty results
- Limits larger than available results
- Ordering before computing (order applies after compute)
- Empty network pipelines

### 8. TestParameterizedPipes (3 tests)
Tests parameterized queries in complex pipelines:
- Multiple parameters in a single pipeline
- Reusing parameterized queries with different values
- Parameters in layer expressions (current behavior verification)

### 9. TestErrorHandlingInPipes (3 tests)
Tests error handling in the middle of pipes:
- Unknown measure raises error with suggestion
- Invalid layer returns empty results (not error)
- Invalid comparison operator raises ValueError

### 10. TestInteropWithLegacyAPI (2 tests)
Tests interoperability between builder API and legacy DSL:
- Builder result equivalence to legacy DSL result
- Complex query equivalence verification

### 11. TestComputeAliasesInPipes (3 tests)
Tests compute with aliases in various pipe scenarios:
- Single compute with alias
- Multiple computes with different aliases
- Mixed aliased and non-aliased computes

### 12. TestOrderingEdgeCases (2 tests)
Tests edge cases in ordering operations:
- Ordering by multiple keys
- Ordering when some nodes lack computed values

## Bug Fixed

### ParamRef in Limit Clauses

**File:** `py3plex/dsl/executor.py`

**Problem:** When using `Param.int("n")` in a `.limit()` clause, the parameter was not being resolved before use as a slice index, causing a `TypeError: slice indices must be integers or None or have an __index__ method`.

**Solution:**
1. Implemented proper parameter binding in `_bind_parameters()` to resolve `ParamRef` in limit clauses before execution
2. Added `params` parameter threading through the entire condition evaluation chain:
   - `_execute_select()` → `_filter_by_conditions()` → `_evaluate_conditions()` → `_evaluate_atom()` → `_evaluate_comparison()`
3. Parameters in WHERE conditions are now resolved dynamically during evaluation using `_resolve_param()`

**Code Changes:**
```python
# Before: stub implementation
def _bind_parameters(query: Query, params: Dict[str, Any]) -> Query:
    return query

# After: proper parameter resolution
def _bind_parameters(query: Query, params: Dict[str, Any]) -> Query:
    import copy
    bound_query = copy.deepcopy(query)
    if bound_query.select and bound_query.select.limit is not None:
        bound_query.select.limit = _resolve_param(bound_query.select.limit, params)
    return bound_query
```

## Test Results

### New Tests
✅ **38 tests in test_dsl_pipes.py** - All pass

### Regression Tests
✅ **178 tests in test_dsl.py + test_dsl_v2.py** - All pass
✅ **346 total DSL tests** - All pass (including new pipe tests)

### Coverage Added
- Long method chains (5-9 steps)
- All method combinations
- Layer algebra in pipes
- Multiple calls to same method
- Query reusability patterns
- Export integrations
- EXPLAIN mode with pipes
- Parameterized pipes
- Error handling in chains
- Edge cases (empty results, limits, etc.)
- Interop with legacy API

## Examples of New Test Scenarios

### Example 1: 9-Step Pipeline
```python
result = (
    Q.nodes()
     .from_layers((L["social"] + L["work"]) - L["hobby"])
     .where(degree__gt=0)
     .compute("degree")
     .compute("clustering")
     .order_by("-degree")
     .order_by("clustering")
     .limit(5)
     .execute(network)
)
```

### Example 2: Parameterized Reusable Query
```python
q = (
    Q.nodes()
     .where(layer=Param.str("target_layer"), degree__gt=Param.int("min_deg"))
     .compute("degree")
     .limit(Param.int("n"))
)

# Execute with different parameters
result1 = q.execute(network, target_layer="social", min_deg=1, n=5)
result2 = q.execute(network, target_layer="work", min_deg=0, n=10)
```

### Example 3: Multiple Where Clauses
```python
result = (
    Q.nodes()
     .where(layer="social")
     .where(degree__gt=1)
     .where(degree__lt=5)
     .execute(network)
)
# All three conditions are ANDed together
```

## Benefits

1. **Comprehensive Coverage**: Tests now cover complex real-world query patterns that users will encounter
2. **Bug Prevention**: The ParamRef bug was caught and fixed during test development
3. **Documentation**: Tests serve as examples of how to use the DSL builder API in complex scenarios
4. **Confidence**: 346 passing tests provide confidence that the DSL works correctly in all scenarios
5. **Regression Protection**: Future changes can be validated against this comprehensive test suite

## Future Considerations

1. **Performance Tests**: Consider adding performance benchmarks for long pipelines
2. **Negative Tests**: More error condition tests could be added (malformed queries, type errors, etc.)
3. **Integration Tests**: Tests with real-world sized networks could be valuable
4. **Temporal Queries**: While basic temporal query tests exist, more complex temporal pipelines could be tested

## References

- Issue: "test coverage for dsl - more involved tests missing, pipe level"
- Test File: `tests/test_dsl_pipes.py`
- Fixed File: `py3plex/dsl/executor.py`
- Related Tests: `tests/test_dsl.py`, `tests/test_dsl_v2.py`
- DSL Builder API: `py3plex/dsl/builder.py`
- DSL Documentation: `docfiles/reference/dsl.rst`
