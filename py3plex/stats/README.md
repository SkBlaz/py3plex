# py3plex.stats: Uncertainty-First Statistics Module

This module implements an **uncertainty-first statistics system** where every statistic is represented as `(value + uncertainty + provenance)`.

## Quick Start

```python
from py3plex.stats import StatValue, Delta, Gaussian, Bootstrap, Provenance
import numpy as np

# Deterministic statistic
degree_stat = StatValue(
    value=5,
    uncertainty=Delta(0.0),  # Zero uncertainty
    provenance=Provenance("degree", "delta", {})
)

print(float(degree_stat))  # 5.0 - backward compatible
print(degree_stat.std())   # 0.0 - no uncertainty
print(degree_stat.robustness())  # 1.0 - perfectly robust

# Statistic with Gaussian uncertainty
bc_stat = StatValue(
    value=0.42,
    uncertainty=Gaussian(0.0, 0.05),  # std = 0.05
    provenance=Provenance("betweenness", "analytic", {})
)

print(bc_stat.ci(0.95))  # (0.324, 0.516) - 95% CI
print(bc_stat.robustness())  # ~0.893 - high robustness

# Statistic with Bootstrap uncertainty
samples = np.array([0.1, -0.05, 0.15, 0.0, 0.08])
boot_stat = StatValue(
    value=0.5,
    uncertainty=Bootstrap(samples),
    provenance=Provenance("pagerank", "bootstrap", {"n_boot": 100}, seed=42)
)

# Arithmetic with automatic uncertainty propagation
combined = degree_stat + bc_stat
print(combined.std())  # Propagated uncertainty
```

## Core Components

### StatValue

Container for `(value, uncertainty, provenance)`:

- **value**: Point estimate (float, int, or ndarray)
- **uncertainty**: Uncertainty model
- **provenance**: Computation metadata

**Methods:**
- `float(sv)`: Convert to float (backward compatibility)
- `sv.mean()`: Point estimate
- `sv.std()`: Standard deviation
- `sv.ci(level=0.95)`: Confidence interval
- `sv.robustness()`: Robustness score [0, 1]
- `sv.to_json_dict()`: Serialize

**Arithmetic:**
- Supports `+`, `-`, `*`, `/`, `**`, unary `-`
- Automatic uncertainty propagation
- Works with scalars and other StatValues

### Uncertainty Models

#### Delta
Deterministic or known-precision uncertainty.

```python
d = Delta(0.0)  # Perfect certainty
d = Delta(0.01)  # Small known error
```

#### Gaussian
Normal distribution uncertainty.

```python
g = Gaussian(mean=0.0, std_dev=0.1)
low, high = g.ci(0.95)  # Exact Gaussian CI
```

#### Bootstrap
Empirical uncertainty from bootstrap resampling.

```python
samples = np.array([...])  # Bootstrap samples
b = Bootstrap(samples)
low, high = b.ci(0.95)  # Percentile-based CI
```

#### Empirical
General empirical distribution (similar to Bootstrap).

```python
samples = np.array([...])
e = Empirical(samples)
```

#### Interval
Interval-based uncertainty without distribution assumption.

```python
i = Interval(-0.1, 0.15)
samples = i.sample(100)  # Uniform sampling
```

### Provenance

Tracks computation metadata:

```python
prov = Provenance(
    algorithm="brandes",
    uncertainty_method="bootstrap",
    parameters={"n_samples": 100},
    seed=42
)
```

### Statistics Registry

Enforces that every registered statistic has an uncertainty model:

```python
from py3plex.stats import StatisticSpec, register_statistic

def compute_degree(network, node):
    return network.core_network.degree(node)

def degree_uncertainty(network, node, **kwargs):
    return Delta(0.0)  # Deterministic

spec = StatisticSpec(
    name="degree",
    estimator=compute_degree,
    uncertainty_model=degree_uncertainty
)

register_statistic(spec)
```

## Key Features

 **Five uncertainty models**: Delta, Gaussian, Bootstrap, Empirical, Interval
 **Automatic propagation**: Arithmetic operations propagate uncertainty
 **Backward compatible**: `float(statvalue)` for existing code
 **Serializable**: JSON export for all types
 **Reproducible**: Seed tracking in provenance
 **Type-safe**: Frozen dataclasses prevent mutation
 **Tested**: 51 unit tests, 100% coverage of core functionality

## Examples

See:
- `examples/network_analysis/example_stats_degree_delta.py`
- `examples/network_analysis/example_stats_betweenness_bootstrap.py`

## Documentation

Complete reference: `docfiles/reference/uncertainty_first_statistics.rst`

## Design Philosophy

This module provides **lower-level primitives** for uncertainty handling. It complements the existing `py3plex.uncertainty` module (which provides `StatSeries`, `bootstrap_metric`, etc.) by offering:

1. **Per-value uncertainty**: StatValue wraps individual scalars
2. **Composable arithmetic**: Operators propagate uncertainty
3. **Multiple models**: Choice of Delta, Gaussian, Bootstrap, etc.
4. **Registry discipline**: Enforced uncertainty models

The existing `py3plex.uncertainty` module continues to work and is used by the DSL. Use `py3plex.stats` when you need:
- Fine-grained control over individual value uncertainties
- Arithmetic with uncertainty propagation
- Multiple uncertainty model types
- Registry-based statistic management

## Dependencies

- numpy (required)
- scipy (optional, for Gaussian CI computation)

No heavy dependencies added - only standard scientific Python stack.

## Testing

```bash
pytest tests/test_stats_core.py tests/test_stats_registry.py -v
```

All 51 tests pass.

## Future Enhancements

Potential additions (not yet implemented):
- Integration with DSL query filtering (`WHERE stat__std__lt=0.05`)
- QueryResult export with uncertainty columns
- Visualization with uncertainty (fade/errorbars/bands)
- Aggregation with uncertainty preservation
