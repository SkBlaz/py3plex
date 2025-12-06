Front Matter
============

About This Book
---------------

**Practical Multilayer Network Analysis with Py3plex** is a research-oriented handbook for graduate students and applied network scientists. It provides both theoretical foundations and practical guidance for analyzing complex systems using multilayer network representations.

This book covers:

* Mathematical foundations of multilayer networks
* The py3plex library architecture and design philosophy
* Hands-on examples and workflows for real network analysis
* A powerful SQL-like DSL for network queries
* Production deployment and reproducibility practices

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

**py3plex** (version 1.x) is an open-source Python library for multilayer and multiplex network analysis. It provides:

* Native support for multilayer network structures
* 17+ specialized algorithms for multilayer analysis
* A SQL-like query language (DSL) for network exploration
* NetworkX compatibility and interoperability
* High-performance I/O with Arrow/Parquet support

The library is actively maintained and tested on Python 3.8+.

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

All code examples in this book are runnable and tested. Examples use consistent naming and follow modern Python conventions. File paths reference the accompanying GitHub repository:

    https://github.com/SkBlaz/py3plex

Conventions
~~~~~~~~~~~

* **Code blocks** use syntax highlighting and are self-contained
* **Mathematical notation** follows standard network science conventions
* **Feature status** is clearly marked:
  
  * **Stable** - Production-ready with guarantees
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

Version Information
-------------------

* **Book version:** 1.0 (2025)
* **py3plex version:** 1.x
* **Python support:** 3.8+

