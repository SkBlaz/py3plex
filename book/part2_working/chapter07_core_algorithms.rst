.. _algorithms-chapter:

Core Algorithms: What Is Estimated, What Is Approximated
=========================================================

This chapter organizes py3plex algorithm use around interpretation risk rather than interface breadth.

Three Families
--------------

1. **Community detection** (partition structure)
2. **Centrality** (node or edge importance under specific definitions)
3. **Dynamics** (state evolution under explicit process assumptions)

Community Detection
-------------------

py3plex supports multilayer community workflows through methods such as Louvain/Leiden-style procedures and related wrappers.

Interpretive caution:

* Partition quality metrics are objective-specific.
* Comparable scores do not imply identical community semantics across methods.
* Global vs per-layer community detection answer different questions.

Centrality
----------

Many centrality measures are available, but users must state:

* whether analysis is per-layer or global,
* whether values are exact or approximated,
* whether measures were computed on native multilayer structure or reduced projections.

Approximation is often suitable for ranking-oriented exploration on larger graphs, but claims about small score differences should be avoided unless validated.

Dynamics
--------

SIS/SIR-like models in py3plex are useful for scenario analysis under explicit assumptions.

Do not infer causal epidemiological truths from toy parameter sweeps. Dynamics outputs are model-conditional, not domain truth.

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

Method Selection Checklist
--------------------------

Before choosing an algorithm, specify:

1. target estimand,
2. acceptable approximation error,
3. computational budget,
4. validation strategy (alternative methods, perturbation, or UQ).

This prevents the common workflow error of selecting methods by convenience rather than inferential fit.
