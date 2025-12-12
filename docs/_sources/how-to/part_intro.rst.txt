How-to Guides
=============

Task-oriented guides for accomplishing specific goals with py3plex. Each guide is focused on a single question: "How do I...?"

**This section covers:**

Network Operations
------------------

* :doc:`load_and_build_networks` — Create networks from scratch or load from files
* :doc:`export_serialize` — Save networks in various formats

Analysis Tasks
--------------

* :doc:`compute_statistics` — Calculate multilayer metrics and centrality measures
* :doc:`run_community_detection` — Find groups of closely connected nodes
* :doc:`simulate_dynamics` — Model epidemic spread and diffusion processes
* :doc:`run_random_walks` — Generate network embeddings for machine learning

Visualization
-------------

* :doc:`visualize_networks` — Create publication-ready network diagrams

Query and Transform
-------------------

* :doc:`query_with_dsl` — Use SQL-like syntax for network queries
* :doc:`query_with_patterns` — Find graph motifs and subgraph patterns
* :doc:`build_pipelines` — Chain operations with dplyr-style API

Workflows
---------

* :doc:`reproduce_workflows` — Complete analysis recipes and patterns

Reading This Section
--------------------

**Structure of each guide:**

1. **Goal:** What you'll accomplish
2. **Prerequisites:** What you need to know first
3. **Steps:** Concrete, actionable instructions with code
4. **Expected output:** What you should see
5. **Next steps:** Links to related concepts and references

**How to use these guides:**

* Each guide is **self-contained** — you can jump directly to the task you need
* Code examples are **complete and runnable** — copy-paste and run
* Guides focus on **what to do**, not why — for theory, see :doc:`../concepts/part_intro`
* For API details, see :doc:`../reference/part_intro`

Quick Navigation
----------------

**I want to...**

* Load data → :doc:`load_and_build_networks`
* Measure network properties → :doc:`compute_statistics`
* Find communities → :doc:`run_community_detection`
* Create visualizations → :doc:`visualize_networks`
* Query networks → :doc:`query_with_dsl`
* Find patterns/motifs → :doc:`query_with_patterns`
* Model processes → :doc:`simulate_dynamics`

**I'm coming from...**

* **NetworkX:** Start with :doc:`load_and_build_networks` to see multilayer specifics, then :doc:`query_with_dsl` for py3plex's unique DSL
* **Single-layer networks:** Read :doc:`compute_statistics` and :doc:`run_community_detection` to understand multilayer-specific metrics
* **Other tools:** Jump to :doc:`export_serialize` for data import/export

Related Sections
----------------

* **Learning multilayer concepts:** :doc:`../concepts/part_intro`
* **Detailed API reference:** :doc:`../reference/part_intro`
* **Complete examples:** :doc:`../examples/index`
* **Tutorials for beginners:** :doc:`../getting_started/part_intro`
