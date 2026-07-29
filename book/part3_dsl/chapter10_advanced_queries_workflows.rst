.. _advanced-dsl-chapter:

Advanced Workflows: Compositional Queries Under Uncertainty
===========================================================

Advanced DSL usage is not about longer chains. It is about controlling semantic scope, computational cost, and uncertainty propagation.

Workflow Pattern 1: Grouped Selection with Coverage
----------------------------------------------------

.. code-block:: python

    from py3plex.dsl import Q, L

    result = (
        Q.nodes()
         .from_layers(L['*'])
         .compute('degree')
         .per_layer()
           .top_k(10, 'degree')
         .end_grouping()
         .coverage(mode='at_least', k=2)
         .execute(network)
    )

Judgment point: coverage threshold controls strictness. ``all`` can be too restrictive in heterogeneous systems.
Do not use coverage when the analysis target is deliberately layer-specific; cross-layer intersection logic can erase exactly the heterogeneity you are trying to study.

Workflow Pattern 2: UQ-Aware Ranking
------------------------------------

.. code-block:: python

    result = (
        Q.nodes()
         .compute('pagerank')
         .uq(method='bootstrap', n_samples=100, seed=42)
         .order_by('-pagerank')
         .limit(20)
         .execute(network)
    )

Interpretive warning: confidence intervals quantify algorithm/data perturbation under a model; they do not validate domain truth.
Interpretive warning: interval overlap does not imply irrelevance, and non-overlap does not imply biological or social truth; both depend on model choice, data quality, and estimand definition.

Workflow Pattern 3: Temporal Slicing
------------------------------------

.. code-block:: python

    temporal = (
        Q.edges()
         .during(100.0, 150.0)
         .from_layers(L['transport'])
         .execute(temporal_network)
    )

Judgment point: time-window boundaries can dominate observed effects. Report window design choices explicitly.
Here ``.during()`` is intended as stable public DSL syntax for temporal windowing, not merely illustrative pseudocode.

Composability vs Readability
----------------------------

As pipelines grow, readability declines. Recommended practices:

* split complex pipelines into named stages,
* log final query strings or AST hashes,
* avoid mixing exploratory and production logic in one chain.

Performance and Approximation
-----------------------------

For larger networks:

* use selective layer scopes before expensive measures,
* use approximations when ranking is sufficient,
* record approximation parameters in outputs.

Never present approximate outputs as exact without explicit disclosure.

Static Review Before Execution
------------------------------

Current DSL tooling includes a static-analysis layer in ``py3plex.dsl.lint``.
Use it before long or expensive runs when a query depends on fragile layer names,
schema assumptions, or expensive full scans.

.. code-block:: python

    from py3plex.dsl import Q
    from py3plex.dsl.lint import lint

    query = Q.nodes().where(degree__gt=5).compute('pagerank').to_ast()
    diagnostics = lint(query, graph=network)
    for diagnostic in diagnostics:
        print(diagnostic.code, diagnostic.message)

This does not replace execution-time validation.  It is an early warning layer
for unknown layers, unknown attributes, type mismatches, redundant predicates,
and performance hazards.

Graph Programs and Rewrites
---------------------------

For reusable workflows that must be inspected, transformed, or compared,
``py3plex.dsl.program`` exposes ``GraphProgram`` objects.  The practical use
case is not "more abstraction"; it is auditable program identity, rewrite
history, cost estimates, and execution fingerprints.

.. code-block:: python

    from py3plex.dsl import Q
    from py3plex.dsl.program import GraphProgram, apply_rewrites

    program = GraphProgram.from_ast(Q.nodes().compute('degree').to_ast())
    optimized = apply_rewrites(program)
    result = optimized.execute(network)

When reviewing a rewritten program, verify that optimization did not change the
analysis population, grouping semantics, or uncertainty configuration.

Scaling and Cross-Run Workflows
-------------------------------

The advanced DSL ecosystem now includes adjacent infrastructure:

* ``py3plex.out_of_core`` for supported streaming query shapes over disk-backed
  edge data,
* ``py3plex.meta`` for pooling comparable network statistics across networks,
* ``py3plex.experiments`` for persisting run metadata and artifacts.

These tools are most valuable when they preserve the same query semantics while
making larger or repeated analyses auditable.  They should not be used to hide
unsupported query patterns or incompatible effect definitions.

Advanced Checklist
------------------

Before finalizing an advanced query workflow:

1. verify semantic scope (global vs per-layer),
2. verify uncertainty configuration,
3. verify seeds and provenance capture,
4. verify that outputs answer the intended question.

Synthesis: Managing Complexity Creep
------------------------------------

Advanced pipelines fail most often through complexity creep: each added clause is locally reasonable, but the combined workflow becomes hard to audit. Treat readability, explicit assumptions, and provenance capture as first-class constraints, not post-hoc cleanup tasks.
