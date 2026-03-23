.. _data-loading-chapter:

Data Loading and Representation Choices
=======================================

Loading data is not a clerical step. Representation decisions made here determine what your metrics can mean later.

Representation Decisions with Analytical Consequences
-----------------------------------------------------

Before importing anything, answer:

1. What constitutes a layer in this domain?
2. Are inter-layer edges observed data, inferred links, or modeling conveniences?
3. Are edge weights comparable across layers?
4. What entity identity rules resolve duplicates and missingness?

These decisions should be documented alongside code.

A Minimal, Auditable Loading Pattern
------------------------------------

.. code-block:: python

    from py3plex.core import multinet

    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Alice', 'type': 'work'},
        {'source': 'Bob',   'type': 'social'},
    ])
    net.add_edges([
        {'source': 'Alice', 'target': 'Bob',
         'source_type': 'social', 'target_type': 'social'},
    ])

    layers = net.get_layers()
    print(layers)

Implementation detail: py3plex expects explicit layer attributes in node and edge dictionaries for multilayer semantics.

Bad Import / Corrected Import (Layer Naming)
--------------------------------------------

.. code-block:: python

    # Bad: inconsistent layer labels create artificial layer splits
    bad_edges = [
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'Social', 'target_type': 'social'},
    ]

    # Corrected: normalize labels before import
    fixed_edges = [
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    ]

Format Selection (Practical Rule)
---------------------------------

Use format choice as a workflow decision:

* **CSV/edgelist:** transparent and easy to diff; good for iterative cleaning.
* **GraphML/GML:** richer metadata, stronger interoperability.
* **Arrow/Parquet pipelines:** useful when throughput and schema stability matter.

No format is universally best. Prefer the one that minimizes ambiguity in your current pipeline.

Validation Before Analysis
--------------------------

At minimum, validate:

* layer names and counts,
* missing node or layer labels,
* self-loops and duplicate edges (if relevant to your methods),
* weight domain assumptions (non-negative, normalized, etc.).
* explicit distinction between coupling edges and domain edges.

A naive mistake is to accept parser success as data validity.

Coupling Edges vs Domain Edges
------------------------------

Coupling edges encode identity continuity across layers (for example, ``Alice_social`` to ``Alice_work``), while domain edges encode real relations inside a domain layer (for example, trust or transaction ties). Mixing both without tags makes transfer intensity look like domain connectivity and can distort both centrality and community interpretation.

What Can Go Wrong
-----------------

* Layer labels encoded inconsistently (e.g., `Social`, `social`, `soc`).
* Coupling edges mixed with domain edges without tagging.
* Flattened imports accidentally treated as multilayer outputs.
* Cross-layer weights treated as comparable when one layer uses probabilities and another uses counts (for example, 0.8 reliability vs 80 interactions).
* Missingness concentrated in one layer, causing false "low influence" or unstable community assignments for nodes that are merely under-observed.

These errors usually survive until interpretation, where they are expensive to detect.

Recommendation
--------------

Treat data loading code as part of your methodological appendix. If another analyst cannot reconstruct your representation choices from that code, the pipeline is not yet ready. At the end of loading, save a reproducibility bundle containing the cleaned input snapshot, layer schema, entity-resolution rules, and a machine-readable load manifest (versions, parsing options, and checksums).
