Builder API and Explain Plans: Reading Your Own Query
======================================================

This chapter focuses on query structure, execution traceability, and failure diagnosis.

Builder as Structured Intent
----------------------------

The builder API is most valuable when it makes intent reviewable by someone other than the original author.

A useful pattern is to keep pipelines in named stages:

.. code-block:: python

    from py3plex.dsl import Q, L

    scoped = Q.nodes().from_layers(L['social'])
    filtered = scoped.where(degree__gt=5)
    measured = filtered.compute('degree', 'pagerank')
    ranked = measured.order_by('-pagerank').limit(20)
    result = ranked.execute(network)

This is less concise than one long chain, but easier to audit.

Explain Plans
-------------

Use explain tooling to inspect what will be executed and in what order. This is especially important when autocompute, grouping, or coverage steps are involved.

Ask three questions when reading a plan:

1. Which fields are materialized and when?
2. Which operations depend on grouped context?
3. Where could expensive computations be delayed or reduced?

Parameterized Queries
---------------------

For repeated analyses, parameterize thresholds rather than editing literals in notebooks.

.. code-block:: python

    from py3plex.dsl import Q, Param

    query = Q.nodes().where(degree__gt=Param.int('k')).compute('degree')
    result = query.execute(network, k=4)

This improves reproducibility and reduces accidental drift across runs.

Failure Diagnostics
-------------------

When queries fail, categorize the issue quickly:

* syntax-level problem,
* unknown field/measure,
* grouping misuse,
* missing parameters,
* type mismatch.

Treat diagnostic messages as part of your workflow review process, not only as debugging output.

When the Builder Is Not the Right Tool
--------------------------------------

If your workflow is a one-off simple filter, direct Python operations may be clearer. DSL helps most when you need replayability, composability, and explicit provenance.
