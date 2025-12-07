# TODO Tracking Document

This document tracks all TODO items found in the py3plex repository, their status, and implementation notes.

## Summary

- **Total TODOs Found**: 19 (7 code + 12 documentation)
- **Completed**: 3 code TODOs
- **In Progress**: 0
- **Remaining**: 4 code + 12 documentation TODOs

---

## Code TODOs

### ✅ COMPLETED: 1. multinet.py get_tensor() method
**File**: `py3plex/core/multinet.py:2305`  
**Original TODO**: `TODO` (empty docstring)  
**Status**: ✅ **COMPLETED**  
**Implementation Date**: 2025-12-07  

**Solution**: Implemented full `get_tensor()` method that:
- Returns supra-adjacency matrix in various sparse formats (BSR, CSR, CSC, COO, LIL, DOK)
- Includes comprehensive docstring with examples
- Supports conversion between sparse matrix formats
- Includes error handling with warnings for invalid formats
- Tested with 13 comprehensive unit tests

**Files Changed**:
- `py3plex/core/multinet.py` - Implementation
- `tests/test_tensor_representation.py` - Test suite (13 tests)

---

### ✅ COMPLETED: 2. graph_ops.py to_subgraph() TODO
**File**: `py3plex/graph_ops.py:834`  
**Original TODO**: "TODO: Currently returns a new multi_layer_network with the selected nodes and all edges between them. Full implementation depends on py3plex's subnetwork extraction capabilities."  
**Status**: ✅ **COMPLETED**  
**Implementation Date**: 2025-12-07  

**Solution**: The method was already fully implemented with:
- Support for py3plex's native `subnetwork()` method
- Fallback implementation for manual subgraph construction
- Proper node and edge copying
- Removed obsolete TODO and updated docstring to reflect current implementation

**Files Changed**:
- `py3plex/graph_ops.py` - Removed TODO, updated docstring

**Notes**: The TODO was outdated. The method had complete implementation with both native subnetwork support and manual fallback.

---

### ✅ COMPLETED: 3. hedwig adjustment.py holdout method
**File**: `py3plex/algorithms/hedwig/stats/adjustment.py:10`  
**Original TODO**: `TODO: The holdout approach.`  
**Status**: ✅ **COMPLETED**  
**Implementation Date**: 2025-12-07  

**Solution**: Implemented complete holdout validation method for multiple testing adjustment:
- Splits ruleset into discovery and holdout sets using configurable ratio
- Filters rules on discovery set by significance level (alpha)
- Validates filtered rules against holdout set
- Conservative approach to reduce false positives
- Includes comprehensive docstring with parameters and notes
- Tested with 9 unit tests

**Files Changed**:
- `py3plex/algorithms/hedwig/stats/adjustment.py` - Implementation
- `tests/test_hedwig_adjustment.py` - Test suite (9 tests)

**Implementation Details**:
```python
def _holdout(ruleset, holdout_ratio=0.3, alpha=0.05):
    # Splits data, filters discovery set, validates on holdout
    # Returns conservative filtered ruleset
```

---

### 🔴 REMAINING: 4. label_propagation.py TensorFlow implementation
**File**: `py3plex/algorithms/network_classification/label_propagation.py:234`  
**Original TODO**: `TODO: implement` (TensorFlow-based label propagation)  
**Status**: 🔴 **DEFERRED - Requires major implementation**  

**Context**: Placeholder function for TensorFlow-based label propagation:
```python
def label_propagation_tf() -> None:
    """TensorFlow-based label propagation (TODO: implement).
    
    Placeholder for future TensorFlow implementation.
    """
    # todo..
    pass
```

**Why Not Implemented**:
1. **Major Feature**: Requires significant implementation effort
2. **TensorFlow Dependency**: Would add a heavy optional dependency
3. **Design Decisions Needed**:
   - API design for TF-based propagation
   - Integration with existing label propagation methods
   - Performance benchmarking strategy
   - GPU support considerations

**Recommendation**: 
- Keep as placeholder for future enhancement
- Consider as a separate feature branch/PR
- Requires discussion with maintainers on:
  - Whether TensorFlow integration is desired
  - API design
  - Performance requirements

**Estimated Effort**: 2-3 days for full implementation with tests

---

### 🔴 REMAINING: 5. hedwig learner.py advanced features
**File**: `py3plex/algorithms/hedwig/learners/learner.py:18`  
**Original TODO**: 
```
TODO:
    - bottom clause approach
    - feature construction
```
**Status**: 🔴 **DEFERRED - Requires domain expertise**  

**Context**: Enhancement requests for the Hedwig learner class.

**Why Not Implemented**:
1. **Specialized Domain**: Requires deep knowledge of inductive logic programming and Hedwig algorithms
2. **Research-Level Features**: These are advanced ILP techniques
3. **Existing Learner Works**: Current implementation is functional without these features
4. **No Clear Specification**: Needs more detailed requirements

**Background**:
- **Bottom Clause Approach**: ILP technique for generating candidate rules from examples
- **Feature Construction**: Automatic generation of new features from existing ones

**Recommendation**:
- Keep as enhancement request in docstring
- Requires collaboration with algorithm domain expert
- Should be addressed in dedicated feature development cycle
- Consider creating GitHub issue for community input

**Estimated Effort**: 5-7 days per feature with research and testing

---

### 🔴 REMAINING: 6. example_CBSSD.py UniProt generalization
**File**: `examples/advanced/example_CBSSD.py:4`  
**Original TODO**: `# this works for UniProt identifiers TODO:generalize!`  
**Status**: 🔴 **DEFERRED - Example-specific enhancement**  

**Context**: Example code for community-based semantic subgroup discovery currently hardcoded for UniProt identifiers.

**Why Not Implemented**:
1. **Example Code**: Not core library functionality
2. **Domain-Specific**: Requires knowledge of biological databases and identifier schemes
3. **Limited Impact**: Affects one example file, not core features
4. **Works As Is**: Current example is functional for its intended use case

**What Generalization Would Involve**:
- Support for other biological identifier schemes (Ensembl, NCBI, etc.)
- Configurable identifier type parameter
- Abstraction of RDF mapping logic
- Additional validation for different identifier formats

**Recommendation**:
- Keep as enhancement note in example
- Consider as separate example for different identifier types
- Document current limitation in example docstring
- Add to "future examples" wishlist

**Estimated Effort**: 1-2 days including testing with different identifier types

---

### 🔴 REMAINING: 7. example_CBSSD.py table export
**File**: `examples/advanced/example_CBSSD.py:61`  
**Original TODO**: `# initiate the learning part (TODO: export this as table of some sort)`  
**Status**: 🔴 **DEFERRED - Enhancement request**  

**Context**: Hedwig learning results should be exportable as a table.

**Why Not Implemented**:
1. **Unclear Requirements**: "some sort" is vague - what format? CSV, DataFrame, JSON?
2. **Hedwig Output**: Need to understand hedwig.run() output structure
3. **API Consideration**: Should this be in hedwig module or example?
4. **Example Code**: Lower priority than core features

**What Would Be Needed**:
1. Analyze hedwig.run() return value or output structure
2. Design table schema for rule representation
3. Implement export function (to CSV, pandas DataFrame, or similar)
4. Add to example or hedwig utilities

**Recommendation**:
- Add utility function to hedwig module: `hedwig.export_results_to_table()`
- Support multiple formats: CSV, pandas DataFrame, JSON
- Document in example how to use export function
- Consider adding to main hedwig API if broadly useful

**Estimated Effort**: 1 day including documentation and tests

---

## Documentation TODOs

### 🔴 REMAINING: 8. Changelog Documentation
**Files**: 
- `docs/_sources/project/changelog.rst.txt:5,13,23`
- `docfiles/reference/configuration.rst` (if exists)

**Original TODOs**:
- "TODO: This page needs to be populated with release history from the GitHub releases."
- "TODO: Add release notes for version 1.0.0"
- "TODO: Add historical release notes"

**Status**: 🔴 **REMAINING**  
**Priority**: High (important for users)  

**What's Needed**:
1. Extract release information from GitHub releases
2. Document version 1.0.0 and 1.0.1 changes
3. Add historical release notes from git history
4. Follow standard changelog format (e.g., Keep a Changelog)

**Estimated Effort**: 2-3 hours

---

### 🔴 REMAINING: 9. Configuration Documentation
**File**: `docs/_sources/reference/configuration.rst.txt:5,10,19`  

**Original TODOs**:
- "TODO: Document configuration file formats and options"
- "TODO: Document environment variables used by py3plex"
- "TODO: Document logging configuration"

**Status**: 🔴 **REMAINING**  
**Priority**: Medium  

**What's Needed**:
1. Document py3plex configuration system (if any)
2. List all environment variables
3. Explain logging configuration options
4. Provide examples of configuration files

**Estimated Effort**: 3-4 hours

---

### 🔴 REMAINING: 10. Book Chapter Expansions
**Files**: Multiple book chapter files  

**Original TODOs** (from book/):
- `part3_dsl/chapter09_builder_api_explain.rst:4` - Expand with builder API examples
- `part3_dsl/chapter10_advanced_queries_workflows.rst:301` - Expand from advanced DSL patterns
- `part5_systems/chapter17_gui_overview.rst:4` - High-level GUI overview
- `part5_systems/chapter15_testing_validation.rst:4` - Consolidate from tests/ structure
- `part5_systems/chapter16_reproducible_environments.rst:4` - Environment setup practices
- `part4_case_studies/chapter12_case_study_1.rst:46` - Develop from examples
- `part4_case_studies/chapter13_case_study_2.rst:4` - Dynamics/epidemic modeling case
- `part4_case_studies/chapter14_case_study_3.rst:4` - Advanced DSL case study
- `part2_working/chapter06_visualization_exploration.rst:4` - Expand from visualization guide

**Status**: 🔴 **REMAINING**  
**Priority**: Medium (book is supplementary)  

**What's Needed**:
Each chapter needs expansion from existing documentation and examples. This is a significant documentation project.

**Estimated Effort**: 1-2 weeks for complete book expansion

---

### 🔴 REMAINING: 11. Benchmark Results Documentation
**File**: `docs/_sources/project/benchmarking.rst.txt:102`  
**Original TODO**: "TODO: Add benchmark results from benchmarks/ directory"  

**Status**: 🔴 **REMAINING**  
**Priority**: Low  

**What's Needed**:
1. Run benchmarks from benchmarks/ directory
2. Collect and format results
3. Add to documentation with analysis
4. Create visualizations if appropriate

**Estimated Effort**: 2-3 hours

---

### 🔴 REMAINING: 12. GUI Architecture Documentation
**File**: `docs/_sources/gui_architecture.rst.txt:386`  
**Original TODO**: "Production Hardening (TODO)"  

**Status**: 🔴 **REMAINING**  
**Priority**: Low (GUI is supplementary)  

**What's Needed**:
Document production deployment considerations for the GUI:
- Security hardening
- Performance optimization
- Deployment configurations
- Monitoring and logging

**Estimated Effort**: 2-3 hours

---

## Recommendations

### Immediate Actions (Can be completed now)
1. ✅ **DONE**: Implement `get_tensor()` method
2. ✅ **DONE**: Remove obsolete TODO from `to_subgraph()`
3. ✅ **DONE**: Implement `_holdout()` method
4. **Document changelog** - Extract from GitHub releases
5. **Document configuration** - Survey config system and document

### Short-term (1-2 week effort)
6. Add table export utility for hedwig results
7. Create additional example for different identifiers
8. Complete benchmark results documentation
9. Expand priority book chapters

### Long-term (Requires design decisions)
10. TensorFlow label propagation - Needs maintainer input on design
11. Hedwig learner enhancements - Needs domain expert collaboration
12. Complete book expansion - Ongoing documentation project

### Technical Debt / Nice-to-have
- GUI production hardening docs
- Remaining book chapter expansions
- Example code generalizations

---

## Testing Coverage

### Completed Tests
- ✅ `test_tensor_representation.py` - 13 tests for get_tensor() (all passing)
- ✅ `test_hedwig_adjustment.py` - 9 tests for holdout method (all passing)
- ✅ `test_graph_ops.py` - Existing tests cover to_subgraph()

### Test Commands
```bash
# Run all new tests
pytest tests/test_tensor_representation.py tests/test_hedwig_adjustment.py -v

# Run with coverage
pytest tests/test_tensor_representation.py tests/test_hedwig_adjustment.py --cov=py3plex --cov-report=term
```

---

## Notes for Future Implementation

### TensorFlow Label Propagation (TODO #4)
If implementing, consider:
- Making TensorFlow an optional dependency
- Providing CPU and GPU implementations
- Benchmarking against existing methods
- Following sklearn-like API for consistency

### Hedwig Enhancements (TODO #5)
If implementing:
- Consult ILP literature for bottom clause construction
- Review feature construction techniques in similar tools
- Ensure backward compatibility with existing learner API
- Add comprehensive examples

### Documentation TODOs (TODOs #8-12)
- Consider using automated tools for changelog generation
- Use consistent format across all documentation
- Cross-link related documentation sections
- Include code examples in all conceptual docs

---

**Last Updated**: 2025-12-07  
**Updated By**: GitHub Copilot Agent  
**Repository**: SkBlaz/py3plex
