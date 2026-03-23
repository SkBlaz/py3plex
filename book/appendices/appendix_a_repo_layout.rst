Appendix A: Repository Layout and Scripts
==========================================

This appendix is a compact navigation map, not a full manual.

Repository Map (Condensed)
--------------------------

.. code-block:: text

    py3plex/
    ├── py3plex/      # Main package (core, algorithms, dsl, io, visualization, dynamics)
    ├── tests/        # Automated validation and regression checks
    ├── examples/     # Runnable examples by topic
    ├── book/         # This manuscript source
    ├── docfiles/     # Sphinx documentation source
    ├── gui/          # Experimental web interface
    ├── pyproject.toml
    └── Makefile

The main package is organized around analytical concerns: representation (`core/`), inference (`algorithms/`), query workflows (`dsl/`), simulation (`dynamics/`), and data interchange (`io/`).

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
