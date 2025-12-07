Concepts & Architecture
=======================

Multilayer networks capture systems where entities interact through multiple types of relationships simultaneously. This section explains the theory behind multilayer networks and how py3plex implements them.

**Reading Paths:**

* **New to multilayer networks?** Start with :doc:`multilayer_networks_101` for essential concepts, then :doc:`py3plex_core_model` to see how py3plex represents them. This foundation is crucial before using the library.

* **Coming from NetworkX?** Read :doc:`py3plex_core_model` to understand the node-layer pair abstraction and supra-adjacency matrix, then :doc:`design_principles` for design decisions. Skip the theory in 101 if you're familiar with complex networks.

* **Building expertise?** Read all four chapters in order: theory (:doc:`multilayer_networks_101`), implementation (:doc:`py3plex_core_model`), design rationale (:doc:`design_principles`), and available tools (:doc:`algorithm_landscape`).

**This section covers:**

* **Multilayer Networks 101** — Types (multiplex, heterogeneous, temporal) and when to use them
* **py3plex Core Model** — Node-layer pairs, supra-adjacency matrix, NetworkX integration
* **Design Principles** — Why py3plex works the way it does
* **Algorithm Landscape** — Overview of available algorithms

After reading, you'll be able to:

* Model real-world systems as multilayer networks
* Choose appropriate parameters (e.g., inter-layer coupling strength)
* Interpret results correctly
* Avoid common pitfalls (e.g., flattening important structure)

.. tip::

   **Quick check:** After reading this section, you should be able to answer:
   
   * What's the difference between multiplex and heterogeneous networks?
   * What does the supra-adjacency matrix represent?
   * When should you use high vs. low inter-layer coupling?
