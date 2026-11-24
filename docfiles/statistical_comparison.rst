Statistical Comparison Framework
==================================

Overview
--------

The ``stats_comparison`` module provides a comprehensive framework for performing statistical comparisons between multilayer networks. This enables quantification of structural or topological differences across network ensembles or experimental conditions.

Pass a list of cohorts (each a list of independent graphs) for inferential
comparisons. Each graph contributes one summary per metric and layer. A flat
list reports descriptive results by default. Set
``assume_exchangeable=True`` only when the study design supports treating
within-graph observations as exchangeable. Set ``seed`` for reproducible
permutations.

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

Quickstart
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

    results = compare_multilayer_networks(
        [net1, net2], metrics=["density", "average_degree"]
    )
    print(results[["metric", "layer", "mean_group_0", "mean_group_1"]])

For these networks, the triangle has density 1 and mean degree 2. The
path has density 2/3 and mean degree 4/3. The p-value columns are
missing for this descriptive comparison.

API Reference
-------------

compare_multilayer_networks()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Main function for comparing multilayer networks.

**Parameters:**

- ``networks`` (list): A flat list of at least two networks for descriptive comparisons, or a list of independent graph cohorts for inference
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
  - ``'t-test'``: Welch's t-test (2 groups)
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

- ``assume_exchangeable`` (bool, optional): Enables within-graph inference for flat lists (default: False)
- ``seed`` (int, optional): Random seed for permutation sampling
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

Compute percentile intervals conditional on the input graph's node set and
multiplex couplings. Each draw resamples the other edges with replacement.

**Parameters:**

- ``networks`` (List[MultilayerNetwork]): List of networks
- ``metric_func`` (Callable): Function mapping network to scalar metric
- ``n_bootstrap`` (int, optional): Number of bootstrap samples (default: 1000)
- ``confidence_level`` (float, optional): Confidence level (default: 0.95)
- ``seed`` (int, optional): Random seed for edge resampling

**Returns:**

Dictionary mapping keys such as ``group_0`` to (lower, upper) percentile bounds.

Examples
--------

Compare Independent Cohorts
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The three simulated cohorts below contain eight independent graphs each.
The test permutes cohort assignments at the graph level.

.. code-block:: python

    from py3plex.datasets import make_random_multiplex

    cohorts = [
        [
            make_random_multiplex(
                n_nodes=20, n_layers=2, p=probability,
                random_state=100 * group + replicate,
            )
            for replicate in range(8)
        ]
        for group, probability in enumerate((0.15, 0.25, 0.35))
    ]
    results = compare_multilayer_networks(
        cohorts, metrics=["density", "average_degree"],
        test="permutation", n_permutations=999, correction="holm", seed=42,
    )
    print(results[["metric", "layer", "p_value", "adjusted_p_value"]])

Bootstrap Confidence Intervals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.statistics.multilayer_statistics import layer_density
    from py3plex.algorithms.statistics.stats_comparison import bootstrap_confidence_interval

    intervals = bootstrap_confidence_interval(
        [net1, net2], lambda network: layer_density(network, "L1"),
        n_bootstrap=500, confidence_level=0.95, seed=42,
    )
    for graph, (lower, upper) in intervals.items():
        print(f"{graph}: [{lower:.4f}, {upper:.4f}]")

Best Practices
--------------

Choosing Statistical Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use independent graphs as replicates and check the assumptions for your
chosen test. Welch's t-test allows unequal group variances. Permutation
tests require exchangeable group assignments under the null. A descriptive
comparison is appropriate for a single network observed at several times.

Multiple Comparison Correction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When testing multiple metrics or layers:

1. **Conservative**: Use Bonferroni (controls family-wise error rate)
2. **Less Conservative**: Use Holm-Bonferroni (sequential Bonferroni)
3. **Recommended**: Use FDR (Benjamini-Hochberg) - balances power and error control

Effect Sizes
~~~~~~~~~~~~

The function reports Cohen's d for two groups and eta-squared for three or
more groups. Interpret the magnitude in the context of the metric and study.

Use Cases
---------

Biological Networks
~~~~~~~~~~~~~~~~~~~

Compare disease vs. healthy protein interaction networks across multiple tissues:

.. code-block:: python

    results = compare_multilayer_networks(
        [disease_networks, healthy_networks],
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
        metrics=['average_degree', 'coupling_strength']
    )

Temporal Networks
~~~~~~~~~~~~~~~~~

Compare network snapshots across time periods:

.. code-block:: python

    results = compare_multilayer_networks(
        [t1_network, t2_network, t3_network],
        metrics=['density', 'entropy']
    )

See Also
--------

- Example notebook: ``examples/pipelines/statistical_comparison_example.ipynb``
- Example script: ``examples/network_analysis/compare_multilayer_networks_example.py``
- Module documentation: :mod:`py3plex.algorithms.statistics.stats_comparison`
- Related: :doc:`multilayer_centrality_matrix_functions`

References
----------

1. Kivelä, M., et al. (2014). "Multilayer networks." *Journal of Complex Networks*, 2(3), 203-271.
2. Good, P. (2013). "Permutation Tests: A Practical Guide to Resampling Methods for Testing Hypotheses."
3. Efron, B., & Tibshirani, R. J. (1994). "An Introduction to the Bootstrap."
4. Benjamini, Y., & Hochberg, Y. (1995). "Controlling the false discovery rate: a practical and powerful approach to multiple testing."
