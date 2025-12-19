Multilayer Networks 101
========================

This chapter explains what multilayer networks are, when to use them, and how to choose the right type for your data—without flattening away important structure.

**You will learn:**

* What distinguishes multilayer from single-layer networks
* Types: multiplex, heterogeneous, temporal, interdependent
* When to use multilayer modeling
* Common pitfalls to avoid

Key ideas to keep in mind:

* A **layer** labels the context of an interaction (relationship type, time slice, modality).
* A **node-layer pair** ``(node_id, layer_id)`` is the atomic unit; the same node can appear in multiple layers.
* **Coupling** uses inter-layer edges that link the same entity across layers, with a weight controlling how strongly layers influence each other. When the weight is 0, layers are independent; higher weights make layers behave more coherently.

What are Multilayer Networks?
-----------------------------

A **multilayer network** models systems with multiple types of relationships, node types, or interaction contexts while keeping each interaction labeled by its layer. Each edge carries both endpoints *and* the layer context, so interactions remain distinguishable.

**Example:** A researcher's social world includes coauthors, colleagues, students, and Twitter followers. These are different relationship types with different meanings. A multilayer network keeps them as separate **layers** rather than flattening into one graph.

**Traditional vs. Multilayer:**

============== ============================ ============================
Aspect         Single-Layer                 Multilayer
============== ============================ ============================
Node types     One (e.g., only people)      Multiple (people, orgs, docs)
Edge types     One (e.g., only friendship)  Multiple per layer
Structure      Homogeneous                  Heterogeneous
Analysis       Standard graph algorithms    Layer-aware algorithms
============== ============================ ============================

Types of Multilayer Networks
-----------------------------

The examples below use simple edge lists to show how different modeling choices map to different layer structures. Choose the structure that matches (a) whether node identities repeat across layers and (b) whether relationships are interchangeable or context-specific.

Multiplex Networks
~~~~~~~~~~~~~~~~~~

**Same nodes, different relationship types.** Use when the *entities* are the same everywhere, but interactions mean different things per layer.

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network(network_type="multiplex")
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
        ['Bob', 'colleagues', 'Dave', 'colleagues', 1],
    ], input_type="list")

**Examples:** Social networks across platforms, transportation via air/rail/road, communication via email/phone/chat.

**Tip:** Inter-layer edges typically connect identical nodes across layers to model the idea that "Alice in friends" is still Alice in "colleagues."

Heterogeneous Information Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Different node types with type-specific relationships.** Use when layers hold different entity types or schemas, not just interaction labels.

.. code-block:: python

    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'authors', 'P1', 'papers', 1],
        ['P1', 'papers', 'ICML', 'venues', 1],
    ], input_type="list")

**Examples:** Academic networks (authors, papers, venues), e-commerce (users, products, sellers), biomedical (drugs, diseases, targets).

**Tip:** Keep node identifiers disjoint across types (e.g., ``P1`` is always a paper) to avoid accidental coupling.

Temporal Networks
~~~~~~~~~~~~~~~~~

**Networks that evolve over time, with time-sliced layers.** Use when order and timing change interpretation (e.g., diffusion, cascades).

.. code-block:: python

    network = multinet.multi_layer_network()
    network.add_edges([
        ['A', '2020', 'B', '2020', 1],
        ['A', '2021', 'B', '2021', 1],
        ['B', '2021', 'C', '2021', 1],
    ], input_type="list")

**Examples:** Communication over time, social dynamics, disease spread.

**Tip:** Choose time-slice granularity that matches the process of interest—too coarse hides dynamics, too fine yields sparse noise. Adjacent slices can be coupled with inter-layer edges to allow information to move through time.

Interdependent Networks
~~~~~~~~~~~~~~~~~~~~~~~~

**Multiple networks where nodes depend on each other rather than sharing identity.** Dependencies capture "if X fails in layer A, Y fails in layer B," not "X is the same as Y."

**Examples:** Power grid depends on communication network, supply chains, cyber-physical systems.

**Tip:** Model dependencies explicitly with inter-layer edges that indicate which nodes fail together or require coordination; these edges can connect different node IDs across layers and often have direction (who depends on whom).

When to Use Multilayer Networks
-------------------------------

Use multilayer modeling when:

1. **Multiple relationship types matter** — Friendship and professional connections behave differently.
2. **Node roles vary by context** — A hub in work may be peripheral in hobbies.
3. **Layer interactions are important** — Transportation failures in one mode affect others.
4. **Temporal evolution matters** — Relationships change over time and order matters.
5. **System-level properties emerge** — Cross-layer dependencies affect resilience, spreading, or coordination.

Choosing a Modeling Approach
----------------------------

Ask these questions:

1. **Layers vs. attributes?** If relationships differ in *kind* (email vs. meeting), use layers. If they differ only in *intensity* (weight, frequency), keep one layer and add attributes.
2. **Same or different nodes?** Same entities in all layers → multiplex. Different entity types → heterogeneous (avoid forcing identity coupling).
3. **Coupling strength?** When identities repeat across layers, set an inter-layer weight ``omega ≥ 0`` to control how tightly node copies move together (e.g., start with ``omega=1.0`` for identity coupling; reduce it if layers should diverge).
4. **Temporal structure?** If order matters, use time-sliced layers with optional coupling between adjacent slices; only aggregate into a static network when chronology is irrelevant.

What Goes Wrong When You Flatten
--------------------------------

Flattening throws away layer information. Typical failure modes include:

**Community structure destroyed:** Flattening can create spurious bridges between groups that are distinct in the layer structure.

**Centrality becomes misleading:** A researcher with 2 coauthors and 500 Twitter followers has degree 502 when flattened, but academic influence is only 2. Centrality scores mix incomparable interaction modes.

**Path analysis fails:** Email → meeting transitions matter for information flow but are invisible in a flattened network, so path-based predictions over- or under-estimate reachability.

**Layer semantics disappear:** Once layers are merged, you can no longer tell which mode of interaction drove a result.

Common Pitfalls
---------------

* **Over-aggregating** — Combining layers that should stay separate; prefer explicit layers when semantics differ.
* **Under-aggregating** — Too many ultra-sparse layers; use edge weights or coarser bins instead.
* **Ignoring coupling** — Treating layers as independent when nodes correspond; set ``omega`` explicitly.
* **Wrong coupling strength** — Too high forces artificial consistency; too low loses cross-layer information.
* **Mismatched identifiers** — Same entity must have the same ID across layers for identity coupling to work.
* **Inconsistent time slicing** — Changing window sizes mid-analysis hides or invents trends; keep cadence consistent.

Key Terminology
---------------

* **Intra-layer edges** — Within a single layer (same layer ID on both endpoints)
* **Inter-layer edges** — Between layers (often identity edges connecting the same node across layers)
* **Node-layer pairs** — ``(node_id, layer_id)`` tuples, the fundamental unit for most algorithms
* **Supra-adjacency matrix** — Block matrix encoding both intra- and inter-layer connections; shape is ``(n·L) × (n·L)`` for ``n`` nodes appearing in ``L`` layers
* **Coupling** — Strength of inter-layer edges (often ``omega``); controls how strongly layers influence one another

Next Steps
----------

* :doc:`py3plex_core_model` — Internal data structures
* :doc:`design_principles` — Why py3plex works this way
* :doc:`algorithm_landscape` — Available algorithms

**References:**

* Kivelä et al. (2014). "Multilayer networks." *J. Complex Networks* 2(3): 203-271.
* Boccaletti et al. (2014). "The structure and dynamics of multilayer networks." *Physics Reports* 544(1): 1-122.
