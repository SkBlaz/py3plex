.. _limitations-stability-chapter:

Limitations and Stability: What py3plex Does Not Promise
=========================================================

This chapter is intentionally strict. It defines reliability boundaries for methods used in this book.

Scope of Stability Statements
-----------------------------

A statement like "stable API" means the workflows documented here are intended to remain usable across minor revisions. It does **not** mean every internal behavior is immutable.

Major Limitation Classes
------------------------

1. **Semantic limitations**
   Multilayer outputs can be misread if replica-level and physical-node interpretations are mixed.

2. **Algorithmic limitations**
   Some methods rely on assumptions (connectivity, weight domains, stochastic convergence) that may fail silently if not checked.

3. **Scalability limitations**
   Exact methods can become impractical on larger graphs; approximations trade precision for tractability.

4. **Interoperability limitations**
   Delegation to single-layer backends can alter semantics if projection steps are not explicit.

Stability Practices That Help
-----------------------------

* pin versions for reproducible studies,
* record query provenance and random seeds,
* include at least one robustness comparison,
* keep method caveats near reported results.

What to Report in Publications
------------------------------

At minimum, report:

* representation choices,
* algorithm and parameter settings,
* approximation/UQ configuration,
* software version and environment details,
* known limitations relevant to your claims.

A short, honest limitations paragraph is usually more credible than broad claims of robustness.
