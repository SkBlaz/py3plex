# Dynamics Implementation Summary

## Overview

This implementation adds comprehensive multilayer dynamics functionality to py3plex, complementing the existing high-level DSL/builder API with traditional OOP-style classes for implementing custom dynamics on multilayer networks.

## What Was Added

### Core Abstractions (py3plex/dynamics/core.py)

1. **DynamicsProcess** - Base class for discrete-time dynamics
   - Synchronous updates
   - Flexible state representation
   - Reproducible via seeding
   - Callbacks support

2. **ContinuousTimeProcess** - Base class for continuous-time dynamics
   - Gillespie algorithm implementation
   - Event-based simulation
   - Proper time advancement

3. **TemporalGraph** - Wrapper for time-varying networks
   - Snapshot-based or function-based
   - Compatible with existing dynamics

4. **TemporalDynamicsProcess** - Base for temporal dynamics
   - Extends DynamicsProcess for temporal networks

### Discrete-Time Models (py3plex/dynamics/models.py)

1. **RandomWalkDynamics** - Single-walker random walk
   - Lazy probability support
   - Visit count tracking
   - Works with multilayer networks

2. **MultiRandomWalkDynamics** - Multiple walkers
   - Absorbing states
   - Hitting time statistics
   - Independent walker dynamics

3. **SISDynamics** - Susceptible-Infected-Susceptible epidemic
   - Python/NumPy/PyTorch backends
   - Prevalence tracking
   - Vectorized operations

4. **AdaptiveSISDynamics** - Co-evolutionary SIS
   - Edge rewiring
   - Edge type counting
   - Network structure evolution

5. **TemporalRandomWalk** - Walk on temporal networks
   - Time-varying edge constraints

### Compartmental Models (py3plex/dynamics/compartmental.py)

1. **CompartmentalDynamics** - Generic framework
   - Arbitrary compartments
   - Flexible transition rules
   - Compartment counting

2. **SIRDynamics** - Susceptible-Infected-Recovered
   - Absorbing recovered state
   - Standard epidemic model

3. **SEIRDynamics** - Susceptible-Exposed-Infected-Recovered
   - Exposed/latent period
   - Four-compartment model

4. **SISContinuousTime** - Continuous-time SIS
   - Gillespie algorithm
   - Event-driven simulation

### Config-Based Builder (py3plex/dynamics/config.py)

- **build_dynamics_from_config()** - Create dynamics from JSON/dict
- Simple DSL for transition rules
- Safe expression evaluation
- No code generation needed

### Utilities (py3plex/dynamics/_utils.py)

- iter_multilayer_nodes() - Iterate over nodes
- iter_multilayer_neighbors() - Iterate over neighbors
- get_adjacency_matrix() - Extract adjacency
- State conversion utilities
- Layer information extraction

## Testing

Added comprehensive test suite in `tests/test_dynamics_core.py`:

- 36 new tests covering all functionality
- All tests pass (100% success rate)
- Tests include:
  - Random walks (single and multi-walker)
  - Epidemic models (SIS, SIR, SEIR)
  - Continuous-time dynamics
  - Temporal networks
  - Config-based dynamics
  - Reproducibility verification
  - Backend consistency checks
  - Error handling

Total: 137 dynamics-related tests passing

## Examples

Added `examples/advanced/example_dynamics_core.py` with 8 complete examples:

1. Random walk on Karate Club network
2. Multiple walkers with absorbing states
3. SIS epidemic model
4. Adaptive SIS with edge rewiring
5. SIR compartmental model
6. Continuous-time SIS (Gillespie)
7. Temporal network dynamics
8. Config-based dynamics

All examples run successfully and demonstrate key features.

## Key Features

### Reproducibility
- Dedicated RNG per instance
- `set_seed()` method for re-seeding
- Consistent behavior across runs

### Performance
- Multiple backends (Python, NumPy, PyTorch)
- Vectorized operations where possible
- Efficient state management

### Flexibility
- Works with NetworkX and py3plex multilayer networks
- Extensible base classes
- Config-based specification option

### Integration
- Complements existing ProcessSpec system
- Reuses existing utilities
- Maintains backward compatibility

## Architecture Decisions

1. **Separate from ProcessSpec system**: The new classes provide an alternative, OOP-style interface rather than replacing the existing declarative system.

2. **Flexible state representation**: States can be dicts, arrays, or custom objects depending on the model.

3. **Backend abstraction**: SISDynamics demonstrates how to support multiple backends for performance.

4. **Minimal dependencies**: Core functionality requires only NumPy and NetworkX.

5. **Safety first**: Config parser uses restricted eval with whitelist validation.

## Files Modified/Added

### New Files
- py3plex/dynamics/core.py (550 lines)
- py3plex/dynamics/models.py (700 lines)
- py3plex/dynamics/compartmental.py (450 lines)
- py3plex/dynamics/config.py (350 lines)
- py3plex/dynamics/_utils.py (180 lines)
- tests/test_dynamics_core.py (620 lines)
- examples/advanced/example_dynamics_core.py (310 lines)

### Modified Files
- py3plex/dynamics/__init__.py (added exports)

Total: ~3,160 lines of new code

## Validation

- All 137 dynamics-related tests pass
- All existing tests still pass (backward compatible)
- CodeQL security scan: 0 alerts
- Code review completed with feedback addressed
- Examples run successfully

## Documentation

The implementation includes:
- Comprehensive docstrings (Google style)
- Type hints throughout
- Detailed examples
- This summary document

## Future Work

Potential extensions (not implemented in this PR):

1. More compartmental models (SIRS, SEIRD, etc.)
2. Network generation coupled with dynamics
3. Parallel simulation support
4. Additional backends (JAX, CuPy)
5. Visualization integration
6. Advanced statistics and analysis

## Conclusion

This implementation successfully extends py3plex with comprehensive dynamics functionality that:
- Provides users with flexible, Pythonic interfaces
- Maintains high performance through vectorization
- Ensures reproducibility for scientific computing
- Integrates cleanly with existing codebase
- Follows best practices for security and maintainability

The new dynamics core classes complement the existing high-level API, giving users the choice between declarative configuration and programmatic control.
