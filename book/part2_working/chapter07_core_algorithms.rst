.. _algorithms-chapter:

Core Algorithms: What Is Estimated, What Is Approximated
=========================================================

This chapter organizes py3plex algorithm use around interpretation risk rather than interface breadth.

Native Multilayer Methods
-------------------------

These methods preserve layer semantics during estimation (for example, multilayer community workflows, layer-aware coverage logic, and multilayer-specific centrality variants).

* **Safe claim:** "This estimate is computed under an explicit multilayer representation."
* **Unsafe claim:** "Therefore it is automatically closer to domain truth."

Delegated Single-Layer Methods
------------------------------

Some workflows project or flatten to use mature single-layer backends.

* **Safe claim:** "This is a projection-based baseline for comparison."
* **Unsafe claim:** "This delegated result has the same semantics as native multilayer output."

Approximate Methods
-------------------

Approximation is a practical necessity for expensive measures on larger graphs.

* **Safe claim:** "Approximate ranking is acceptable for screening under stated error tolerance."
* **Unsafe claim:** "Small score gaps are interpretable as substantive differences without robustness checks."

Stochastic Methods
------------------

Stochasticity appears in community search, perturbation workflows, and simulation.

* **Safe claim:** "Result is one seeded draw (or one uncertainty summary) under a specified model."
* **Unsafe claim:** "Single seeded output is definitive without stability analysis."

Community Detection
-------------------

py3plex supports multilayer community workflows through methods such as Louvain/Leiden-style procedures and related wrappers.

Interpretive caution:

* Partition quality metrics are objective-specific.
* Comparable scores do not imply identical community semantics across methods.
* **Global partitions** optimize communities that can span layers; **per-layer partitions** optimize separate structures inside each layer and are better for layer-to-layer comparison.

Centrality
----------

Many centrality measures are available, but users must state:

* whether analysis is per-layer or global,
* whether values are exact or approximated,
* whether measures were computed on native multilayer structure or reduced projections.

Approximation is often suitable for ranking-oriented exploration on larger graphs, but claims about small score differences should be avoided unless validated; score gaps that look large in a plot can collapse under perturbation or alternative layer scopes.

Dynamics
--------

SIS/SIR-like models in py3plex are useful for scenario analysis under explicit assumptions.

Do not infer causal epidemiological truths from toy parameter sweeps. Dynamics outputs are model-conditional, not domain truth.
Also distinguish topology-driven scenarios (what structure permits) from domain-calibrated scenarios (what parameters and interventions are realistic); both are useful, but they support different claims.

Practical Pattern
-----------------

.. code-block:: python

    from py3plex.dsl import Q, L

    result = (
        Q.nodes()
         .from_layers(L['social'])
         .compute('degree', 'betweenness_centrality')
         .order_by('-degree')
         .limit(20)
         .execute(network)
    )

What this gives: a ranked summary under a specific representation.

What it does not give: robustness, causal explanation, or cross-representation invariance.

Method Family Summary Table
---------------------------

+-------------------------+---------------------------+-----------------------------------------------+-----------------------------------------------+
| Method family           | Typical output type       | Main assumption                                | Common failure mode                            |
+=========================+===========================+===============================================+===============================================+
| Native multilayer       | layer-aware score/partition| layer boundaries are meaningful                | overclaiming from one representation choice    |
+-------------------------+---------------------------+-----------------------------------------------+-----------------------------------------------+
| Delegated single-layer  | projected score/partition | projection preserves relevant signal           | semantic drift hidden as "equivalent result"   |
+-------------------------+---------------------------+-----------------------------------------------+-----------------------------------------------+
| Approximate             | approximate ranking/value | approximation error acceptable for objective   | interpreting tiny score differences literally   |
+-------------------------+---------------------------+-----------------------------------------------+-----------------------------------------------+
| Stochastic              | seeded output or UQ summary| sampled/heuristic search reflects target space | treating one run as final without stability     |
+-------------------------+---------------------------+-----------------------------------------------+-----------------------------------------------+

Method Selection Checklist
--------------------------

Before choosing an algorithm, specify:

1. target estimand,
2. acceptable approximation error,
3. computational budget,
4. validation strategy (alternative methods, perturbation, or UQ).

This prevents the common workflow error of selecting methods by convenience rather than inferential fit.
