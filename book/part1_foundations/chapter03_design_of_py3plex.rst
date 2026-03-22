Design of py3plex: Trade-offs and Boundaries
=============================================

This chapter explains why py3plex is structured the way it is, and what those choices imply for analysis quality.

Design Goal
-----------

py3plex is designed to make multilayer analysis practical in Python without hiding key modeling decisions.

The project prioritizes:

1. a consistent multilayer representation,
2. interoperability with established graph tooling,
3. explicit caveats around approximations and feature maturity.

Core Architectural Choice
-------------------------

py3plex builds on NetworkX-compatible graph objects while layering multilayer semantics on top.

**Benefit:** immediate access to mature single-layer algorithms and ecosystem tooling.

**Cost:** some multilayer operations necessarily pass through reductions (for example, layer-restricted or projected computations). Those transitions can alter interpretation if not documented.

Theory, Implementation, Workflow
--------------------------------

Throughout py3plex, it helps to separate three categories:

* **Theory:** what a multilayer statistic means mathematically.
* **Implementation:** how py3plex computes or delegates that statistic.
* **Workflow:** how analysts sequence filtering, computation, and validation in practice.

Confusing these categories leads to overclaiming. An implementation convenience is not theoretical justification.

What py3plex Optimizes For
--------------------------

* reproducible scripting workflows,
* incremental exploration from small to medium-scale multilayer graphs,
* composable query pipelines (especially via DSL in Part III).

What py3plex Does Not Optimize For
----------------------------------

* maximal performance on very large graphs without approximation,
* complete replacement of specialized HPC graph libraries,
* automatic protection from poor modeling assumptions.

Implications for Users
----------------------

If your analysis is sensitive to representation choices or approximation error:

1. record provenance and seeds,
2. run at least one robustness check,
3. compare multilayer and flattened baselines explicitly,
4. report implementation path (native multilayer vs delegated/projection path).

Why This Matters
----------------

Architecture is methodology in practice. Knowing where py3plex delegates, approximates, or preserves multilayer semantics is part of responsible interpretation.
