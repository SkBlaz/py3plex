Statistical Comparison Framework
==================================

Overview
--------

The ``stats_comparison`` module provides a comprehensive framework for performing statistical comparisons between multilayer networks. This enables quantification of structural or topological differences across network ensembles or experimental conditions.

Features
--------

- **Pairwise and Multi-group Comparisons**: Compare 2 or more multilayer networks
- **Multiple Statistical Tests**:
  
  - Parametric: t-test, ANOVA
  - Non-parametric: Mann-Whitney U, Kruskal-Wallis
  - Permutation-based: Empirical null hypothesis testing

- **Effect Size Estimation**: Cohen's d, eta-squared
- **Multiple Comparison Correction**: Bonferroni, Holm-Bonferroni, FDR (Benjamini-Hochberg)
- **Bootstrap Confidence Intervals**: Estimate metric uncertainty
- **Comprehensive Metrics**: Density, degree, clustering, node activity, coupling strength, entropy

Installation
------------

The module is part of py3plex. Ensure you have the required dependencies:

.. code-block:: bash

    pip install numpy scipy pandas networkx

Quick Start
-----------

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics.stats_comparison import compare_multilayer_networks

    # Create networks
    net1 = multinet.multi_layer_network(directed=False)
    net1.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
        ['C', 'L1', 'A', 'L1', 1]
    ], input_type='list')

    net2 = multinet.multi_layer_network(directed=False)
    net2.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1]
    ], input_type='list')

    # Compare networks
    results = compare_multilayer_networks(
        [net1, net2],
        metrics=['density', 'average_degree'],
        test='permutation',
        n_permutations=1000,
        correction='fdr_bh',
        alpha=0.05
    )

    print(results)

**Expected Output (pandas DataFrame):**

.. code-block:: text

       metric layer  statistic   p_value  adjusted_p_value  effect_size  significant  mean_group_0  mean_group_1
    0  density    L1      0.250     0.132             0.132        0.500        False         1.000         0.667
    1  average_degree  L1  0.667     0.215             0.215        0.816        False         2.000         1.333

API Reference
-------------

compare_multilayer_networks()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Main function for comparing multilayer networks.

**Parameters:**

- ``networks`` (List[MultilayerNetwork]): List of networks to compare (minimum 2)
- ``metrics`` (List[str], optional): Metrics to compute. Options:
  
  - ``'density'``: Layer density
  - ``'average_degree'``: Mean node degree
  - ``'clustering'``: Clustering coefficient
  - ``'node_activity'``: Node activity across layers
  - ``'coupling_strength'``: Inter-layer coupling
  - ``'entropy'``: Entropy of multiplexity
  - Default: ``['average_degree', 'density', 'clustering']``

- ``test`` (str, optional): Statistical test type. Options:
  
  - ``'permutation'``: Permutation test (default)
  - ``'t-test'``: Student's t-test (2 groups)
  - ``'mann-whitney'``: Mann-Whitney U test (2 groups)
  - ``'anova'``: One-way ANOVA (2+ groups)
  - ``'kruskal'``: Kruskal-Wallis H test (2+ groups)

- ``n_permutations`` (int, optional): Number of permutations (default: 1000)
- ``alpha`` (float, optional): Significance level (default: 0.05)
- ``correction`` (str, optional): Multiple comparison correction. Options:
  
  - ``'bonferroni'``: Bonferroni correction
  - ``'holm'``: Holm-Bonferroni correction
  - ``'fdr_bh'``: Benjamini-Hochberg FDR (default)
  - ``None``: No correction

- ``node_mapping`` (Dict, optional): Node correspondence mapping across networks
- ``layer_scope`` (str, optional): Layer scope (``'intralayer'``, ``'interlayer'``, or ``'both'``)
- ``custom_metrics`` (Dict[str, Callable], optional): Custom metric functions

**Returns:**

pandas.DataFrame with columns:

- ``metric``: Metric name
- ``layer``: Layer identifier or 'global'
- ``statistic``: Test statistic value
- ``p_value``: Raw p-value
- ``adjusted_p_value``: Corrected p-value
- ``effect_size``: Effect size (Cohen's d or similar)
- ``significant``: Boolean indicating significance
- ``mean_group_0``, ``mean_group_1``, ...: Mean values per group

bootstrap_confidence_interval()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compute bootstrap confidence intervals for network metrics.

**Parameters:**

- ``networks`` (List[MultilayerNetwork]): List of networks
- ``metric_func`` (Callable): Function mapping network to scalar metric
- ``n_bootstrap`` (int, optional): Number of bootstrap samples (default: 1000)
- ``confidence_level`` (float, optional): Confidence level (default: 0.95)

**Returns:**

Dictionary mapping group indices to (lower, upper) CI bounds.

Examples
--------

Basic Two-Network Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics.stats_comparison import compare_multilayer_networks

    # Create networks with different densities
    net1 = multinet.multi_layer_network(directed=False)
    net1.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
        ['C', 'L1', 'A', 'L1', 1],  # Triangle
        ['A', 'L2', 'B', 'L2', 1]
    ], input_type='list')

    net2 = multinet.multi_layer_network(directed=False)
    net2.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],  # Line
        ['A', 'L2', 'B', 'L2', 1]
    ], input_type='list')

    # Compare using permutation test
    results = compare_multilayer_networks(
        [net1, net2],
        metrics=['density', 'clustering'],
        test='permutation',
        n_permutations=10000
    )

    # Show significant differences
    significant = results[results['significant']]
    print(significant)

Multi-Group Comparison
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Compare three or more networks
    results = compare_multilayer_networks(
        [net1, net2, net3, net4],
        metrics=['density', 'average_degree'],
        test='kruskal',  # Non-parametric for multiple groups
        correction='holm'
    )

    # Filter by metric
    density_results = results[results['metric'] == 'density']
    print(density_results)

Bootstrap Confidence Intervals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import numpy as np
    from py3plex.algorithms.statistics.stats_comparison import bootstrap_confidence_interval

    def avg_clustering(network):
        """Compute average clustering coefficient."""
        from py3plex.algorithms.statistics import multilayer_statistics as mls
        clustering = mls.multilayer_clustering_coefficient(network)
        return np.mean(list(clustering.values()))

    # Get 95% CI for clustering
    ci = bootstrap_confidence_interval(
        [net1, net2],
        avg_clustering,
        n_bootstrap=1000,
        confidence_level=0.95
    )

    for group, (lower, upper) in ci.items():
        print(f"{group}: [{lower:.4f}, {upper:.4f}]")

Best Practices
--------------

Choosing Statistical Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Sample Size < 30**: Use permutation or non-parametric tests
2. **Normal Distribution**: Parametric tests (t-test, ANOVA) have more power
3. **Two Groups**: t-test (parametric) or Mann-Whitney (non-parametric)
4. **Multiple Groups**: ANOVA (parametric) or Kruskal-Wallis (non-parametric)
5. **Unknown Distribution**: Permutation test (most general)

Multiple Comparison Correction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When testing multiple metrics or layers:

1. **Conservative**: Use Bonferroni (controls family-wise error rate)
2. **Less Conservative**: Use Holm-Bonferroni (sequential Bonferroni)
3. **Recommended**: Use FDR (Benjamini-Hochberg) - balances power and error control

Effect Sizes
~~~~~~~~~~~~

Always report effect sizes in addition to p-values:

- **Cohen's d**: d < 0.2 (small), 0.2-0.5 (medium), > 0.8 (large)
- **Eta-squared**: η² < 0.01 (small), 0.01-0.06 (medium), > 0.14 (large)

Use Cases
---------

Biological Networks
~~~~~~~~~~~~~~~~~~~

Compare disease vs. healthy protein interaction networks across multiple tissues:

.. code-block:: python

    results = compare_multilayer_networks(
        disease_networks + healthy_networks,
        metrics=['density', 'clustering', 'node_activity'],
        test='mann-whitney',
        correction='fdr_bh'
    )

Social Networks
~~~~~~~~~~~~~~~

Analyze structural differences in social networks before/after interventions:

.. code-block:: python

    results = compare_multilayer_networks(
        [pre_intervention_net, post_intervention_net],
        metrics=['average_degree', 'coupling_strength'],
        test='permutation',
        n_permutations=10000
    )

Temporal Networks
~~~~~~~~~~~~~~~~~

Compare network snapshots across time periods:

.. code-block:: python

    results = compare_multilayer_networks(
        [t1_network, t2_network, t3_network],
        metrics=['density', 'entropy'],
        test='kruskal'
    )

See Also
--------

- Example notebook: ``examples/statistical_comparison_example.ipynb``
- Example script: ``examples/compare_multilayer_networks_example.py``
- Module documentation: :mod:`py3plex.algorithms.statistics.stats_comparison`
- Related: :doc:`multilayer_centrality_matrix_functions`

References
----------

1. Kivelä, M., et al. (2014). "Multilayer networks." *Journal of Complex Networks*, 2(3), 203-271.
2. Good, P. (2013). "Permutation Tests: A Practical Guide to Resampling Methods for Testing Hypotheses."
3. Efron, B., & Tibshirani, R. J. (1994). "An Introduction to the Bootstrap."
4. Benjamini, Y., & Hochberg, Y. (1995). "Controlling the false discovery rate: a practical and powerful approach to multiple testing."
