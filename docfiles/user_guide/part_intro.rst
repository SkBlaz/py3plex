User Guide
==========

Comprehensive how-to guides covering every major py3plex capability—from basic network operations to advanced analysis workflows.

.. admonition:: Featured: DSL Query Language
   :class: dsl-example

   One of py3plex's standout features is the **SQL-like DSL** for querying networks:

   .. code-block:: python

       from py3plex.dsl import Q, L

       # Declarative, readable network queries
       result = (
           Q.nodes()
            .from_layers(L["social"] + L["work"])
            .where(degree__gt=5)
            .compute("betweenness_centrality")
            .order_by("-betweenness_centrality")
            .limit(10)
            .execute(network)
       )

   The DSL makes complex analyses concise and maintainable. See :doc:`dsl` for complete details!

**Reading Paths:**

* **New users:** Start with :doc:`networks` (creating and loading networks), then :doc:`statistics` (basic metrics), then explore :doc:`visualization` (seeing your data). This gives you the core workflow: load → analyze → visualize.

* **NetworkX users:** Jump to :doc:`dsl` to see py3plex's query language, then :doc:`community_detection` and :doc:`statistics` for multilayer-specific algorithms that extend what you know from single-layer analysis.

* **Advanced users:** Begin with :doc:`multilayer_dynamics` for simulations, :doc:`random_walks_embeddings` for learning representations, and :doc:`recipes_and_workflows` for production patterns. See :doc:`case_studies` for complete real-world examples.

**This section covers:**

* **Networks** — Create, load, query, and extract subnetworks
* **Statistics** — Measure layer density, node activity, edge overlap, versatility
* **Community Detection** — Find groups of nodes that cluster together across layers
* **Multilayer Dynamics** — Simulate epidemic spread and diffusion processes
* **Random Walks & Embeddings** — Generate features for machine learning
* **I/O and Formats** — Import/export data in various formats
* **Visualization** — Create publication-ready network diagrams
* **DSL** — SQL-like query language for network exploration
* **Graph Operations** — Chainable API for data transformations
* **Recipes & Workflows** — Ready-to-use solutions for common tasks
* **Case Studies** — Complete end-to-end analyses
