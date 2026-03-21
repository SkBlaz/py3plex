Front Matter
============

About This Book
---------------

**Practical Multilayer Network Analysis with Py3plex** is a research-oriented handbook for graduate students and applied network scientists. It provides both theoretical foundations and practical guidance for analyzing complex systems using multilayer network representations.

This book covers:

* Mathematical foundations of multilayer networks
* The py3plex library architecture and design philosophy
* Hands-on examples and workflows for real network analysis
* A SQL-like DSL for network queries
* Production deployment and reproducibility practices

.. admonition:: DSL Feature Highlight
   :class: dsl-example

   Py3plex includes a first-class DSL for querying networks with SQL-like syntax:

   .. code-block:: python

       from py3plex.dsl import Q, L

       # Find top influencers using builder API
       result = (
           Q.nodes()
            .from_layers(L["social"])
            .where(degree__gt=5)
            .compute("betweenness_centrality")
            .order_by("-betweenness_centrality")
            .limit(10)
            .execute(network)
       )

   See **Part III** for complete DSL coverage!

Target Audience
---------------

This book is designed for:

* **Graduate students** in network science, computer science, and related fields
* **Applied researchers** working with complex relational data
* **Data scientists** analyzing social, biological, or infrastructure networks
* **Software engineers** building network analysis pipelines

Prerequisites
~~~~~~~~~~~~~

Readers should be familiar with:

* Python programming (intermediate level)
* Basic graph theory concepts
* Fundamental linear algebra

About the Software
------------------

**py3plex** (version 1.1.4) is an open-source Python library for multilayer and multiplex network analysis. It provides:

* Native support for multilayer network structures
* 17+ specialized algorithms for multilayer analysis
* A SQL-like query language (DSL) for network exploration
* NetworkX compatibility and interoperability
* High-performance I/O with Arrow/Parquet support

The library targets Python 3.8+ for runtime compatibility.

How to Use This Book
--------------------

**Part I** establishes foundations: what multilayer networks are, when to use them, and how py3plex is designed.

**Part II** teaches practical usage: installation, data loading, visualization, and running core algorithms.

**Part III** presents the DSL query language, a major feature for expressing complex analyses concisely.

**Part IV** demonstrates real-world applications through detailed case studies.

**Part V** covers systems topics: testing, reproducibility, and the web GUI.

**Appendices** provide reference material, detailed configurations, and extensive validation examples that supplement the main text.

Code Examples
~~~~~~~~~~~~~

Examples in this book are intended to be runnable in the documented environment. Compatibility may vary across platforms and project revisions, so treat outputs as representative unless a section explicitly reports validated benchmark results. File paths reference the accompanying GitHub repository:

    https://github.com/SkBlaz/py3plex

Conventions
~~~~~~~~~~~

* **Code blocks** use syntax highlighting and are self-contained
* **Mathematical notation** follows standard network science conventions
* **Feature status** is clearly marked:
  
  * **Stable** - Intended to be stable for the workflows described in this book
  * **Experimental** - Functional but may change
  * **Planned** - Future features (mentioned only briefly)

Acknowledgments
---------------

This work builds on contributions from the py3plex community and research collaborations in multilayer network analysis.

If you use py3plex in your research, please cite:

.. code-block:: bibtex

    @Article{Skrlj2019,
      author={Skrlj, Blaz and Kralj, Jan and Lavrac, Nada},
      title={Py3plex toolkit for visualization and analysis of multilayer networks},
      journal={Applied Network Science},
      year={2019},
      volume={4},
      number={1},
      pages={94},
      doi={10.1007/s41109-019-0203-7}
    }

License
-------

The py3plex library is released under the MIT License. This book's content is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).

.. note::
   **Version Information:** This book edition is version 1.1.4 (2025), aligned with py3plex 1.1.4 and Python 3.8+ runtime support.
