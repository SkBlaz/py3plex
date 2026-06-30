Appendix A: Repository Layout and Scripts
==========================================

This appendix is a compact navigation map, not a full manual.

Repository Map (Condensed)
--------------------------

.. code-block:: text

    py3plex/
    ├── py3plex/      # Main package (core, algorithms, dsl, algebra, embeddings, io, ...)
    ├── tests/        # Automated validation and regression checks
    ├── examples/     # Runnable examples by topic
    ├── book/         # This manuscript source
    ├── docfiles/     # Sphinx documentation source
    ├── gui/          # Experimental web interface
    ├── pyproject.toml
    └── Makefile

The main package is organized around analytical concerns: representation
(``core/``), inference (``algorithms/`` and ``centrality/``), query workflows
(``dsl/``), simulation (``dynamics/``), data interchange (``io/`` and
``out_of_core/``), algebraic path/query machinery (``algebra/`` and
``semiring/``), embeddings (``embeddings/`` and ``ml/embedding/``), experiment
tracking (``experiments/``), meta-analysis (``meta/``), and cost/planning
support (``optimizer/`` and ``dsl/program/``).

Current Package Landmarks
-------------------------

Use this list to orient yourself when the book discusses newer repository
capabilities:

``py3plex/algebra`` and ``py3plex/semiring``
 Semiring-style path, closure, fixed-point, and witness utilities.

``py3plex/embeddings`` and ``py3plex/ml/embedding``
 NetMF, MetaPath2Vec, Node2Vec/DeepWalk/LINE-style embedding primitives and
 shared embedding utilities.

``py3plex/dsl/lint`` and ``py3plex/dsl/program``
 Static query diagnostics plus first-class ``GraphProgram`` objects for typed,
 rewritable, cost-aware DSL workflows.

``py3plex/experiments`` and ``py3plex/meta``
 Filesystem-backed experiment records and meta-analytic pooling of network
 statistics across runs or datasets.

``py3plex/out_of_core`` and ``py3plex/optimizer``
 Streaming query execution over disk-resident edge data and cost-based planning
 infrastructure for larger analyses.

Chapter-to-Example Map
----------------------

:ref:`installation-chapter`
  ``examples/getting_started/`` for minimal verified runs.

:ref:`data-loading-chapter`
  ``examples/io_and_data/`` for loading and format-conversion patterns.

:ref:`algorithms-chapter`
  ``examples/network_analysis/`` for centrality, communities, and dynamics.

:ref:`dsl-chapter` and :ref:`advanced-dsl-chapter`
  ``examples/dsl_zoo/`` for DSL patterns and reusable snippets.

:ref:`advanced-dsl-chapter`
  ``examples/advanced/example_graph_program.py`` and
  ``examples/advanced/example_rewrite_engine.py`` for program/rewrite examples;
  ``examples/out_of_core/`` for streaming query examples.

:ref:`algorithms-chapter`
  ``examples/advanced/example_metapath2vec.py`` and related embedding examples
  for the current embedding surface.

:ref:`gui-chapter`
  ``gui/`` for local GUI setup and interaction flow.

Where to Start to Reproduce Book Examples
-----------------------------------------

1. Create a clean environment and run the chapter-5 smoke test first.
2. Start with ``examples/getting_started/`` and then open the chapter-mapped folders above.
3. Use one case-study script at a time, keeping seeds and output paths explicit.
4. Record version, commit, and query/provenance metadata alongside outputs.

Key Commands (Minimal)
----------------------

.. code-block:: bash

    make setup
    make dev-install
    make test
    make docs

These commands cover most local reproduction workflows; deployment-heavy details are intentionally moved to Appendix B and repository docs.
