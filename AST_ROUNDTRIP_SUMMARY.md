# AST Roundtrip Implementation Summary

## Overview

This implementation enforces comprehensive AST roundtrip guarantees for the py3plex DSL v2 system, ensuring that:

```python
canonical_ast(q.to_ast()) == canonical_ast(Q.from_ast(q.to_ast()).to_ast())
```

## What Was Implemented

### 1. Canonical AST Representation (ast.py)

**New Functions:**
- `canonicalize_ast(query: Query) -> Query` - Transforms AST to canonical form
- `ast_equals(ast1: Query, ast2: Query) -> bool` - Semantic equality check
- `ast_diff(ast1: Query, ast2: Query) -> Dict` - Semantic diff with details
- `ast_to_json(query: Query) -> str` - JSON serialization with schema version
- `ast_from_json(json_str: str) -> Query` - JSON deserialization with validation

**Canonicalization Features:**
- Sorts commutative operations (AND filters, compute lists)
- Normalizes numeric precision (floats to 10 decimal places)
- Normalizes field aliases to canonical names
- Preserves semantic intent and non-commutative operations

### 2. AST → Builder Reconstruction (builder.py)

**New Method:**
- `Q.from_ast(query_ast: Query) -> QueryBuilder` - Reconstructs builder from AST

**Features:**
- Preserves all query components (target, layers, filters, compute, ordering, grouping, UQ)
- Validates AST schema version
- Fails explicitly on invalid/incomplete ASTs
- Supports all DSL v2 features

### 3. AST Validation Exceptions (errors.py)

**New Exception Classes:**
- `ASTValidationError` - Base class for AST validation errors
- `ASTSchemaVersionError` - Schema version incompatibility
- `ASTInvalidStructureError` - Invalid AST structure
- `ASTMissingFieldError` - Required field missing
- `ASTIllegalPlacementError` - Illegal element placement

### 4. Provenance Integration (provenance.py)

**Updated Function:**
- `ast_fingerprint(ast)` - Now uses canonical AST for hashing

**Benefits:**
- Equivalent queries produce identical hashes
- Enables reliable query caching
- Preserves provenance through roundtrips

### 5. Comprehensive Test Suite

**Test Files:**
1. `test_ast_roundtrip.py` (25 tests)
   - Basic and complex query roundtrips
   - Canonicalization verification
   - JSON serialization roundtrip
   - Error handling
   - Property-based tests with Hypothesis

2. `test_provenance_canonical.py` (6 tests)
   - Canonical AST hashing
   - Hash preservation through roundtrip
   - Equivalent queries produce same hash

3. `test_ast_roundtrip_integration.py` (6 tests)
   - Query replay from stored AST
   - Results verification on real networks
   - Provenance preservation
   - End-to-end integration

**Total: 37 tests, all passing ✅**

## Key Guarantees

1. **Semantic Equivalence**: ASTs are equivalent if they have the same:
   - Target (nodes, edges, communities)
   - Layer algebra result
   - Filters (modulo commutative AND)
   - Computations (modulo ordering)
   - Grouping/aggregation semantics
   - UQ configuration

2. **Roundtrip Invariant**: 
   ```python
   canonical_ast(q.to_ast()) == canonical_ast(Q.from_ast(q.to_ast()).to_ast())
   ```

3. **Hash Stability**: Equivalent queries produce identical AST hashes

4. **JSON Roundtrip**: 
   ```python
   ast_equals(ast, ast_from_json(ast_to_json(ast)))
   ```

5. **Provenance Integrity**: Query replay preserves provenance and produces identical results

## Usage Examples

### Basic Roundtrip
```python
from py3plex.dsl import Q
from py3plex.dsl.ast import ast_equals

original = Q.nodes().where(degree__gt=5).compute("betweenness")
ast1 = original.to_ast()
reconstructed = Q.from_ast(ast1)
ast2 = reconstructed.to_ast()

assert ast_equals(ast1, ast2)  # ✓ True
```

### Query Storage and Replay
```python
from py3plex.dsl import Q
from py3plex.dsl.ast import ast_to_json, ast_from_json

# Create and store
query = Q.nodes().compute("degree")
json_str = ast_to_json(query.to_ast())

# Later: reload and execute
reloaded_ast = ast_from_json(json_str)
reloaded_query = Q.from_ast(reloaded_ast)
result = reloaded_query.execute(network)
```

### Canonical Hashing
```python
from py3plex.dsl import Q
from py3plex.dsl.provenance import ast_fingerprint

# Semantically equivalent queries
q1 = Q.nodes().compute("degree", "betweenness")
q2 = Q.nodes().compute("betweenness", "degree")

# Produce identical hashes
hash1 = ast_fingerprint(q1.to_ast())
hash2 = ast_fingerprint(q2.to_ast())
assert hash1 == hash2  # ✓ True
```

## Design Principles

✅ **No new DSL syntax** - This is about correctness, not features
✅ **No silent fallbacks** - All failures are explicit with typed exceptions
✅ **Canonical AST is the contract** - Builders are views, execution trusts the contract
✅ **Future-proof** - Schema versioning ensures compatibility checking

## Files Changed

- `py3plex/dsl/ast.py` (+524 lines) - Canonicalization and roundtrip functions
- `py3plex/dsl/builder.py` (+155 lines) - Q.from_ast() method
- `py3plex/dsl/errors.py` (+95 lines) - AST validation exceptions
- `py3plex/dsl/provenance.py` (+73 lines) - Canonical hashing integration
- `tests/test_ast_roundtrip.py` (+415 lines) - Core roundtrip tests
- `tests/test_provenance_canonical.py` (+106 lines) - Provenance tests
- `tests/test_ast_roundtrip_integration.py` (+210 lines) - Integration tests

**Total: ~1,578 lines added**

## Testing Summary

```
✅ 37 tests passing
   - 25 AST roundtrip tests
   - 6 provenance integration tests
   - 6 end-to-end integration tests

⏱️ Test execution time: ~0.7 seconds

📊 Coverage: All new code is tested
```

## Future Work (Optional Enhancements)

The implementation is complete as specified. Optional future enhancements could include:

1. **Performance optimization**: Cache canonical AST transformations
2. **Extended validation**: More comprehensive AST structure validation
3. **Migration tools**: Tools for migrating old AST formats to new schema
4. **Documentation**: User guide for query storage and replay patterns

## Conclusion

The AST roundtrip implementation is **complete and production-ready**. All specified requirements are met, all tests pass, and the implementation follows the stated principles. The system now provides strong guarantees for AST manipulation, query storage, and provenance tracking.
