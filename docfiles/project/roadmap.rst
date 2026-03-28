Roadmap & Vision
================

This page outlines the vision and planned development for py3plex. Roadmaps are snapshots and may shift with user feedback. For the latest updates, see `GitHub Releases <https://github.com/SkBlaz/py3plex/releases>`_ and `GitHub Issues <https://github.com/SkBlaz/py3plex/issues>`_.

Long-Term Vision
----------------

py3plex aims to be the go-to Python library for multilayer network analysis with a focus on:

**Research Goals:**

* Implementing state-of-the-art multilayer network algorithms from current research
* Providing a flexible framework for developing and comparing new multilayer methods
* Supporting reproducible research with clear documentation and runnable examples

**Production Use Cases:**

* Enabling analysis of real-world multilayer networks at scale (millions of nodes)
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
* Community detection (Louvain, Infomap, multilayer variants)
* Dynamics simulation (SIR, SIS, random walks, custom models)
* Network embeddings (Node2Vec, DeepWalk)
* Centrality measures (degree, betweenness, PageRank, multilayer variants)
* Uncertainty quantification utilities
* Visualization tools (matplotlib, plotly, interactive)
* CLI tools for common operations and a web GUI for exploration

Planned Enhancements
--------------------

Planned work is grouped by expected timeframe. Items may move as priorities change.

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

Documentation Gaps Blocking New-User Adoption
---------------------------------------------

After reviewing ``README.md``, ``AGENTS.md``, and the current docs tree, these are the highest-impact documentation gaps for first-time users:

1. **Conflicting example inventory and scale claims**

   * README says **170+** examples.
   * ``AGENTS.md`` says **267** examples.
   * ``docfiles/getting_started/tutorial_10min.rst`` says **26 focused examples** in its section list.

   New users cannot quickly trust which navigation map is current.

2. **Broken or stale example path references in onboarding docs**

   Several onboarding pages reference example folders that are not present in the current top-level ``examples/`` layout (for example ``examples/00_quickstart/`` and category folders such as ``communities/`` and ``temporal/``). This blocks copy-paste adoption because the first command often fails with "file not found".

3. **No single canonical "start here" path across README and docs**

   README, docs homepage, and tutorial pages each present different starting flows. The project has strong content depth, but first-time users lack one authoritative linear path from install -> first successful query -> next steps.

4. **README flagship snippet is advanced before a minimal validated success case**

   The first large code sample is feature-rich (community detection + UQ + grouping + explainability), which is valuable for power users but can overwhelm new adopters who need a shortest possible "first success" script first.

5. **Audience boundary between AGENTS.md and human docs is unclear**

   ``AGENTS.md`` is comprehensive and agent-oriented, but there is no prominent warning in beginner-facing docs clarifying that it is an expert/automation playbook rather than the recommended first learning resource for humans.

6. **No documented single source of truth for doc metadata drift-prone fields**

   Counts and path catalogs (examples totals, folder maps, quickstart file paths) are repeated in multiple places without a clearly designated canonical source, causing recurring drift.

Vote on Features
~~~~~~~~~~~~~~~~

Help prioritize development by:

* Commenting on existing feature request issues with your use case
* Opening new issues for feature requests (use the "enhancement" label)
* Using  reactions to vote on priorities
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
