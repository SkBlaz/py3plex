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

Concrete delegated/projection path: a workflow may start from a multilayer object, restrict to selected layers, project to a monoplex graph for a delegated NetworkX routine, then map results back to multilayer identifiers. That path is often computationally practical, but it is analytically different from a native multilayer operator.

Theory, Implementation, Workflow
--------------------------------

Throughout py3plex, it helps to separate three categories:

* **Theory:** what a multilayer statistic means mathematically.
* **Implementation:** how py3plex computes or delegates that statistic.
* **Workflow:** how analysts sequence filtering, computation, and validation in practice.

Confusing these categories leads to overclaiming. An implementation convenience is not theoretical justification.

Native multilayer workflows are preferred when the estimand depends on layer identity (for example, cross-layer brokerage, layer coverage, or multilayer community structure). Delegated single-layer backends are often acceptable for exploratory baselines, coarse screening, or compatibility checks, provided the projection step is explicitly reported.

What Users Most Often Overclaim from Implementation Convenience
---------------------------------------------------------------

Three overclaims recur in practice:

1. "This centrality is multilayer-native" when the computation was actually run on a projection.
2. "This partition is robust across contexts" when only one delegated backend and one parameter setting were used.
3. "This ranking is stable" when no perturbation or UQ check was performed.

A useful correction is to phrase results in execution-path terms: "native multilayer estimate" versus "projection-based baseline."

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

Trade-off story: in a commuter network, a projected single-layer betweenness run may finish in seconds and support fast scenario triage, while a native multilayer alternative may take longer but preserve transfer semantics needed for policy claims. The right choice depends on whether the question is screening or inference.

Why This Matters
----------------

py3plex optimizes for explicit, auditable multilayer workflows under practical constraints; it does not optimize for eliminating methodological judgment. Remember this contrast: fast convenience paths are valuable for exploration, but only semantically aligned paths can support strong claims.
