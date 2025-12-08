Roadmap & Vision
================

This page outlines the vision and planned development for py3plex. For the latest updates, see `GitHub Releases <https://github.com/SkBlaz/py3plex/releases>`_ and `GitHub Issues <https://github.com/SkBlaz/py3plex/issues>`_.

Long-Term Vision
----------------

py3plex aims to be the go-to Python library for multilayer network analysis with a focus on:

**Research Goals:**

* Implementing state-of-the-art multilayer network algorithms from research literature
* Providing a flexible framework for developing new multilayer methods
* Supporting reproducible research with comprehensive documentation and examples

**Production Use Cases:**

* Enabling analysis of real-world multilayer networks at scale
* Providing robust APIs for integration into production systems
* Supporting diverse data formats and interoperability with existing tools

**Community Building:**

* Growing an active community of researchers and practitioners
* Facilitating collaboration through open-source development
* Providing educational resources and workshops

Current Focus (v1.0+)
---------------------

**Established Features:**

* Core multilayer network data structures and operations
* DSL (Domain-Specific Language) for declarative network queries
* Community detection algorithms (Louvain, Infomap, multilayer variants)
* Dynamics simulation (SIR, SIS, random walks, custom models)
* Network embeddings (Node2Vec, DeepWalk)
* Centrality measures (degree, betweenness, PageRank, multilayer variants)
* First-class uncertainty quantification
* Visualization tools (matplotlib, plotly, interactive)
* CLI tools for common operations
* Web GUI for interactive exploration

Planned Enhancements
--------------------

**Priority areas for future development:**

Near Term (Next Release)
~~~~~~~~~~~~~~~~~~~~~~~~~

* Performance optimizations for large-scale networks (>1M nodes)
* Additional temporal network analysis tools
* Extended DSL capabilities (aggregation, window functions)
* More community detection algorithms
* Enhanced visualization options (layer-specific layouts)

Medium Term (1-2 Releases)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* GPU acceleration for select algorithms
* Streaming network analysis capabilities
* Advanced temporal dynamics models
* Integration with graph database systems
* Additional export formats (Neo4j, GraphML extensions)
* More comprehensive benchmarking suite

Longer Term (Future Releases)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Distributed computing support (Dask, Spark integration)
* Advanced machine learning on multilayer networks
* Causal inference tools for multilayer systems
* Time-varying parameter estimation
* Additional domain-specific toolkits (bioinformatics, social, transport)

**Note:** Feature priorities may shift based on community feedback and research developments. Track specific feature requests and vote on priorities through `GitHub Issues <https://github.com/SkBlaz/py3plex/issues>`_.

Research Directions
-------------------

py3plex development is informed by ongoing research in multilayer network science:

**Current Research Areas:**

* **Multilayer centrality:** Novel measures that account for layer dependencies
* **Temporal dynamics:** Time-varying multilayer processes and intervention modeling
* **Uncertainty quantification:** Principled handling of measurement error and structural uncertainty
* **Scalability:** Algorithms that scale to networks with millions of nodes and layers
* **Domain applications:** Collaborations in biology, social science, transportation, finance

**Contributing Research:**

If you're developing new multilayer network methods, we welcome contributions! See :doc:`contributing` for guidelines on:

* Implementing new algorithms
* Adding test cases and benchmarks
* Contributing examples and documentation
* Citing your research in the codebase

Community Requests
------------------

The following features have been requested by the community. For the full list and to vote on priorities, see `GitHub Issues <https://github.com/SkBlaz/py3plex/issues>`_.

**High-Priority Requests:**

* Support for very large networks (>10M nodes) - **In progress**
* Additional temporal network analysis tools - **Planned**
* More extensive documentation and tutorials - **Ongoing**
* Enhanced performance for centrality computations - **Planned**
* Integration with popular graph databases - **Under consideration**

Vote on Features
~~~~~~~~~~~~~~~~

Help prioritize development by:

* Commenting on existing feature request issues with your use case
* Opening new issues for feature requests (use the "enhancement" label)
* Using 👍 reactions to vote on priorities
* Contributing implementations for features you need

Contributing to Development
----------------------------

Want to help implement these features? We welcome contributions of all kinds:

* **Code contributions:** Implement new algorithms, fix bugs, improve performance
* **Documentation:** Write tutorials, improve API docs, add examples
* **Testing:** Add test cases, report bugs, validate algorithms
* **Community:** Answer questions, review PRs, organize workshops

See :doc:`contributing` for detailed guidelines.

Release Cycle
-------------

py3plex follows semantic versioning (MAJOR.MINOR.PATCH):

**Version Scheme:**

* **Major releases** (x.0.0): Breaking API changes, major new features
* **Minor releases** (1.x.0): New features, backward-compatible changes
* **Patch releases** (1.0.x): Bug fixes, documentation updates

**Development Process:**

* **Main branch:** Stable, production-ready code
* **Development branches:** Feature development and testing
* **Release candidates:** Beta testing before major releases
* **Documentation:** Updated with each release

**Release Timeline:**

* Major releases: ~1-2 per year
* Minor releases: As features are completed (typically quarterly)
* Patch releases: As needed for bug fixes

See :doc:`changelog` for release history.

Staying Updated
---------------

* **GitHub Releases:** https://github.com/SkBlaz/py3plex/releases
* **Issue Tracker:** https://github.com/SkBlaz/py3plex/issues
* **Discussions:** https://github.com/SkBlaz/py3plex/discussions

Next Steps
----------

* **Current features:** :doc:`../getting_started/tutorial_10min`
* **Contribute:** :doc:`contributing`
* **Report issues:** https://github.com/SkBlaz/py3plex/issues

