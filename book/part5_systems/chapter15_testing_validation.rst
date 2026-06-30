.. _testing-chapter:

Testing and Validation as Methodological Controls
=================================================

Testing is not only software hygiene. In analytical pipelines, tests are controls against silent methodological drift (such as changes in representation or approximation defaults that alter results).

Validation Layers
-----------------

py3plex workflows benefit from four test layers:

1. **Unit checks** for deterministic core behavior.
2. **Property/metamorphic checks** for invariants under transformations.
3. **Differential checks** across equivalent APIs.
4. **Workflow checks** that validate representative end-to-end analyses.

Mini-Test Example (Main-Text Scale)
-----------------------------------

.. code-block:: python

    from py3plex.dsl import Q

    result = Q.nodes().compute('degree').execute(network)
    assert result.count > 0
    assert 'degree' in result.to_pandas().columns

This tiny test does not prove correctness, but it catches a surprisingly common regression class: query executes but expected metric materialization changes silently.

Why This Matters for Analysis
-----------------------------

A pipeline can execute successfully and still be wrong:

* representation drift changes semantics,
* approximation defaults change outputs (for example, an exact betweenness call silently becoming approximate),
* query refactors alter grouping logic.

Tests should target these failure modes directly.

Practical Workflow
------------------

* run focused tests near changed analytical components,
* include at least one deterministic seed-based test for stochastic paths,
* preserve small synthetic fixtures with known expected behavior,
* treat regression diffs as analytical review prompts, not only coding errors.

Current Repository Validation Map
---------------------------------

The repository now contains focused tests for the newer subsystems discussed in
this edition:

* ``tests/test_dsl_lint.py`` for static DSL diagnostics,
* ``tests/test_program.py`` and ``tests/test_dsl_program_rewrite.py`` for
  ``GraphProgram`` identity, typing, and rewrite behavior,
* ``tests/test_algebra_*.py`` and ``tests/property/test_algebra_properties.py``
  for semiring/algebra invariants,
* ``tests/test_meta_analysis.py`` and ``tests/property/test_meta_properties.py``
  for pooled-effect semantics,
* ``tests/test_out_of_core.py`` for streaming-query boundaries,
* ``tests/test_metapath2vec.py`` and embedding examples for representation
  learning behavior.

Use these files as starting points when changing the corresponding package
families.  They are more reliable than searching for a broad "full suite" entry
point because each subsystem has different optional dependencies and runtime
costs.

Example Validation Questions
----------------------------

* Does node/edge count conservation hold after import transformations?
* Do equivalent query formulations return equivalent sets (for example, ``Q.nodes().where(layer='social')`` versus a graph-ops layer filter path)?
* Are ranking changes under perturbation within expected bounds?
* Are provenance fields complete and stable?

When a test fails, treat it as an analytical review decision point: decide whether the underlying methodological change is intended and document it, or roll it back.

Connection to Reproducibility
-----------------------------

Testing catches accidental changes; reproducibility practices make intentional changes auditable. Both are required for credible technical results.
The next chapter turns this into environment-level practice: how to make a run replayable across machines and time.
