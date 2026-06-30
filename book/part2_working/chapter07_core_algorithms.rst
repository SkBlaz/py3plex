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

Robustness-oriented centrality helpers live alongside the traditional
multilayer centrality implementations.  Use them when the scientific claim is
about rank stability or sensitivity, not only about a single centrality value.

Embeddings and Representation Learning
--------------------------------------

The current repository includes embedding APIs in ``py3plex.embeddings`` and
``py3plex.ml.embedding``.  These cover NetMF, MetaPath2Vec, Node2Vec,
DeepWalk/LINE-style primitives, multiplex variants, link-feature operators, and
shared training/evaluation utilities.

Embedding outputs are useful for exploratory similarity, link prediction, and
downstream machine-learning features.  They should not be described as
interpretable multilayer explanations unless the chosen walk schema, meta-paths,
negative sampling, and evaluation target are reported.

Algebraic Paths and Closure
---------------------------

``py3plex.algebra`` and ``py3plex.semiring`` provide semiring-style path,
closure, fixed-point, and witness machinery.  This is the appropriate family
when a workflow needs explicit path algebra (for example shortest paths,
reachability, reliability, or lexicographic transfer costs) rather than a
single hard-coded shortest-path routine.

Report the semiring, lift function, hop bounds, and witness policy whenever
path outputs support a claim.

Statistical Pooling and Experiment Records
------------------------------------------

``py3plex.meta`` supports fixed-effect and random-effects meta-analysis of
network statistics across datasets or experimental conditions.  ``py3plex`` also
includes ``experiments`` helpers for storing run metadata and artifacts.

Use these when a conclusion depends on repeated networks or repeated runs.  Do
not pool scores across networks without checking whether the estimand and
standard errors are comparable.

Out-of-Core and Planning Infrastructure
---------------------------------------

``py3plex.out_of_core`` provides streaming query execution for disk-resident
edge data, and ``py3plex.optimizer``/``py3plex.dsl.program`` provide planning,
cost, and rewrite infrastructure.  These are scalability aids.  They do not
remove the need to state which query shapes are supported and which operations
fall back to in-memory analysis.

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
| Embedding               | vector representation      | walk/objective captures relevant similarity    | treating latent coordinates as explanations     |
+-------------------------+---------------------------+-----------------------------------------------+-----------------------------------------------+
| Algebraic path/closure  | path value or witness      | semiring/lift matches the substantive path cost| hiding semantics in an arbitrary weight lift    |
+-------------------------+---------------------------+-----------------------------------------------+-----------------------------------------------+
| Meta-analysis           | pooled effect/interval     | comparable effects and uncertainty estimates   | pooling incompatible networks or estimands      |
+-------------------------+---------------------------+-----------------------------------------------+-----------------------------------------------+

Method Selection Checklist
--------------------------

Before choosing an algorithm, specify:

1. target estimand,
2. acceptable approximation error,
3. computational budget,
4. validation strategy (alternative methods, perturbation, or UQ).

This prevents the common workflow error of selecting methods by convenience rather than inferential fit.
