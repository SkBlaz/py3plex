# Remaining Mypy Type Errors - October 14, 2025

## Summary

**Current Status**: 40 errors in 18 files (down from 82 errors in 27 files)  
**Progress**: 51% reduction (42 errors fixed)  
**Estimated Effort**: 1-2 days to resolve all remaining errors

## Error Breakdown by Type

| Error Type | Count | Description |
|------------|-------|-------------|
| no-any-return | 9 | Functions returning `Any` instead of declared type |
| assignment | 9 | Type incompatibility in variable assignments |
| index | 4 | Invalid dictionary key type |
| attr-defined | 4 | Missing attributes on modules/classes |
| var-annotated | 4 | Missing type annotations |
| return-value | 2 | Incompatible return type |
| list-item | 2 | List item type mismatch |
| call-arg | 2 | Too few function arguments |
| no-redef | 1 | Variable redefinition |
| import-untyped | 1 | Missing stub for `six` library |
| operator | 1 | Unsupported operand types |
| return | 1 | Missing return statement |

## Remaining Errors by File

### High Priority (Core functionality)

#### 1. `py3plex/core/multinet.py` (1 error)
- Line 1336: `multi_layer_network` has no attribute `print_basic_stats` [attr-defined]
- **Fix**: The method exists but may not be properly defined. Need to verify class definition.

#### 2. `py3plex/core/converters.py` (2 errors)
- Line 142: Incompatible assignment (tuple vs dict) [assignment]
- Line 143: Incompatible return type [return-value]
- **Fix**: Review function return type and ensure consistency.

#### 3. `py3plex/core/nx_compat.py` (1 error)
- Line 27: Returning Any from function declared to return str [no-any-return]
- **Fix**: Add explicit return type annotation or cast.

### Medium Priority (I/O System)

#### 4. `py3plex/io/converters.py` (4 errors)
- Lines 351, 358, 359: Invalid index type Hashable for dict [index]
- Line 355: Variable redefinition [no-redef]
- **Fix**: Use proper tuple type for dictionary keys or adjust type hints.

#### 5. `py3plex/io/api.py` (2 errors)
- Lines 158, 200: Too few arguments [call-arg]
- **Fix**: Review function signatures and add missing required arguments.

#### 6. `py3plex/io/schema.py` (1 note)
- Line 286: Untyped function bodies not checked [annotation-unchecked]
- **Fix**: Add type hints to function parameters.

### Community Detection (5 files, 15 errors)

#### 7. `py3plex/algorithms/community_detection/node_ranking.py` (1 error)
- Line 111: Returning Any from function [no-any-return]

#### 8. `py3plex/algorithms/community_detection/community_measures.py` (3 errors)
- Line 25: Incompatible assignment (list vs dict) [assignment]
- Lines 52, 65: Returning Any from typed functions [no-any-return]

#### 9. `py3plex/algorithms/community_detection/community_ranking.py` (3 errors)
- Line 46: Need type annotation for "clusters" [var-annotated]
- Lines 54, 59: Incompatible assignments [assignment]

#### 10. `py3plex/algorithms/community_detection/multilayer_benchmark.py` (4 errors)
- Line 466: Need type annotation for "assigned" [var-annotated]
- Line 519: Incompatible assignment (list vs set) [assignment]
- Line 555: Returning Any from typed function [no-any-return]
- Line 588: Incompatible assignment (ndarray vs int) [assignment]

### Statistics & Algorithms (4 files, 8 errors)

#### 11. `py3plex/algorithms/statistics/enrichment_modules.py` (1 error)
- Line 67: Returning Any from function [no-any-return]

#### 12. `py3plex/algorithms/statistics/correlation_networks.py` (1 error)
- Line 42: Returning Any from function [no-any-return]

#### 13. `py3plex/algorithms/statistics/critical_distances.py` (1 error)
- Line 281: Need type annotation for "results" [var-annotated]

#### 14. `py3plex/algorithms/statistics/topology.py` (4 errors)
- Lines 96, 138: Incompatible assignment (str vs int) [assignment]
- Line 131: Incompatible assignment (list vs ndarray) [assignment]
- Line 143: Unsupported operand types (str + int) [operator]

#### 15. `py3plex/algorithms/hedwig/__init__.py` (3 errors)
- Line 11: Module attributes not found [attr-defined]
- **Note**: May be related to dynamic imports or missing definitions.

### Wrappers & Visualization (3 files, 6 errors)

#### 16. `py3plex/wrappers/benchmark_nodes.py` (2 errors)
- Line 13: Missing stubs for "six" library [import-untyped]
- Line 167: Incompatible return type (dict[float, ...] vs dict[str, Any]) [return-value]
- **Fix**: `pip install types-six` for first error, adjust return type for second.

#### 17. `py3plex/wrappers/node2vec_embedding.py` (3 errors)
- Line 175: Invalid index type (float vs str) [index]
- Line 180: List item type mismatch (float vs int) [list-item] (2 errors)

#### 18. `py3plex/visualization/bezier.py` (2 errors)
- Line 49: Returning Any from typed function [no-any-return]
- Line 52: Missing return statement [return]

#### 19. `py3plex/visualization/layout_algorithms.py` (2 errors)
- Line 108: Need type annotation for "norm" [var-annotated]
- Line 134: Returning Any from typed function [no-any-return]

## Recommended Fix Order

### Phase 1: Quick Wins (30 minutes)
1. Install types-six: `pip install types-six`
2. Add simple type annotations (var-annotated errors) - 4 fixes
3. Fix obvious type casts (str vs int, float vs str) - 3 fixes

### Phase 2: Core Fixes (2-3 hours)
1. Fix core/converters.py type mismatches - 2 fixes
2. Fix core/nx_compat.py return type - 1 fix
3. Fix core/multinet.py attribute error - 1 fix
4. Fix I/O system errors (converters, api) - 6 fixes

### Phase 3: Algorithm Fixes (3-4 hours)
1. Fix no-any-return errors with explicit casts - 9 fixes
2. Fix assignment incompatibilities - 9 fixes
3. Fix remaining edge cases - 5 fixes

## Testing After Fixes

After fixing all errors:
```bash
# Verify no errors remain
python3 -m mypy py3plex/ --ignore-missing-imports

# Update Makefile to remove || true
sed -i 's/@$(MYPY) $(PACKAGE)\/ --ignore-missing-imports || true/@$(MYPY) $(PACKAGE)\/ --ignore-missing-imports/' Makefile

# Verify CI enforcement works
make lint
```

## Related Documents

- **LLM.md**: Main roadmap document
- **OPEN_ISSUES_ANALYSIS_2025-10-14.md**: Comprehensive analysis of all open issues
- **ROADMAP_STATUS_SUMMARY.md**: Quick reference for roadmap status

---

**Last Updated**: October 14, 2025  
**Status**: 51% complete (42/82 errors fixed)  
**Next Milestone**: Complete remaining 40 errors to enable full mypy enforcement in CI
