===============================================
How-To: Uncertainty-Aware Network Analysis
===============================================

This guide demonstrates how to compute network statistics with uncertainty estimates using py3plex's uncertainty-aware DSL.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
========

py3plex provides first-class support for uncertainty quantification in network analysis. Every graph statistic can optionally carry uncertainty information including:

- **Confidence intervals** (via bootstrap or perturbation)
- **Standard errors** (empirical across replicates)
- **Z-scores and p-values** (via null models)
- **Replication metadata** (number of replicates, method identifiers)

This makes it easy to assess the robustness of your network findings and perform statistical hypothesis testing.

Basic Usage
===========

What ``uncertainty=True`` returns
---------------------------------

When uncertainty is enabled, each metric value becomes a dictionary with common keys:

- ``mean``: Point estimate computed on the observed network
- ``std``: Standard deviation across replicates (bootstrap / perturbation) or across null draws (null model)
- ``quantiles``: Empirical confidence interval bounds keyed by probabilities, e.g. ``quantiles[0.025]``
- ``n_boot`` or ``n_null``: Number of bootstrap or null-model replicates used
- ``method``: Estimation method that produced the entry (e.g., ``"bootstrap"`` or ``"null_model"``)

This structure is consistent across bootstrap, null-model, perturbation, and seed-based methods.

When ``uncertainty=False``, metrics are returned as plain scalars or arrays instead of dictionaries.

Computing Metrics with Uncertainty
-----------------------------------

Use the ``uncertainty=True`` parameter in ``compute()`` to enable uncertainty estimation:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import Q
    
    # Create a network
    net = multinet.multi_layer_network(directed=False)
    net.add_edges([
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
        ["c", "L0", "a", "L0", 1.0],
    ], input_type="list")
    
    # Compute degree with uncertainty
    result = (
        Q.nodes()
        .compute("degree", uncertainty=True, n_boot=100, ci=0.95)
        .execute(net)
    )
    
    # Access results
    df = result.to_pandas()
    print(df["degree"])

Uncertainty Estimation Methods
===============================

Bootstrap Method
----------------

Bootstrap resampling provides confidence intervals by resampling network units (edges, nodes, or layers) with replacement.

**Syntax:**

.. code-block:: python

    result = (
        Q.nodes()
        .compute(
            "betweenness_centrality",
            uncertainty=True,
            method="bootstrap",
            n_boot=500,
            ci=0.95,
            bootstrap_unit="edges",      # or "nodes", "layers"
            bootstrap_mode="resample",   # or "permute"
            random_state=42
        )
        .execute(net)
    )

**Parameters:**

- ``method="bootstrap"``: Use bootstrap resampling
- ``n_boot``: Number of bootstrap replicates (default: 50)
- ``ci``: Confidence interval level, e.g., 0.95 for 95% CI (default: 0.95); intervals use percentile bounds from the bootstrap draws
- ``bootstrap_unit``: What to resample - ``"edges"``, ``"nodes"``, or ``"layers"`` (default: ``"edges"``); resampling a unit rebuilds an induced graph from that sample
- ``bootstrap_mode``: Resampling mode - ``"resample"`` (sample with replacement) or ``"permute"`` (shuffle labels without replacement to break associations) (default: ``"resample"``)
- ``random_state``: Random seed for reproducibility (optional)

**Example: Finding Robust Hubs**

.. code-block:: python

    # Find high-degree nodes with narrow confidence intervals
    robust_hubs = (
        Q.nodes()
        .compute(
            "degree", "betweenness_centrality",
            uncertainty=True,
            method="bootstrap",
            n_boot=300,
            bootstrap_unit="edges"
        )
        .order_by("-betweenness_centrality")
        .limit(10)
        .execute(net)
    )
    
    # Display results with uncertainty
    df = robust_hubs.to_pandas()
    for idx, row in df.iterrows():
        node_id = row['id']
        bc = row['betweenness_centrality']
        
        if isinstance(bc, dict):
            mean = bc['mean']
            std = bc['std']
            ci_low = bc['quantiles'][0.025]
            ci_high = bc['quantiles'][0.975]
            print(f"{node_id}: {mean:.4f} ± {std:.4f}, CI=[{ci_low:.4f}, {ci_high:.4f}]")

Null Model Method
-----------------

Null models test statistical significance by comparing observed values to randomized networks that preserve certain properties.

**Syntax:**

.. code-block:: python

    result = (
        Q.nodes()
        .compute(
            "degree",
            uncertainty=True,
            method="null_model",
            n_null=200,
            null_model="degree_preserving",  # or "erdos_renyi", "configuration"
            random_state=42
        )
        .execute(net)
    )

**Parameters:**

- ``method="null_model"``: Use null model hypothesis testing
- ``n_null``: Number of null model replicates (default: 200)
- ``null_model``: Null model type (default: ``"degree_preserving"``)
  
  - ``"degree_preserving"``: Rewire edges while preserving degree sequence (keeps degree histogram fixed)
  - ``"erdos_renyi"``: Random graph with the same density (destroys degree sequence)
  - ``"configuration"``: Configuration model matching degree distribution (allows multi-edges/self-loops depending on implementation)

- ``random_state``: Random seed for reproducibility (optional)

**Output Format:**

When ``method="null_model"``, metric dictionaries contain:

- ``mean``: Observed value on the input network
- ``mean_null``: Mean value from null models
- ``std``: Standard deviation of the null distribution
- ``zscore``: ``(observed - mean_null) / std`` (defined when ``std > 0``; undefined if null distribution is degenerate)
- ``pvalue``: Two-tailed p-value under the null distribution
- ``n_null``: Number of null replicates
- ``method``: Null model type used

**Example: Detecting Significant Nodes**

.. code-block:: python

    # Find nodes with significantly high betweenness
    significant_nodes = (
        Q.nodes()
        .compute(
            "betweenness_centrality",
            uncertainty=True,
            method="null_model",
            n_null=500,
            null_model="degree_preserving"
        )
        .execute(net)
    )
    
    df = significant_nodes.to_pandas()
    for idx, row in df.iterrows():
        node_id = row['id']
        bc = row['betweenness_centrality']
        
        if isinstance(bc, dict):
            obs = bc['mean']
            zscore = bc['zscore']
            pvalue = bc['pvalue']
            
            if pvalue < 0.05:  # Significant at α = 0.05 (adjust for multiple tests as needed)
                print(f"{node_id}: observed={obs:.4f}, z={zscore:.2f}, p={pvalue:.4f} *")

Legacy Methods
--------------

py3plex also supports legacy uncertainty methods for backward compatibility; prefer ``bootstrap`` or ``null_model`` unless you need behavior preserved from earlier releases.

**Perturbation:**

.. code-block:: python

    result = (
        Q.nodes()
        .compute("degree", uncertainty=True, method="perturbation", n_samples=100)
        .execute(net)
    )

Randomly perturb edges (e.g., add/drop according to internal defaults) and recompute the metric.

**Seed (Monte Carlo):**

.. code-block:: python

    result = (
        Q.nodes()
        .compute("degree", uncertainty=True, method="seed", n_samples=100)
        .execute(net)
    )

Run multiple independent executions with different random seeds when the metric itself is stochastic.

Global Defaults
===============

Set global defaults for uncertainty parameters to avoid repeating them in every query. The ``enabled`` flag toggles whether uncertainty is applied automatically; otherwise you still opt-in per call with ``uncertainty=True``.

Setting Defaults
----------------

.. code-block:: python

    from py3plex.dsl import Q
    
    # Configure global defaults
    Q.uncertainty.defaults(
        enabled=False,              # Auto-enable uncertainty for all queries?
        method="bootstrap",         # Default method
        n_boot=200,                 # Bootstrap replicates
        ci=0.95,                    # Confidence level
        bootstrap_unit="edges",     # What to resample
        bootstrap_mode="resample",  # Resampling mode
        n_null=200,                 # Null model replicates
        null_model="degree_preserving",  # Null model type
        random_state=42             # For reproducibility
    )
    
    # Now queries use these defaults
    result = Q.nodes().compute("degree", uncertainty=True).execute(net)

Querying and Resetting Defaults
--------------------------------

.. code-block:: python

    # Get a single default value
    n_boot = Q.uncertainty.get("n_boot")
    
    # Get all defaults
    all_defaults = Q.uncertainty.get_all()
    print(all_defaults)
    
    # Reset to initial values
    Q.uncertainty.reset()

Overriding Defaults
--------------------

Explicit parameters in ``compute()`` override global defaults:

.. code-block:: python

    # Set defaults
    Q.uncertainty.defaults(n_boot=100, ci=0.95)
    
    # Override with explicit parameters
    result = (
        Q.nodes()
        .compute("degree", uncertainty=True, n_boot=500, ci=0.99)
        .execute(net)
    )

Advanced Usage
==============

Multiple Metrics with Uncertainty
----------------------------------

Compute uncertainty for multiple metrics simultaneously:

.. code-block:: python

    result = (
        Q.nodes()
        .compute(
            "degree",
            "betweenness_centrality",
            "clustering",
            uncertainty=True,
            method="bootstrap",
            n_boot=200
        )
        .execute(net)
    )
    
    df = result.to_pandas()
    print(df[["id", "degree", "betweenness_centrality", "clustering"]])

Chaining with Other DSL Operations
-----------------------------------

Uncertainty works seamlessly with other DSL operations:

**Filtering:**

.. code-block:: python

    # Compute with uncertainty, then filter
    result = (
        Q.nodes()
        .where(layer="social")
        .compute("degree", uncertainty=True, n_boot=100)
        .execute(net)
    )

**Ordering:**

.. code-block:: python

    # Order by mean betweenness
    top_nodes = (
        Q.nodes()
        .compute("betweenness_centrality", uncertainty=True, n_boot=100)
        .order_by("-betweenness_centrality")
        .limit(10)
        .execute(net)
    )

**Grouping:**

.. code-block:: python

    # Per-layer uncertainty
    per_layer = (
        Q.nodes()
        .per_layer()
        .compute("degree", uncertainty=True, n_boot=50)
        .top_k(5, "degree")
        .execute(net)
    )

Layer-Specific Bootstrap
-------------------------

Bootstrap by resampling layers to assess inter-layer robustness:

.. code-block:: python

    result = (
        Q.nodes()
        .compute(
            "degree",
            uncertainty=True,
            method="bootstrap",
            n_boot=100,
            bootstrap_unit="layers"  # Resample layers
        )
        .execute(net)
    )

Node-Level Bootstrap
--------------------

Bootstrap by resampling nodes (useful for induced subgraph analysis):

.. code-block:: python

    result = (
        Q.nodes()
        .compute(
            "clustering",
            uncertainty=True,
            method="bootstrap",
            n_boot=100,
            bootstrap_unit="nodes"
        )
        .execute(net)
    )

Practical Examples
==================

Example 1: Robust Hub Detection
--------------------------------

Find hub nodes whose high centrality is robust to network perturbations:

.. code-block:: python

    # Compute betweenness with bootstrap CIs
    hubs = (
        Q.nodes()
        .compute(
            "betweenness_centrality",
            uncertainty=True,
            method="bootstrap",
            n_boot=500,
            ci=0.95
        )
        .order_by("-betweenness_centrality")
        .limit(20)
        .execute(net)
    )
    
    # Filter for robust hubs (narrow CI)
    df = hubs.to_pandas()
    for idx, row in df.iterrows():
        bc = row['betweenness_centrality']
        if isinstance(bc, dict):
            mean = bc['mean']
            ci_low = bc['quantiles'][0.025]
            ci_high = bc['quantiles'][0.975]
            ci_width = ci_high - ci_low
            rel_width = ci_width / mean if mean > 0 else float('inf')
            
            # Flag nodes with relative CI width < 20%
            if rel_width < 0.2:
                print(f"Robust hub: {row['id']}, BC={mean:.4f}, CI width={ci_width:.4f}")

Example 2: Statistical Significance Testing
--------------------------------------------

Test whether observed centrality values are significantly different from random:

.. code-block:: python

    # Compare against degree-preserving null model
    results = (
        Q.nodes()
        .compute(
            "betweenness_centrality",
            uncertainty=True,
            method="null_model",
            n_null=1000,
            null_model="degree_preserving"
        )
        .execute(net)
    )
    
    # Extract significant nodes
    df = results.to_pandas()
    significant = []
    
    for idx, row in df.iterrows():
        bc = row['betweenness_centrality']
        if isinstance(bc, dict):
            if bc['pvalue'] < 0.01:  # Bonferroni-corrected threshold (assumes independence)
                significant.append({
                    'node': row['id'],
                    'observed': bc['mean'],
                    'expected': bc['mean_null'],
                    'zscore': bc['zscore'],
                    'pvalue': bc['pvalue']
                })
    
    print(f"Found {len(significant)} statistically significant nodes")

Example 3: Comparing Layers
----------------------------

Use uncertainty to compare metric distributions across layers:

.. code-block:: python

    import numpy as np
    
    # Compute degree with uncertainty per layer
    layer_results = (
        Q.nodes()
        .per_layer()
        .compute("degree", uncertainty=True, method="bootstrap", n_boot=200)
        .execute(net)
    )
    
    # Compute summary statistics per layer
    df = layer_results.to_pandas()
    layer_summaries = {}
    
    for layer in df['layer'].unique():
        layer_df = df[df['layer'] == layer]
        degrees = []
        
        for _, row in layer_df.iterrows():
            deg = row['degree']
            if isinstance(deg, dict):
                degrees.append(deg['mean'])
        
        layer_summaries[layer] = {
            'mean_degree': np.mean(degrees),
            'std_degree': np.std(degrees)
        }
    
    for layer, stats in layer_summaries.items():
        print(f"{layer}: mean={stats['mean_degree']:.2f} ± {stats['std_degree']:.2f}")

Best Practices
==============

Choosing Replication Counts
----------------------------

- **Quick exploration**: 50-100 replicates
- **Publication quality**: 500-1000 replicates
- **Critical decisions**: 1000+ replicates

Increase the replication count until the reported intervals stop changing materially for your metric of interest.

Bootstrap Unit Selection
-------------------------

- Use ``"edges"`` for most centrality metrics (default)
- Use ``"nodes"`` for community detection or clustering
- Use ``"layers"`` to assess inter-layer robustness

Null Model Selection
---------------------

- ``"degree_preserving"``: Best for most centrality metrics (preserves local structure)
- ``"erdos_renyi"``: Tests against completely random baseline
- ``"configuration"``: Tests against random networks with same degree distribution

Reproducibility
---------------

Always set ``random_state`` for reproducible results:

.. code-block:: python

    result = Q.nodes().compute(
        "degree",
        uncertainty=True,
        n_boot=500,
        random_state=42  # For reproducibility
    ).execute(net)

Performance Tips
----------------

1. Start with small replication counts during development
2. Use ``bootstrap_unit="layers"`` for faster computation on large networks
3. Set global defaults to avoid repetition
4. Consider ``method="perturbation"`` for very large networks when full bootstrap runs are prohibitively slow (results are approximate)

API Reference
=============

compute() Parameters
--------------------

.. code-block:: python

    QueryBuilder.compute(
        *measures,                      # Metric names to compute
        alias=None,                     # Alias for single metric
        aliases=None,                   # Dict of metric aliases
        uncertainty=False,              # Enable uncertainty estimation
        method=None,                    # "bootstrap", "null_model", "perturbation", "seed"
        n_samples=None,                 # Generic replicate count (default: 50)
        n_boot=None,                    # Alias for n_samples when using bootstrap/perturbation/seed
        n_null=None,                    # Number of null replicates (default: 200)
        ci=None,                        # Confidence level (default: 0.95)
        bootstrap_unit=None,            # "edges", "nodes", "layers" (default: "edges")
        bootstrap_mode=None,            # "resample", "permute" (default: "resample")
        null_model=None,                # "degree_preserving", "erdos_renyi", "configuration"
        random_state=None               # Random seed for reproducibility
    )

Q.uncertainty Methods
---------------------

.. code-block:: python

    # Set global defaults
    Q.uncertainty.defaults(**kwargs)
    
    # Get a default value
    Q.uncertainty.get(key, default=None)
    
    # Get all defaults
    Q.uncertainty.get_all()
    
    # Reset to initial values
    Q.uncertainty.reset()

See Also
========

- :doc:`compute_statistics` - Computing network statistics
- :doc:`query_with_dsl` - DSL query guide
- :doc:`build_pipelines` - Building analysis pipelines

References
==========

- Efron, B., & Tibshirani, R. J. (1994). *An Introduction to the Bootstrap*. CRC press.
- Milo, R., et al. (2002). "Network motifs: simple building blocks of complex networks." *Science*, 298(5594), 824-827.

Distributional Community Detection
===================================

**New in v1.1**: Uncertainty-aware community detection.

Beyond metrics, py3plex now supports distributional community detection that quantifies uncertainty in community assignments.

Quick Example
-------------

.. code-block:: python

    from py3plex.algorithms.community_detection import multilayer_louvain_distribution
    
    # Run distributional community detection
    dist = multilayer_louvain_distribution(
        net,
        n_runs=100,
        resampling='perturbation',
        perturbation_params={'edge_drop_p': 0.05},
        seed=42
    )
    
    # Get consensus and confidence
    consensus = dist.consensus_partition()
    confidence = dist.node_confidence()
    
    # Filter stable core (high confidence nodes)
    stable_mask = confidence >= 0.8

See :doc:`../user_guide/community_detection` for complete documentation.
