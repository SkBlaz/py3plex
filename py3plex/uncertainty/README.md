# First-Class Uncertainty in py3plex

This module implements first-class uncertainty support for network statistics in py3plex. The key innovation is treating uncertainty as "the way stats are represented" rather than an add-on feature.

## Core Concepts

### StatSeries: The Universal Statistic Type

Every statistic in py3plex can now return a `StatSeries` object that carries:

- **mean**: The point estimate (or single-run value)
- **std**: Standard deviation (None for deterministic)
- **quantiles**: Confidence intervals (e.g., 95% CI)
- **meta**: Algorithm parameters and run info

**Deterministic mode** (default):
```python
result = multilayer_pagerank(network)
result.is_deterministic  # True
result.std  # None
result.certainty  # 1.0
```

**Uncertainty mode** (explicit or via context):
```python
result = multilayer_pagerank(network, uncertainty=True, n_runs=50)
result.is_deterministic  # False
result.std  # array([0.01, 0.02, ...])
result.quantiles  # {0.025: [...], 0.975: [...]}
result.certainty  # 0.0
```

### Backward Compatibility

StatSeries implements `__array__()` for seamless numpy integration:

```python
result = multilayer_pagerank(network)
arr = np.array(result)  # Returns mean values
```

Dictionary-like access:
```python
node = result.index[0]
stats = result[node]  # {'mean': 0.25, 'std': 0.02, 'quantiles': {...}}
```

## Usage Patterns

### 1. Explicit Uncertainty Parameter

```python
from py3plex.algorithms.centrality_toolkit import multilayer_pagerank
from py3plex.uncertainty import ResamplingStrategy

# With uncertainty
result = multilayer_pagerank(
    network,
    uncertainty=True,
    n_runs=100,
    resampling=ResamplingStrategy.PERTURBATION,
    random_seed=42
)

print(f"Mean PageRank: {result.mean}")
print(f"Std deviation: {result.std}")
print(f"95% CI: [{result.quantiles[0.025]}, {result.quantiles[0.975]}]")
```

### 2. Global Context Manager

Enable uncertainty for an entire pipeline:

```python
from py3plex.uncertainty import uncertainty_enabled

with uncertainty_enabled(n_runs=50):
    # All stats computed in this block will have uncertainty
    pr = multilayer_pagerank(network)
    bc = multilayer_betweenness_centrality(network)
    # Both have uncertainty information
```

### 3. Resampling Strategies

#### SEED Strategy
Run algorithm multiple times with different random seeds:
```python
result = multilayer_pagerank(
    network,
    uncertainty=True,
    resampling=ResamplingStrategy.SEED,
    n_runs=100
)
```

#### PERTURBATION Strategy
Perturb network structure (drop edges/nodes) and recompute:
```python
result = multilayer_pagerank(
    network,
    uncertainty=True,
    resampling=ResamplingStrategy.PERTURBATION,
    n_runs=50
)
```

You can customize perturbations:
```python
from py3plex.uncertainty import estimate_uncertainty

def my_metric(net):
    return multilayer_pagerank(net)

result = estimate_uncertainty(
    network,
    my_metric,
    n_runs=50,
    resampling=ResamplingStrategy.PERTURBATION,
    perturbation_params={
        "edge_drop_p": 0.1,  # Drop 10% of edges
        "node_drop_p": 0.05  # Drop 5% of nodes
    }
)
```

## Supported Functions

### Centrality (Phase 3) 
- `multilayer_pagerank()` - Full support with uncertainty
- `multilayer_betweenness_centrality()` - Coming soon
- `multilayer_eigenvector_centrality()` - Coming soon
- `multiplex_degree_centrality()` - Coming soon

### Community Detection (Phase 4) 
- Louvain detection with `CommunityStats`
- Co-association matrices
- Stability indices

### Robustness (Future) 
- `robustness_centrality()` returning StatSeries
- Dynamic process simulations with uncertainty

## Type Reference

### StatSeries

```python
@dataclass
class StatSeries:
    index: List[Any]              # Node IDs, time points, etc.
    mean: np.ndarray              # (n,) mean values
    std: Optional[np.ndarray]     # (n,) std deviations or None
    quantiles: Optional[Dict[float, np.ndarray]]  # Percentiles
    meta: Dict[str, Any]          # Metadata
    
    @property
    def is_deterministic(self) -> bool: ...
    
    @property
    def certainty(self) -> float: ...
    
    def __array__(self) -> np.ndarray: ...  # Backward compat
    def __getitem__(self, key) -> Dict: ...  # Dict-like access
    def to_dict(self) -> Dict: ...           # Serialization
```

### StatMatrix

For adjacency matrices, co-association matrices, etc.:

```python
@dataclass
class StatMatrix:
    index: List[Any]              # Row/column labels
    mean: np.ndarray              # (n, n) mean matrix
    std: Optional[np.ndarray]     # (n, n) std matrix
    quantiles: Optional[Dict[float, np.ndarray]]
    meta: Dict[str, Any]
```

### CommunityStats

For community detection results:

```python
@dataclass
class CommunityStats:
    labels: Dict[Any, int]        # Node -> community ID
    modularity: Optional[float]   # Mean modularity
    modularity_std: Optional[float]
    coassoc: Optional[StatMatrix] # Co-association matrix
    stability: Optional[Dict[Any, float]]  # Per-node stability
    n_communities: int
    meta: Dict[str, Any]
```

### ResamplingStrategy

```python
class ResamplingStrategy(Enum):
    SEED = "seed"                 # Multiple random seeds
    BOOTSTRAP = "bootstrap"       # Bootstrap resampling
    JACKKNIFE = "jackknife"       # Leave-one-out
    PERTURBATION = "perturbation" # Network perturbations
```

## Design Rationale

### Why First-Class Uncertainty?

1. **No Bolt-On Feel**: Uncertainty is native, not an afterthought
2. **Consistent API**: All stats use the same abstraction
3. **Backward Compatible**: Existing code keeps working via `__array__`
4. **Composable**: Uncertainty propagates through derived metrics
5. **Context-Aware**: Global settings via context managers

### Why StatSeries over plain dicts?

- **Type Safety**: Clear structure with validation
- **Rich API**: Properties like `is_deterministic`, `certainty`
- **Interoperability**: Works with numpy, pandas, matplotlib
- **Metadata**: Store algorithm params, run info
- **Future-Proof**: Easy to add new fields (e.g., skewness)

## Examples

See `examples/network_analysis/example_first_class_uncertainty.py` for comprehensive examples including:

1. Deterministic computation
2. Uncertainty estimation
3. Context manager usage
4. Dictionary conversion
5. Comparing deterministic vs uncertain results

## Testing

Run the test suite:

```bash
pytest tests/test_uncertainty.py -v                  # Core types (25 tests)
pytest tests/test_centrality_uncertainty.py -v       # Centrality (11 tests)
pytest tests/test_centrality_robustness.py -v        # Robustness (20 tests)
```

## Future Work

### Phase 4: Community Detection
- Wrap Louvain/Leiden with `CommunityStats`
- Add co-association matrix computation
- Stability indices from multiple runs

### Phase 5: Uncertainty Propagation
Enable composing uncertain stats:

```python
def combined_score(centrality: StatSeries, activity: StatSeries) -> StatSeries:
    mean = centrality.mean * activity.mean
    
    if not centrality.is_deterministic and not activity.is_deterministic:
        # Error propagation for independent variables
        var = (centrality.mean * activity.std)**2 + (activity.mean * centrality.std)**2
        std = np.sqrt(var)
        return StatSeries(index=centrality.index, mean=mean, std=std)
    
    return StatSeries(index=centrality.index, mean=mean)
```

### Phase 6: DSL Integration

```sql
SELECT centrality("pagerank") WITH UNCERTAINTY
FROM layer "transport"
WHERE degree > 5
```

### Phase 7: Visualization

```python
import matplotlib.pyplot as plt

result = multilayer_pagerank(network, uncertainty=True, n_runs=50)

# Plot with error bars
plt.errorbar(
    range(len(result)),
    result.mean,
    yerr=result.std,
    fmt='o'
)

# Or with confidence bands
plt.fill_between(
    range(len(result)),
    result.quantiles[0.025],
    result.quantiles[0.975],
    alpha=0.3
)
plt.plot(result.mean, 'k-')
```

## API Reference

### Main Exports

```python
from py3plex.uncertainty import (
    # Types
    StatSeries,
    StatMatrix,
    CommunityStats,
    # Enums
    ResamplingStrategy,
    UncertaintyMode,
    UncertaintyConfig,
    # Functions
    estimate_uncertainty,
    get_uncertainty_config,
    set_uncertainty_config,
    uncertainty_enabled,
)
```

### Function Signatures

```python
def estimate_uncertainty(
    network: multi_layer_network,
    metric_fn: Callable,
    *,
    n_runs: Optional[int] = None,
    resampling: Optional[ResamplingStrategy] = None,
    random_seed: Optional[int] = None,
    perturbation_params: Optional[Dict] = None,
) -> Union[StatSeries, float]:
    """Estimate uncertainty for any network statistic."""

@contextmanager
def uncertainty_enabled(
    *,
    n_runs: Optional[int] = None,
    resampling: Optional[ResamplingStrategy] = None,
):
    """Context manager to enable uncertainty globally."""
```

## Contributing

When adding new statistics with uncertainty support:

1. Make metric function accept `uncertainty=False` parameter
2. Check context config: `cfg = get_uncertainty_config()`
3. Use `estimate_uncertainty()` helper if `uncertainty=True`
4. Wrap deterministic results in `StatSeries` for consistency
5. Add tests for both deterministic and uncertain modes
6. Update this README

## License

Same as py3plex (MIT)
