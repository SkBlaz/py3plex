Chapter 7: Core Algorithms: Communities, Centrality, Dynamics
=============================================================

*TODO: This chapter consolidates algorithm documentation from multiple sources*

Overview
--------

[Introduce three major algorithm families for multilayer analysis]

Community Detection
-------------------

Multilayer Modularity
~~~~~~~~~~~~~~~~~~~~~

[Mathematical definition and implementation]

.. code-block:: python

    from py3plex.algorithms.community_detection import multilayer_louvain
    
    # Detect communities
    communities = multilayer_louvain.best_partition(network.core_network)

Algorithms Available
~~~~~~~~~~~~~~~~~~~~

[Louvain, Infomap, Label Propagation]

**Complexity:** O(n log n) for most algorithms

Choosing a Community Detection Method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[Guidelines based on network size, structure, and goals]

Centrality Measures
-------------------

Multilayer PageRank
~~~~~~~~~~~~~~~~~~~

[Random walk-based centrality]

Degree Centrality
~~~~~~~~~~~~~~~~~

[Intra-layer vs inter-layer degree]

Betweenness Centrality
~~~~~~~~~~~~~~~~~~~~~~~

[Path-based importance]

Explainable Centrality
~~~~~~~~~~~~~~~~~~~~~~

[Breaking down centrality scores by layer]

.. code-block:: python

    from py3plex.algorithms.centrality.explain import explain_node_centrality
    
    # Get layer-wise breakdown
    explanation = explain_node_centrality(network, 'Alice', measure='degree')

Dynamics and Processes
-----------------------

Random Walks
~~~~~~~~~~~~

[Node2Vec, DeepWalk for embeddings]

Epidemic Models
~~~~~~~~~~~~~~~

[SIS, SIR, SEIR models]

.. code-block:: python

    from py3plex.dynamics.models import SIRDynamics
    
    # Configure epidemic model
    sir = SIRDynamics(network, beta=0.3, gamma=0.1)
    sir.set_seed(42)
    results = sir.run(steps=100)

Diffusion Processes
~~~~~~~~~~~~~~~~~~~

[Information spreading, cascades]

Algorithm Complexity and Scaling
---------------------------------

[Performance characteristics, memory requirements, when to use each]

Summary
-------

[Recap of algorithm families and when to use each]

**Next chapter:** Introduction to the py3plex DSL

*Source files to integrate:*
- docfiles/user_guide/community_detection.rst
- docfiles/user_guide/statistics.rst
- docfiles/tutorials/multilayer_centrality.rst
- docfiles/tutorials/explainable_centrality.rst
- docfiles/sir_epidemic_simulator.rst
- DYNAMICS_IMPLEMENTATION.md
- docfiles/multilayer_centrality_matrix_functions.rst
- docfiles/ricci_curvature.rst
