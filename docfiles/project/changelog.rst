Changelog
=========

This page summarizes the release history of py3plex. For granular, date-stamped entries, see `GitHub Releases <https://github.com/SkBlaz/py3plex/releases>`_.

Release History
---------------

Version 1.0.0 (Current)
~~~~~~~~~~~~~~~~~~~~~~~

**Release Date:** 2024 (current stable line)

The 1.0 series focuses on a stable DSL, multilayer ergonomics, and reproducible analysis workflows.

**Major Features:**

* **DSL Query Language:** SQL-like domain-specific language for querying multilayer networks
  
  * String syntax (``execute_query``) for simple queries
  * Builder API (``Q.nodes()``, ``Q.edges()``) for complex, chainable queries
  * Layer algebra (``L[layer]``, ``L.intersection()``, ``L.union()``)
  * Comprehensive filter, compute, and aggregation operations

* **First-Class Uncertainty Quantification:**
  
  * ``StatSeries`` and ``StatMatrix`` types for statistics with uncertainty
  * Resampling methods (SEED, PERTURBATION) for error propagation
  * Backward-compatible with existing code expecting scalars
  * Integrated across centrality, community detection, and dynamics modules

* **Temporal Network Support:**
  
  * Time-stamped edges and temporal queries
  * Snapshot-based analysis
  * Temporal dynamics simulation

* **Enhanced Dynamics Framework:**
  
  * Refactored dynamics API with consistent interface
  * SIR, SIS, and custom dynamics models
  * Layer-specific and time-varying parameters
  * Comprehensive result objects with measure extraction

* **Community Detection Improvements:**
  
  * Multilayer Louvain with inter-layer coupling
  * Infomap integration (with external binary)
  * Layer-specific community detection workflows
  * Community comparison and stability analysis

* **Web GUI:**
  
  * Interactive network exploration (FastAPI + SvelteKit)
  * Real-time visualization and query interface
  * REST API for programmatic access

* **CLI Tools:**
  
  * ``py3plex`` command-line interface
  * Community detection, statistics, DSL linting
  * Network conversion and export utilities

* **Documentation Overhaul:**
  
  * Comprehensive how-to guides
  * Conceptual documentation
  * API reference with examples
  * Tutorial notebooks

* **Testing & Quality:**
  
  * 500+ unit and integration tests
  * Continuous integration (CI/CD)
  * Type hints throughout codebase
  * Code coverage tracking

**API Changes:**

* Standardized function signatures across modules
* Consistent parameter naming (``gamma`` for resolution, ``omega`` for coupling)
* Deprecated legacy APIs (warnings emitted, will be removed in 2.0)

**Performance Improvements:**

* Optimized tensor operations for multilayer algebra
* Sparse matrix support for large networks
* Caching for expensive computations (centrality, community detection)

**Bug Fixes:**

* Numerous edge-case fixes in community detection
* Corrected centrality calculations for directed multilayer networks
* Fixed memory leaks in long-running dynamics simulations
* Resolved NetworkX compatibility issues (version pinning and adapters)

Previous Versions (0.x Series)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The 0.x series delivered the multilayer foundations: data structures, early DSL prototypes, and visualization primitives. Expect minor API inconsistencies compared to 1.0; migrate when possible.

**Version 0.30 - 0.35 (2020-2023)**

* Incremental feature additions
* Experimental DSL prototype
* Initial dynamics framework
* Community detection algorithms

**Version 0.20 - 0.29 (2018-2020)**

* Multilayer centrality measures
* Visualization improvements
* NetworkX integration

**Version 0.10 - 0.19 (2016-2018)**

* Initial public release
* Core multilayer network data structures
* Basic algorithms (degree, clustering)
* Example notebooks

**Version 0.1 - 0.9 (2014-2016)**

* Research prototype
* Proof-of-concept implementations
* Academic collaborations

How to Check Your Version
--------------------------

Confirm the installed package version from Python (or use ``pip show py3plex`` in the shell):

.. code-block:: python

    import py3plex
    print(py3plex.__version__)

**Expected output:**

.. code-block:: text

    1.0.0

Upgrade Instructions
--------------------

**Upgrade to latest stable release:**

.. code-block:: bash

    pip install --upgrade py3plex

**Install a specific version:**

.. code-block:: bash

    pip install py3plex==1.0.0

**Install development snapshot:**

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git@main

Migration Guides
----------------

Migrating from 0.x to 1.0
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Breaking Changes:**

1. **Network construction API:**
   
   * Old: ``network.add_nodes(node_list)``
   * New: ``network.add_nodes([('node', 'layer'), ...])`` (explicit tuples)

2. **Community detection returns:**
   
   * Old: ``louvain_communities()`` returned dict with node IDs as keys
   * New: Returns dict with ``(node, layer)`` tuples as keys

3. **Centrality functions:**
   
   * Old: Scalar returns
   * New: Can return ``StatSeries`` when ``uncertainty=True``
   * Backward compatible: Use ``result.mean`` or ``np.array(result)``

**Deprecated APIs (still work but emit warnings):**

* ``network.get_nodes_by_layer(layer)`` → Use DSL: ``Q.nodes().from_layers(L[layer])``
* ``network.get_layer_edges(layer)`` → Use DSL: ``Q.edges().from_layers(L[layer])``
* ``compute_centrality(network, measure)`` → Use DSL: ``Q.nodes().compute(measure)``

**New Recommended Patterns:**

.. code-block:: python

    # Old way (still works)
    nodes = network.get_nodes_by_layer('layer1')
    for node in nodes:
        degree = network.core_network.degree(node)
    
    # New DSL way (recommended)
    from py3plex.dsl import Q, L
    result = (
        Q.nodes()
         .from_layers(L['layer1'])
         .compute("degree")
         .execute(network)
    )

**Migration Steps:**

1. Update py3plex: ``pip install --upgrade py3plex``
2. Run your existing code; deprecation warnings will indicate legacy usage
3. Gradually migrate to DSL for queries and layer selection
4. Update community detection code to expect tuple ``(node, layer)`` keys
5. Handle uncertainty-aware results if using ``uncertainty=True`` (e.g., use ``result.mean``)
6. Re-run tests or notebooks to confirm parity before removing legacy patterns

API Changes and Deprecations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use this section to triage warnings during upgrades; deprecated items will be removed in 2.0 unless noted otherwise.

**Removed in 1.0:**

* ``old_louvain_function()`` - replaced by ``louvain_communities()``
* ``legacy_centrality_wrapper()`` - use centrality functions directly

**Deprecated (warnings only, will be removed in 2.0):**

* Direct core_network manipulation - use DSL or network methods
* Legacy node/edge addition formats - use dict or tuple formats

**Renamed:**

* ``multinet.multi_layer_network()`` - unchanged (primary API)
* ``execute_dsl_query()`` → ``execute_query()`` (alias still works)

Contributing to Changelog
--------------------------

When submitting PRs, mirror major notes here if they affect users:

* Brief description of changes
* Link to issue (if applicable)
* Breaking changes clearly marked
* Migration notes for API changes

See :doc:`contributing` for details.

Staying Updated
---------------

* **GitHub Releases:** https://github.com/SkBlaz/py3plex/releases
* **PyPI:** https://pypi.org/project/py3plex/
* **Discussions:** https://github.com/SkBlaz/py3plex/discussions

Next Steps
----------

* **Upgrade guide:** See "Migration Guides" above
* **What's new:** :doc:`roadmap` for planned features
* **Report issues:** https://github.com/SkBlaz/py3plex/issues
