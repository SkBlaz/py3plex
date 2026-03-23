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

Worked Explain-Plan Walkthrough
-------------------------------

Consider this query:

.. code-block:: python

    query = (
        Q.nodes()
         .from_layers(L['social'] + L['work'])
         .where(degree__gt=5)
         .compute('degree', 'betweenness_centrality')
         .order_by('-betweenness_centrality')
         .limit(15)
    )

An explain plan should show that layer scoping and filtering happen before expensive centrality computation. Scientifically, that matters because it defines the analysis population before ranking, making the inferential target explicit rather than accidental.

Opaque Long Chain vs Staged Rewrite
-----------------------------------

Opaque chain:

.. code-block:: python

    result = Q.nodes().from_layers(L['*']).where(degree__gt=3).compute('degree', 'pagerank').per_layer().top_k(10, 'pagerank').end_grouping().coverage(mode='at_least', k=2).order_by('-pagerank').limit(20).execute(network)

Improved staged rewrite:

.. code-block:: python

    scoped = Q.nodes().from_layers(L['*']).where(degree__gt=3)
    measured = scoped.compute('degree', 'pagerank')
    grouped = measured.per_layer().top_k(10, 'pagerank').end_grouping()
    reviewed = grouped.coverage(mode='at_least', k=2).order_by('-pagerank').limit(20)
    result = reviewed.execute(network)

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

Common failure examples:

.. code-block:: python

    # Missing parameter
    query = Q.nodes().where(degree__gt=Param.int('k')).compute('degree')
    # query.execute(network)  # raises parameter-missing error

    # Grouping misuse
    bad = Q.nodes().coverage(mode='all')  # coverage without grouping context

Auditable Review: Provenance and AST Hash
-----------------------------------------

Explain plans are not only computational aids. Together with provenance and AST hash, they support auditable scientific review: reviewers can verify the exact query structure that produced a claim and detect silent workflow drift across revisions.

When the Builder Is Not the Right Tool
--------------------------------------

If your workflow is a one-off simple filter, direct Python operations may be clearer. DSL helps most when you need replayability, composability, and explicit provenance.
