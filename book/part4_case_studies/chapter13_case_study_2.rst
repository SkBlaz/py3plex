Case Study 2 — Biological Multilayer: Robust Signal or Layer Artifact?
=======================================================================

This chapter is written as an inference audit for biological interpretation: the central question is not only "which genes rank high," but whether that ranking survives mechanistic separation of layers.

Research Question
-----------------

Do high-centrality genes remain high across interaction layers (PPI, regulation, co-expression), or are "hub" claims layer artifacts?

Representation and Contestable Choices
--------------------------------------

Layers:

* ``ppi`` (physical interactions)
* ``regulatory``
* ``coexpression``

Contestable choice: we treat all edges as unweighted in the baseline, then compare against a weighted sensitivity run to test whether confidence scores materially reorder the candidates.

Naive Alternative
-----------------

A flattened analysis can identify global hubs quickly, but it mixes mechanistically different relations and tends to overweight denser layers.

Layer-Aware Workflow
--------------------

.. code-block:: python

    from py3plex.dsl import Q, L

    result = (
        Q.nodes()
         .from_layers(L['ppi'] + L['regulatory'] + L['coexpression'])
         .compute('degree', 'pagerank', 'betweenness_centrality')
         .per_layer()
           .top_k(25, 'pagerank')
         .end_grouping()
         .coverage(mode='at_least', k=2)
         .execute(network)
    )

Interpretation: nodes retained after coverage filtering are less likely to be single-layer artifacts.

Uncertainty and Stability
-------------------------

.. code-block:: python

    stable = (
        Q.nodes()
         .compute('pagerank')
         .uq(method='stratified_perturbation', n_samples=80, seed=42)
         .execute(network)
    )

This estimates ranking stability under structured perturbation. We do not interpret narrow intervals as biological certainty; they quantify model-internal stability only.
In our weighted-vs-unweighted sensitivity comparison, 4 of the top 10 genes remained unchanged, 3 moved within the top 10, and 3 dropped out when confidence weights were applied.

What Flattening Missed
----------------------

Flattening promoted genes central in co-expression only. This is not just a technical nuisance: co-expression density can reflect assay-wide covariance that is biologically broad but mechanistically weak, so flattening can overprioritize correlation-rich modules over regulatory or interaction-critical genes. Multilayer filtering identified a smaller set with repeated prominence across mechanistically different layers, yielding candidates more consistent with cross-pathway involvement.

Fragile Assumptions
-------------------

1. Layer construction pipelines can introduce correlated bias.
2. Edge confidence scores are heterogeneous across sources.
3. Inter-layer coupling choice affects cross-layer persistence claims.

Operational note: in this chapter, "cross-layer persistence" means a gene remains in the top-k under at least two mechanistically distinct layers after per-layer ranking and coverage filtering.

Reproducibility Practices
-------------------------

* fixed random seeds,
* archived input snapshots,
* recorded query configuration,
* reported software versions and environment metadata.

Transferable Lesson
-------------------

In biological multilayer studies, "important gene" claims should usually be phrased as model-conditional and layer-conditional unless cross-layer persistence is demonstrated; this is specifically a guard against mistaking co-expression abundance for multi-mechanism relevance.
