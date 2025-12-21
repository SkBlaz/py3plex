How-to Guides
=============

Task-oriented guides for accomplishing specific goals with py3plex. Each guide answers a single question: "How do I...?" with runnable steps you can copy and run.

Pick the task that matches your question and jump straight to the guide.

**This section covers (by topic):**

Network Operations
------------------

* :doc:`load_and_build_networks` — Create networks from scratch or load from files
* :doc:`export_serialize` — Save networks in various formats
* :doc:`compat_conversions` — Convert between py3plex and other graph libraries

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

**What every guide contains:**

1. **Goal:** What you'll accomplish
2. **Prerequisites:** What you need to know first
3. **Steps:** Concrete, actionable instructions with code
4. **Expected output:** What you should see
5. **Next steps:** Links to related concepts and references

**How to navigate:**

* Jump directly to the task you need—each guide is **self-contained**
* Copy-paste examples—they are **complete and runnable**
* Find **what to do** here; for theory, see :doc:`../concepts/part_intro`
* Need API signatures? Go to :doc:`../reference/part_intro`
* Use the quick navigation below if you already know the task name

Quick Navigation
----------------

**I want to...**

* Load data → :doc:`load_and_build_networks`
* Export or serialize data → :doc:`export_serialize`
* Convert to/from NetworkX, SciPy, igraph → :doc:`compat_conversions`
* Measure network properties → :doc:`compute_statistics`
* Find communities → :doc:`run_community_detection`
* Create visualizations → :doc:`visualize_networks`
* Query networks → :doc:`query_with_dsl`
* Find patterns/motifs → :doc:`query_with_patterns`
* Model processes → :doc:`simulate_dynamics`

**I'm coming from...**

* **NetworkX:** Start with :doc:`load_and_build_networks` for multilayer basics, then :doc:`query_with_dsl` for py3plex's DSL
* **Single-layer networks:** See :doc:`compute_statistics` and :doc:`run_community_detection` for multilayer-specific metrics
* **Other tools:** Jump to :doc:`export_serialize` for import/export expectations

Related Sections
----------------

* **Learning multilayer concepts:** :doc:`../concepts/part_intro`
* **Detailed API reference:** :doc:`../reference/part_intro`
* **Complete examples:** :doc:`../examples/index`
* **Tutorials for beginners:** :doc:`../getting_started/part_intro`
