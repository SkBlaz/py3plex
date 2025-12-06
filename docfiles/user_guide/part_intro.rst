User Guide
==========

This section provides comprehensive how-to guides for every major py3plex capability.

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

**This section covers:**

* **Networks** — Create, load, query, and extract subnetworks
* **Statistics** — Measure layer density, node activity, edge overlap, versatility
* **Community Detection** — Find groups of nodes that cluster together across layers
* **Random Walks & Embeddings** — Generate features for machine learning
* **I/O and Formats** — Import/export data in various formats
* **Visualization** — Create publication-ready network diagrams
* **DSL** — SQL-like query language for network exploration
* **Graph Operations** — Chainable API for data transformations
* **Recipes & Workflows** — Ready-to-use solutions for common tasks
* **Case Studies** — Complete end-to-end analyses

How to Use
----------

**Learning:** Read chapters in order—each builds on previous concepts.

**Reference:** Use the Recipes & Workflows chapter for specific solutions.

**Expertise:** Case Studies show how to approach real problems.

Start with :doc:`networks` for fundamental operations.
