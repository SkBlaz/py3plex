Multilayer Networks 101
========================

This chapter explains what multilayer networks are, when to use them, and how to choose the right type for your data.

**You will learn:**

* What distinguishes multilayer from single-layer networks
* Types: multiplex, heterogeneous, temporal, interdependent
* When to use multilayer modeling
* Common pitfalls to avoid

What are Multilayer Networks?
-----------------------------

A **multilayer network** models systems with multiple types of relationships, node types, or interaction contexts.

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

Multiplex Networks
~~~~~~~~~~~~~~~~~~

**Same nodes, different relationship types.**

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

Heterogeneous Information Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Different node types with type-specific relationships.**

.. code-block:: python

    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'authors', 'P1', 'papers', 1],
        ['P1', 'papers', 'ICML', 'venues', 1],
    ], input_type="list")

**Examples:** Academic networks (authors, papers, venues), e-commerce (users, products, sellers), biomedical (drugs, diseases, targets).

Temporal Networks
~~~~~~~~~~~~~~~~~

**Networks that evolve over time, with time-sliced layers.**

.. code-block:: python

    network = multinet.multi_layer_network()
    network.add_edges([
        ['A', '2020', 'B', '2020', 1],
        ['A', '2021', 'B', '2021', 1],
        ['B', '2021', 'C', '2021', 1],
    ], input_type="list")

**Examples:** Communication over time, social dynamics, disease spread.

Interdependent Networks
~~~~~~~~~~~~~~~~~~~~~~~~

**Multiple networks where nodes depend on each other.**

**Examples:** Power grid depends on communication network, supply chains, cyber-physical systems.

When to Use Multilayer Networks
-------------------------------

Use multilayer modeling when:

1. **Multiple relationship types matter** — Friendship and professional connections behave differently
2. **Node roles vary by context** — A hub in work network may be peripheral in hobby network
3. **Layer interactions are important** — Transportation failures in one mode affect others
4. **Temporal evolution matters** — Relationships change over time
5. **System-level properties emerge** — Cross-layer dependencies affect resilience

Choosing a Modeling Approach
----------------------------

Ask these questions:

1. **Layers vs. attributes?** If relationships have different *types* → use layers. If they vary only in *weight* → use edge attributes.

2. **Same or different nodes?** Same entities in all layers → multiplex. Different entity types → heterogeneous.

3. **Coupling strength?** Identity coupling only → ``omega=1.0``. Nodes can differ → lower omega.

4. **Temporal structure?** Yes → time-sliced layers. No → aggregate into static network.

What Goes Wrong When You Flatten
--------------------------------

**Community structure destroyed:** Flattening can create spurious bridges between groups that are distinct in the layer structure.

**Centrality becomes misleading:** A researcher with 2 coauthors and 500 Twitter followers has degree 502 when flattened, but academic influence is only 2.

**Path analysis fails:** Email → meeting transitions matter for information flow but are invisible in a flattened network.

Common Pitfalls
---------------

* **Over-aggregating** — Combining layers that should stay separate
* **Under-aggregating** — Too many sparse layers (use edge weights instead)
* **Ignoring coupling** — Treating layers as independent when nodes correspond
* **Wrong coupling strength** — Too high forces artificial consistency; too low loses information
* **Mismatched identifiers** — Same entity must have same ID across layers

Key Terminology
---------------

* **Intra-layer edges** — Within a single layer
* **Inter-layer edges** — Between layers (often identity edges connecting same node)
* **Node-layer pairs** — ``(node_id, layer_id)`` tuples, the fundamental unit
* **Supra-adjacency matrix** — Block matrix encoding both intra- and inter-layer connections

Next Steps
----------

* :doc:`py3plex_core_model` — Internal data structures
* :doc:`design_principles` — Why py3plex works this way
* :doc:`algorithm_landscape` — Available algorithms

**References:**

* Kivelä et al. (2014). "Multilayer networks." *J. Complex Networks* 2(3): 203-271.
* Boccaletti et al. (2014). "The structure and dynamics of multilayer networks." *Physics Reports* 544(1): 1-122.

