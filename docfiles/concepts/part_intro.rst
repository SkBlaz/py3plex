Concepts & Explanations
=======================

Multilayer networks capture systems where entities interact through multiple types of relationships simultaneously. Use this section to understand the core ideas and learn where each concept is explained in depth.

**What's in this section**

* :doc:`multilayer_networks_101` — Modeling choices (multiplex, heterogeneous, temporal) and when to use each
* :doc:`py3plex_core_model` — Node-layer pairs, supra-adjacency matrix, and how it wraps NetworkX
* :doc:`design_principles` — Why py3plex is structured as it is
* :doc:`algorithm_landscape` — What analysis tools are available and how they fit together

**Reading paths**

* **New to multilayer networks?** Start with :doc:`multilayer_networks_101`, then read :doc:`py3plex_core_model` to see how py3plex represents layers, node-layer pairs, and coupling.
* **Coming from NetworkX?** Jump to :doc:`py3plex_core_model` for the node-layer abstraction and supra-adjacency matrix, then skim :doc:`design_principles` for rationale.
* **Building expertise?** Read in order: theory (:doc:`multilayer_networks_101`), implementation (:doc:`py3plex_core_model`), design rationale (:doc:`design_principles`), and tools (:doc:`algorithm_landscape`).

After Reading This Section
--------------------------

You'll be able to:

* Model real-world systems as multilayer networks instead of flattening them
* Choose appropriate parameters (e.g., layer definitions, inter-layer coupling strength)
* Interpret results in terms of layers and node-layer pairs rather than anonymous nodes
* Avoid common pitfalls (e.g., flattening important structure, mismatched identifiers)

.. tip::

   **Quick check:** After reading this section, you should be able to answer:

   * What distinguishes multiplex from heterogeneous networks?
   * What does the supra-adjacency matrix represent and why use it?
   * When should you tighten vs. relax inter-layer coupling?

**Relation to other sections**

* **Overview** (:doc:`../overview/part_intro`) — Quick 2-minute intro to multilayer networks
* **How-to Guides** (:doc:`../how-to/part_intro`) — Apply these concepts in practice
* **Reference** (:doc:`../reference/part_intro`) — Detailed API and algorithm documentation
* **Examples** (:doc:`../examples/index`) — See concepts in action with real code

**Jump to practical applications**

Once you understand the concepts:

* **Load networks:** :doc:`../how-to/load_and_build_networks`
* **Compute statistics:** :doc:`../how-to/compute_statistics`
* **Detect communities:** :doc:`../how-to/run_community_detection`
* **Query networks:** :doc:`../how-to/query_with_dsl`
