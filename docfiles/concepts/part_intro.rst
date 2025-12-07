Concepts & Explanations
=======================

Multilayer networks capture systems where entities interact through multiple types of relationships simultaneously. This section explains the theory behind multilayer networks and how py3plex implements them.

**What's in this section:**

* :doc:`multilayer_networks_101` — Types (multiplex, heterogeneous, temporal) and when to use them
* :doc:`py3plex_core_model` — Node-layer pairs, supra-adjacency matrix, NetworkX integration
* :doc:`design_principles` — Why py3plex works the way it does
* :doc:`algorithm_landscape` — Overview of available algorithms

**Reading Paths:**

* **New to multilayer networks?** Start with :doc:`multilayer_networks_101` for essential concepts, then :doc:`py3plex_core_model` to see how py3plex represents them. This foundation is crucial before using the library.

* **Coming from NetworkX?** Read :doc:`py3plex_core_model` to understand the node-layer pair abstraction and supra-adjacency matrix, then :doc:`design_principles` for design decisions. Skip the theory in 101 if you're familiar with complex networks.

* **Building expertise?** Read all chapters in order: theory (:doc:`multilayer_networks_101`), implementation (:doc:`py3plex_core_model`), design rationale (:doc:`design_principles`), and available tools (:doc:`algorithm_landscape`).

After Reading This Section
---------------------------

You'll be able to:

* Model real-world systems as multilayer networks
* Choose appropriate parameters (e.g., inter-layer coupling strength)
* Interpret results correctly
* Avoid common pitfalls (e.g., flattening important structure)

.. tip::

   **Quick check:** After reading this section, you should be able to answer:
   
   * What's the difference between multiplex and heterogeneous networks?
   * What does the supra-adjacency matrix represent?
   * When should you use high vs. low inter-layer coupling?

**Relation to Other Sections:**

* **Overview** (:doc:`../overview/part_intro`) — Quick 2-minute intro to multilayer networks
* **How-to Guides** (:doc:`../how-to/part_intro`) — Apply these concepts in practice
* **Reference** (:doc:`../reference/part_intro`) — Detailed API and algorithm documentation
* **Examples** (:doc:`../examples/index`) — See concepts in action with real code

**Jump to Practical Applications:**

Once you understand the concepts:

* **Load networks:** :doc:`../how-to/load_and_build_networks`
* **Compute statistics:** :doc:`../how-to/compute_statistics`
* **Detect communities:** :doc:`../how-to/run_community_detection`
* **Query networks:** :doc:`../how-to/query_with_dsl`
