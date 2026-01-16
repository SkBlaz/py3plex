# SBM Implementation Summary

## Overview
Successfully implemented a complete, fully native (pure Python + NumPy/SciPy) Stochastic Block Model (SBM) family for py3plex, meeting all requirements from the GitHub issue.

## Components Implemented

### 1. Core SBM Variants ✅
- **Standard SBM**: Basic stochastic block model
- **DC-SBM**: Degree-corrected variant for heterogeneous networks
- **MMSBM**: Mixed-membership SBM with soft assignments (via `mmsbm_fit()`)
- **Multilayer modes**:
  - `independent`: Separate B matrices per layer
  - `shared_blocks`: Shared memberships, separate B matrices
  - `shared_affinity`: Shared memberships and single B matrix
  - **`coupled`** (NEW): Shared memberships with coupling penalty

### 2. Uncertainty Quantification (UQ) ✅
Location: `py3plex/algorithms/sbm/uq.py`

- **`align_labels_hungarian()`**: Hungarian algorithm for label alignment across runs
- **`compute_node_stability()`**: Per-node stability via entropy or variance
- **`sbm_seed_resampling_uq()`**: Deterministic seed-based UQ with:
  - `numpy.random.Generator` with `PCG64`
  - `SeedSequence.spawn()` for child seeds
  - Consensus partition and confidence scores
  - Co-assignment matrix computation

### 3. Unified API ✅
Location: `py3plex/algorithms/community_detection/sbm_wrapper.py`

- **`sbm_fit()`**: Main entry point supporting:
  - Algorithm selection: `"sbm"` or `"dc_sbm"`
  - Multilayer modes: `"independent"`, `"shared_blocks"`, `"shared_affinity"`, `"coupled"`
  - Model selection: Automatic K selection via `B_min` and `B_max`
  - UQ integration: Built-in uncertainty quantification
  - Mixed membership: `mixed_membership=True` for soft assignments

### 4. AutoCommunity Integration ✅
- Registered SBM variants in `capabilities.py`:
  - `sbm_fit`
  - `fit_multilayer_sbm`
- Added parameter grids in `community_registry.py`:
  - `n_blocks`: [2, 3, 4, 5] (default) or [3] (fast)
  - `B_min`, `B_max`: For model selection
  - `mode`: ["shared_blocks", "coupled"] (default) or ["shared_blocks"] (fast)
- SBM now auto-discoverable by `auto_select_community()`

### 5. Tests ✅
- **`test_sbm_mmsbm.py`** (9 tests): Mixed-membership SBM
- **`test_sbm_multilayer_coupled.py`** (8 tests): Coupled multilayer mode
- **`test_sbm_uq.py`** (11 tests): UQ functions

Total: **28 comprehensive tests**

### 6. DSL Zoo Examples ✅
Created 6 examples demonstrating all features:

- **36_sbm_basic.py**: Basic SBM with fixed K
- **37_sbm_degree_corrected.py**: DC-SBM for heterogeneous networks
- **38_sbm_mixed_membership.py**: MMSBM with soft assignments
- **39_sbm_multilayer_shared.py**: Multilayer with shared memberships
- **40_sbm_multilayer_coupled.py**: Coupled mode demonstration
- **41_autocommunity_with_sbm.py**: AutoCommunity integration

All examples are complete, runnable, and under 100 lines.

## Key Design Decisions

### 1. Native Implementation
- **Pure Python/NumPy/SciPy** only
- No external dependencies (no graph-tool, igraph, etc.)
- Variational inference with mean-field approximation

### 2. Deterministic UQ
- Uses `numpy.random.Generator(PCG64(seed))` for reproducibility
- `SeedSequence.spawn()` for child seed generation
- Same seed → identical outputs across runs

### 3. Coupled Multilayer Mode
- Interpolates between independent and shared B matrices
- `coupling_strength ∈ [0, 1]`:
  - `0`: Independent (no coupling)
  - `1`: Full coupling (identical B matrices)
- Layer-count independent behavior

### 4. API Compatibility
- Returns partition dicts: `{(node, layer): community_id}`
- Compatible with existing py3plex conventions
- Works with `AutoCommunity` framework

## Usage Examples

### Basic SBM
```python
from py3plex.algorithms.community_detection import sbm_fit

partition = sbm_fit(network, n_blocks=3, algorithm="dc_sbm", seed=42)
```

### Mixed-Membership SBM
```python
from py3plex.algorithms.sbm import mmsbm_fit

model = mmsbm_fit(network, n_blocks=3)
soft_memberships = model.memberships_  # (n_nodes x K)
```

### Coupled Multilayer
```python
partition = sbm_fit(
    network,
    n_blocks=3,
    mode="coupled",
    algorithm="dc_sbm"
)
```

### With UQ
```python
partition, model = sbm_fit(
    network,
    n_blocks=3,
    uq=True,
    uq_n_samples=50,
    return_model=True,
    seed=42
)
stability = model.uq_result_['node_stability']
```

### AutoCommunity
```python
from py3plex.algorithms.community_detection import auto_select_community

result = auto_select_community(
    network,
    mode="pareto",
    fast=True,
    seed=42
)
# SBM variants automatically included as candidates
```

## Code Review Improvements

Addressed all review feedback:
1. ✅ Fixed coupling formula for layer-count independence
2. ✅ Updated tests to use modern `numpy.random.default_rng()`
3. ✅ Documented UQ limitation with mixed_membership mode
4. ✅ Added TODO for soft membership alignment in UQ

## Files Modified/Created

### New Files (7)
- `py3plex/algorithms/sbm/uq.py`
- `py3plex/algorithms/community_detection/sbm_wrapper.py`
- `tests/algorithms/sbm/test_sbm_mmsbm.py`
- `tests/algorithms/sbm/test_sbm_multilayer_coupled.py`
- `tests/algorithms/sbm/test_sbm_uq.py`
- `examples/dsl_zoo/36_sbm_basic.py` through `41_autocommunity_with_sbm.py` (6 files)

### Modified Files (6)
- `py3plex/algorithms/sbm/__init__.py`
- `py3plex/algorithms/sbm/inference_vi.py`
- `py3plex/algorithms/community_detection/__init__.py`
- `py3plex/selection/capabilities.py`
- `py3plex/selection/community_registry.py`

## Testing Status

All components are implemented and integrated. Tests verify:
- Deterministic behavior (same seed → same output)
- Soft membership normalization (sum to 1)
- Label alignment correctness
- Coupled mode convergence
- UQ stability metrics
- AutoCommunity candidate registration

## Future Enhancements (Optional)

1. **DSL v2 Direct Integration**: Add `Q.communities(algorithm="sbm")` builder support
2. **Soft Membership Alignment**: Align soft memberships in UQ (currently TODO)
3. **Mixed Membership UQ**: Extend UQ support to MMSBM
4. **Interlayer Edges**: Support interlayer connections (currently restricted to "none")
5. **Parallel Inference**: Parallelize E-step and M-step computations

## Conclusion

All requirements from the GitHub issue have been met:
- ✅ MMSBM variant
- ✅ Coupled multilayer mode
- ✅ Unified API
- ✅ UQ with label alignment
- ✅ Deterministic reproducibility
- ✅ AutoCommunity integration
- ✅ Comprehensive tests
- ✅ DSL zoo examples

The implementation is fully native, deterministic, and production-ready.
