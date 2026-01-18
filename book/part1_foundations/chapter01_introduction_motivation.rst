Introduction & Motivation
====================================

Why Multilayer Networks?
-------------------------

Real-world systems rarely consist of a single type of relationship. Consider:

* **Social networks:** People interact through friendship, collaboration, family ties, and online connections—each relationship type has different meanings and dynamics.
* **Transportation systems:** Cities connect via air, rail, and road networks. A disruption in one mode affects the others, and travelers make choices across modes.
* **Biological systems:** Proteins interact through physical binding, regulatory relationships, and metabolic pathways—each layer represents a different mechanism.
* **Information systems:** Software components depend on each other through API calls, data flows, and deployment relationships.

Traditional single-layer (monoplex) networks flatten these diverse relationships into a single graph, losing critical structural information. **Multilayer networks** preserve the distinct nature of different relationship types by organizing them into separate but interconnected layers.

The Cost of Flattening
~~~~~~~~~~~~~~~~~~~~~~

When we flatten a multilayer network into a single graph, we lose:

1. **Relationship semantics:** A coauthor edge is fundamentally different from a Twitter follower edge, but flattening treats them identically.

2. **Community structure:** Groups that are well-separated in individual layers may appear spuriously connected when layers are combined.

3. **Node roles:** A person might be central in their professional network but peripheral in their hobby network—this context-dependent centrality disappears upon flattening.

4. **Cross-layer dynamics:** Information spreading from email to in-person meetings follows specific patterns that become invisible when layers are merged.

**Example:** Consider a researcher with 2 coauthors and 500 Twitter followers. In a flattened network, they have degree 502, suggesting high influence. However, their actual academic impact is modest (degree 2 in the coauthor layer). The Twitter followers don't collaborate on research papers. Multilayer analysis preserves this critical distinction between different types of influence.

What py3plex Enables
--------------------

**py3plex** is a Python library designed for practical analysis of multilayer networks. It provides:

**1. Expressive Data Structures**

Native support for multilayer network representations that mirror how real systems are naturally structured:

.. code-block:: python

    from py3plex.core import multinet
    
    # Create a multilayer network
    network = multinet.multi_layer_network()
    
    # Add edges across multiple layers
    network.add_edges([
        ['Alice', 'coauthor', 'Bob', 'coauthor', 1],
        ['Alice', 'twitter', 'Carol', 'twitter', 1],
        ['Bob', 'coauthor', 'Dave', 'coauthor', 1],
    ], input_type="list")

**2. Multilayer-Aware Algorithms**

Algorithms specifically designed for multilayer structure:

* **Community detection** that respects layer boundaries while finding cross-layer modules
* **Centrality measures** that account for both intra-layer and inter-layer importance
* **Random walks** that can transition between layers
* **Dynamics models** (e.g., epidemic spreading) with layer-specific parameters

**3. A Query Language for Networks**

A SQL-like DSL (Domain-Specific Language) for expressing complex network analyses concisely:

.. admonition:: DSL Example: Concise Network Analysis
   :class: dsl-example

   Instead of writing loops and conditions, use declarative queries:

   .. code-block:: python

       from py3plex.dsl import Q, L

       # Find high-degree nodes in the coauthor layer
       result = (
           Q.nodes()
            .from_layers(L["coauthor"])
            .where(degree__gt=5)
            .compute("betweenness_centrality", "pagerank")
            .order_by("-betweenness_centrality")
            .limit(10)
            .execute(network)
       )

       # Export for further analysis
       result.to_pandas().to_csv("top_researchers.csv")

   This replaces dozens of lines of manual filtering and iteration with a clear, composable query.

   **Key DSL features:**
   
   * SQL-like syntax familiar to data analysts
   * Layer algebra: ``L["social"] + L["work"] - L["bots"]``
   * Type-safe Python builder API
   * Export to pandas, NetworkX, Arrow, CSV, JSON
   * EXPLAIN mode for query optimization

**4. Visualization for Multilayer Networks**

Publication-ready visualizations that show layer structure and cross-layer connections:

.. code-block:: python

    # Visualize with layer separation
    network.visualize_network(
        show=True,
        layout_style="force_directed_3d"
    )

**5. Production-Ready Infrastructure**

* **High-performance I/O** with Arrow/Parquet support for large networks
* **NetworkX compatibility** for interoperability with the broader Python ecosystem
* **Testing and validation** frameworks to ensure correctness
* **Docker containers** and CLI tools for deployment

Who Should Use This Book
-------------------------

This book is designed for:

**Graduate Students and Researchers**

If you're analyzing social, biological, or infrastructure networks in your research, this book provides both theoretical foundations and practical tools. You'll learn when multilayer modeling is appropriate and how to apply specialized algorithms correctly.

**Data Scientists and Analysts**

If you're working with complex relational data—user behavior across platforms, supply chain networks, knowledge graphs—py3plex offers a principled way to preserve and analyze structural nuances.

**Software Engineers**

If you're building network analysis pipelines, this book shows how to use py3plex's APIs, DSL, and deployment tools to create maintainable, efficient systems.

Prerequisites
~~~~~~~~~~~~~

This book assumes:

* **Intermediate Python** (classes, list comprehensions, basic NumPy)
* **Basic graph theory** (nodes, edges, paths, degree)
* **Fundamental linear algebra** (matrices, matrix multiplication)

You don't need prior multilayer network experience—Part I builds from fundamentals.

Real-World Applications
-----------------------

Multilayer network analysis has proven valuable in numerous domains:

**Biological Networks**
  * Protein-protein interactions across multiple tissues or conditions
  * Gene regulatory networks with transcription, translation, and metabolic layers
  * Brain connectivity with structural and functional layers

**Social Networks**
  * User behavior across multiple social platforms
  * Organizational networks with formal and informal relationships
  * Citation networks with papers, authors, and venues

**Infrastructure Networks**
  * Transportation with air, rail, and road connections
  * Power grids with generation, transmission, and distribution layers
  * Communication networks with physical and logical layers

**Knowledge and Information**
  * Heterogeneous information networks (authors-papers-venues)
  * Semantic networks with multiple relationship types
  * Code dependency graphs with API, data, and deployment layers

Each of these applications benefits from multilayer analysis by capturing the true structure of the system rather than forcing it into a single-layer representation.

How This Book Is Organized
--------------------------

**Part I (Chapters 1-3): Foundations**
  Introduces multilayer networks, defines key concepts, and explains py3plex's design philosophy.

**Part II (Chapters 4-7): Working with Py3plex**
  Covers installation, data loading, visualization, and core algorithms—everything needed for basic usage.

**Part III (Chapters 8-11): Advanced Analysis and the DSL**
  Deep dive into the query language, a major feature for expressing complex analyses concisely.

**Part IV (Chapters 12-14): Case Studies**
  Complete, reproducible analyses of real datasets across different domains.

**Part V (Chapters 15-17): Systems and Deployment**
  Testing, reproducibility, and production deployment including the web GUI.

**Appendices (A-E): Reference Material**
  Detailed configurations, validation scripts, error handling, and API reference.

Each chapter includes:

* **Conceptual explanations** with mathematical foundations where needed
* **Code examples** that are runnable and tested
* **Practical tips** based on real usage patterns
* **References** for deeper study

Summary
-------

Multilayer networks provide a natural and expressive way to model systems with multiple types of relationships. By preserving the distinct nature of different layers, we can:

* Analyze structure more accurately
* Compute meaningful centralities and communities
* Model dynamics more realistically
* Make better predictions and interventions

**py3plex** makes multilayer network analysis accessible and practical, with a focus on:

* Expressive data structures
* Specialized algorithms
* A powerful query language
* Production-ready tools

The following chapters will show you how to use these capabilities effectively.

Further Reading
---------------

* Kivelä, M., et al. (2014). "Multilayer networks." *Journal of Complex Networks* 2(3): 203-271. [Comprehensive review of multilayer network theory]
* Boccaletti, S., et al. (2014). "The structure and dynamics of multilayer networks." *Physics Reports* 544(1): 1-122. [Physics-focused perspective]
* Bianconi, G. (2018). *Multilayer Networks: Structure and Function.* Oxford University Press. [Textbook treatment]
