===================================
Uncertainty-First Statistics
===================================

Overview
========

py3plex implements an **uncertainty-first statistics system** where every statistic is represented as ``(value + uncertainty + provenance)``. This design makes uncertainty a core part of statistics computation, not an afterthought.

Key Principles
--------------

1. **Every statistic is a StatValue**: No plain floats/ints escaping internal computation paths. Even deterministic values carry ``Delta(0)`` uncertainty.

2. **Uncertainty is first-class**: Uncertainty can be summarized, sampled, propagated through arithmetic, and used in queries.

3. **Backward compatible**: Existing code expecting floats works via ``float(statvalue)``.

4. **Registry discipline**: Statistics must have an uncertainty model to be registered.

5. **Reproducible**: Random processes (bootstrap/MC) support explicit seeds tracked in provenance.

Core Components
===============

StatValue
---------

``StatValue`` is the fundamental container for statistics:

.. code-block:: python

    from py3plex.stats import StatValue, Delta, Provenance
    
    # Create a deterministic statistic
    sv = StatValue(
        value=0.42,
        uncertainty=Delta(0.0),
        provenance=Provenance("degree", "delta", {})
    )
    
    # Access value
    print(float(sv))  # 0.42
    
    # Query uncertainty
    print(sv.std())  # 0.0
    print(sv.ci(0.95))  # (0.42, 0.42)
    print(sv.robustness())  # 1.0

**Key Methods:**

- ``float(sv)``: Convert to point estimate (backward compatibility)
- ``sv.mean()``: Alias for value
- ``sv.std()``: Standard deviation
- ``sv.ci(level=0.95)``: Confidence interval
- ``sv.robustness()``: Robustness score in [0, 1]
- ``sv.to_json_dict()``: Serialize to JSON

Uncertainty Models
------------------

Five concrete uncertainty models are provided:

Delta
~~~~~

Deterministic or known-precision uncertainty.

.. code-block:: python

    from py3plex.stats import Delta
    
    # Perfect certainty
    d = Delta(0.0)
    
    # Small known error
    d = Delta(0.01)

**Properties:**

- ``std()``: Returns sigma
- ``ci(level)``: Returns symmetric interval based on sigma
- ``sample(n, seed)``: Returns constant samples
- Propagation: Analytic error propagation when both are Delta

Gaussian
~~~~~~~~

Normal distribution uncertainty.

.. code-block:: python

    from py3plex.stats import Gaussian
    
    g = Gaussian(mean=0.0, std_dev=0.1)
    
    # Exact CI computation
    low, high = g.ci(0.95)  # ≈ (-0.196, 0.196)

**Properties:**

- ``std()``: Returns std_dev
- ``ci(level)``: Exact Gaussian CI using z-scores
- ``sample(n, seed)``: Generates Gaussian samples
- Propagation: Analytic for addition/subtraction, Monte Carlo for complex ops

Bootstrap
~~~~~~~~~

Empirical uncertainty from bootstrap resampling.

.. code-block:: python

    from py3plex.stats import Bootstrap
    import numpy as np
    
    # Store bootstrap samples (relative to point estimate)
    samples = np.array([0.1, -0.05, 0.15, 0.0, 0.08])
    b = Bootstrap(samples)
    
    # Compute CI from percentiles
    low, high = b.ci(0.95)

**Properties:**

- ``std()``: Sample standard deviation
- ``ci(level)``: Percentile-based CI
- ``sample(n, seed)``: Resample from stored samples
- Propagation: Always Monte Carlo
- Serialization: Stores summary (n, std, CI) not full samples

Empirical
~~~~~~~~~

Similar to Bootstrap but conceptually for any empirical distribution.

.. code-block:: python

    from py3plex.stats import Empirical
    
    samples = np.array([0.1, 0.2, 0.15, 0.18, 0.12])
    e = Empirical(samples)

**Properties:**

- Same as Bootstrap
- Conceptually separate for clarity

Interval
~~~~~~~~

Interval-based uncertainty without assuming distribution.

.. code-block:: python

    from py3plex.stats import Interval
    
    i = Interval(-0.1, 0.15)
    
    # Uniform sampling by default
    samples = i.sample(100, seed=42)

**Properties:**

- ``std()``: Estimates std assuming uniform distribution: ``(high - low) / sqrt(12)``
- ``ci(level)``: Returns the interval bounds
- ``sample(n, seed)``: Uniform sampling
- Propagation: Monte Carlo

Provenance
----------

Tracks how a statistic was computed:

.. code-block:: python

    from py3plex.stats import Provenance
    
    prov = Provenance(
        algorithm="brandes",
        uncertainty_method="bootstrap",
        parameters={"n_samples": 100},
        seed=42,
        timestamp="2024-12-12T17:00:00",
        library_version="1.0.0"
    )
    
    # Serialize
    json_dict = prov.to_json_dict()

**Fields:**

- ``algorithm``: Algorithm name (e.g., "degree", "betweenness")
- ``uncertainty_method``: Uncertainty method (e.g., "delta", "bootstrap")
- ``parameters``: Dict of parameters
- ``seed``: Random seed (optional)
- ``timestamp``: Computation time (optional)
- ``library_version``: Version string (optional)

Statistics Registry
===================

The ``StatisticsRegistry`` enforces that every registered statistic has an uncertainty model.

Registration
------------

.. code-block:: python

    from py3plex.stats import StatisticSpec, register_statistic, Delta
    
    def compute_degree(network, node):
        return network.core_network.degree(node)
    
    def degree_uncertainty(network, node, **kwargs):
        return Delta(0.0)  # Deterministic
    
    spec = StatisticSpec(
        name="degree",
        estimator=compute_degree,
        uncertainty_model=degree_uncertainty,
        assumptions=["deterministic"],
        supports={"directed": True, "weighted": True}
    )
    
    register_statistic(spec)

**Note:** Registration fails if ``uncertainty_model`` is missing.

Usage
-----

.. code-block:: python

    from py3plex.stats import compute_statistic
    
    # Compute with uncertainty
    result = compute_statistic("degree", network, node, with_uncertainty=True)
    # Returns StatValue
    
    # Compute without uncertainty (raw value)
    value = compute_statistic("degree", network, node, with_uncertainty=False)

Arithmetic with Uncertainty
============================

StatValue supports arithmetic operations with automatic uncertainty propagation.

Basic Operations
----------------

.. code-block:: python

    from py3plex.stats import StatValue, Gaussian, Provenance
    
    sv1 = StatValue(1.0, Gaussian(0.0, 0.1), Provenance("a", "gaussian", {}))
    sv2 = StatValue(2.0, Gaussian(0.0, 0.15), Provenance("b", "gaussian", {}))
    
    # Addition
    result = sv1 + sv2
    print(float(result))  # 3.0
    print(result.std())  # ~0.180 (sqrt(0.1² + 0.15²))
    
    # Subtraction
    result = sv1 - sv2
    
    # Multiplication
    result = sv1 * sv2
    
    # Division
    result = sv1 / sv2
    
    # Power
    result = sv1 ** 2
    
    # Negation
    result = -sv1

Scalar Operations
-----------------

StatValue supports operations with scalars:

.. code-block:: python

    sv = StatValue(2.0, Gaussian(0.0, 0.1), Provenance("a", "gaussian", {}))
    
    # Scalar addition
    result = sv + 3  # 5.0 (uncertainty unchanged)
    
    # Scalar multiplication
    result = sv * 2  # 4.0 (uncertainty scaled)
    
    # Scalar division
    result = sv / 2  # 1.0 (uncertainty scaled)

Propagation Rules
-----------------

1. **Delta + Delta**: Analytic error propagation (``σ_sum = sqrt(σ1² + σ2²)``)
2. **Gaussian + Gaussian**: Exact propagation for addition/subtraction
3. **Complex operations**: Monte Carlo propagation (4096 samples by default)
4. **Scalar operations**: Direct computation, uncertainty scaled appropriately

Filtering and Queries
======================

Statistics with uncertainty can be filtered using selectors:

Selector Syntax
---------------

Format: ``attribute__component__operator=value``

**Components:**

- ``mean``: Point estimate (default if omitted)
- ``std``: Standard deviation
- ``ci95__width``: Width of 95% CI
- ``robustness``: Robustness score

**Operators:**

- ``gt``: Greater than
- ``gte``: Greater than or equal
- ``lt``: Less than
- ``lte``: Less than or equal
- ``eq``: Equal
- ``ne``: Not equal

Examples
--------

.. code-block:: python

    # Filter by mean value
    result = Q.nodes().where(degree__mean__gt=3).execute(network)
    
    # Filter by uncertainty
    result = Q.nodes().where(betweenness__std__lt=0.05).execute(network)
    
    # Filter by CI width
    result = Q.nodes().where(degree__ci95__width__lt=0.1).execute(network)
    
    # Filter by robustness
    result = Q.nodes().where(centrality__robustness__gt=0.9).execute(network)

Serialization
=============

StatValue and Uncertainty models support JSON serialization.

StatValue Serialization
-----------------------

.. code-block:: python

    sv = StatValue(
        value=0.42,
        uncertainty=Gaussian(0.0, 0.05),
        provenance=Provenance("betweenness", "analytic", {})
    )
    
    json_dict = sv.to_json_dict()
    # {
    #   "value": 0.42,
    #   "uncertainty": {
    #     "type": "gaussian",
    #     "mean": 0.0,
    #     "std": 0.05
    #   },
    #   "provenance": {
    #     "algorithm": "betweenness",
    #     "uncertainty_method": "analytic",
    #     "params": {}
    #   }
    # }

DataFrame Export
----------------

QueryResult can export to pandas with uncertainty columns:

.. code-block:: python

    result = Q.nodes().compute("betweenness").execute(network)
    
    df = result.to_pandas()
    # Columns: id, betweenness.value, betweenness.std, 
    #          betweenness.ci_low, betweenness.ci_high,
    #          betweenness.uncertainty_type

Best Practices
==============

1. **Always use StatValue internally**: Even for deterministic stats, use ``Delta(0)``
2. **Provide uncertainty models**: Every registered statistic must have one
3. **Use seeds for reproducibility**: Pass explicit seeds to bootstrap/MC operations
4. **Choose appropriate models**:
   
   - Deterministic → ``Delta(0)``
   - Known distribution → ``Gaussian``
   - Empirical estimation → ``Bootstrap`` or ``Empirical``
   - No distribution assumption → ``Interval``

5. **Check robustness**: Use ``sv.robustness()`` to assess reliability
6. **Export uncertainty**: Include uncertainty columns in exports for downstream analysis

Examples
========

See:

- ``examples/network_analysis/example_stats_degree_delta.py``
- ``examples/network_analysis/example_stats_betweenness_bootstrap.py``

API Reference
=============

StatValue
---------

.. code-block:: python

    class StatValue:
        """Statistical value with uncertainty and provenance."""
        
        value: float | int | ndarray
        uncertainty: Uncertainty
        provenance: Provenance
        
        def __float__(self) -> float: ...
        def mean(self) -> float: ...
        def std(self) -> float: ...
        def ci(self, level: float = 0.95) -> tuple[float, float]: ...
        def robustness(self) -> float: ...
        def to_json_dict(self) -> dict: ...

Uncertainty Models
------------------

.. code-block:: python

    class Uncertainty(ABC):
        def summary(self, level: float = 0.95) -> dict: ...
        def sample(self, n: int, *, seed: int | None = None) -> ndarray: ...
        def ci(self, level: float = 0.95) -> tuple[float, float]: ...
        def std(self) -> float | None: ...
        def propagate(self, op: str, other: Uncertainty | None, *, seed: int | None = None) -> Uncertainty: ...
        def to_json_dict(self) -> dict: ...
    
    class Delta(Uncertainty):
        sigma: float = 0.0
    
    class Gaussian(Uncertainty):
        mean: float
        std_dev: float
    
    class Bootstrap(Uncertainty):
        samples: ndarray
    
    class Empirical(Uncertainty):
        samples: ndarray
    
    class Interval(Uncertainty):
        low: float
        high: float

Provenance
----------

.. code-block:: python

    @dataclass(frozen=True)
    class Provenance:
        algorithm: str
        uncertainty_method: str
        parameters: dict = field(default_factory=dict)
        seed: int | None = None
        timestamp: str | None = None
        library_version: str | None = None
        
        def to_json_dict(self) -> dict: ...
        @classmethod
        def from_json_dict(cls, data: dict) -> Provenance: ...

Registry
--------

.. code-block:: python

    @dataclass(frozen=True)
    class StatisticSpec:
        name: str
        estimator: Callable
        uncertainty_model: Callable  # Required
        assumptions: list[str] = field(default_factory=list)
        supports: dict = field(default_factory=dict)
    
    def register_statistic(spec: StatisticSpec, force: bool = False) -> None: ...
    def get_statistic(name: str) -> StatisticSpec: ...
    def list_statistics() -> list[str]: ...
    def compute_statistic(name: str, *args, with_uncertainty: bool = True, **kwargs) -> Any: ...
