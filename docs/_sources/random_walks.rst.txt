Random Walk Algorithms
======================

Py3plex provides comprehensive random walk primitives for graph-based algorithms,
including Node2Vec, DeepWalk, and diffusion processes. These implementations support
weighted, directed, and multilayer networks with deterministic reproducibility.

Overview
--------

Random walks are fundamental building blocks for many graph algorithms:

- **Node2Vec**: Learn node embeddings using biased random walks
- **DeepWalk**: Generate node embeddings through uniform random walks
- **Personalized PageRank**: Compute node importance via random walks with restart
- **Diffusion processes**: Model information or disease propagation
- **Community detection**: Identify network structure through walk patterns

Key Features
~~~~~~~~~~~~

- ✅ Basic random walks with proper edge weight handling
- ✅ Second-order (biased) random walks following Node2Vec logic
- ✅ Multiple simultaneous walks with deterministic seeding
- ✅ Support for directed, weighted, and multigraphs
- ✅ Multilayer network-aware walks with layer constraints
- ✅ Efficient sparse adjacency matrix handling
- ✅ Comprehensive test suite validating correctness properties

Basic Random Walk
-----------------

The basic random walk samples the next node proportionally to normalized edge weights.

Simple Example
~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import basic_random_walk
    import networkx as nx
    
    # Create a simple graph
    G = nx.karate_club_graph()
    
    # Perform a random walk
    walk = basic_random_walk(
        G, 
        start_node=0, 
        walk_length=10,
        seed=42  # for reproducibility
    )
    
    print(f"Walk: {walk}")
    print(f"Length: {len(walk)}")  # 11 nodes (includes start)

Weighted Graphs
~~~~~~~~~~~~~~~

Edge weights are automatically used when ``weighted=True`` (default):

.. code-block:: python

    from py3plex.algorithms.general.walkers import basic_random_walk
    import networkx as nx
    
    # Create weighted graph
    G = nx.Graph()
    G.add_weighted_edges_from([
        (0, 1, 10.0),  # high weight -> more likely
        (0, 2, 1.0),   # low weight -> less likely
        (1, 2, 5.0),
    ])
    
    # Weighted walk (respects edge weights)
    walk = basic_random_walk(G, 0, walk_length=20, weighted=True, seed=42)
    
    # Unweighted walk (uniform transitions)
    walk_uniform = basic_random_walk(G, 0, walk_length=20, weighted=False, seed=42)

Directed Graphs
~~~~~~~~~~~~~~~

Directed edges are handled correctly:

.. code-block:: python

    import networkx as nx
    from py3plex.algorithms.general.walkers import basic_random_walk
    
    # Create directed graph
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (1, 2), (2, 0), (1, 3)])
    
    # Walk respects edge direction
    walk = basic_random_walk(G, 0, walk_length=10, seed=42)
    
    # Verify all transitions follow directed edges
    for i in range(len(walk) - 1):
        assert G.has_edge(walk[i], walk[i+1])

Node2Vec Biased Random Walk
----------------------------

Second-order random walks with return parameter ``p`` and in-out parameter ``q``
following the Node2Vec algorithm (Grover & Leskovec, 2016).

Parameters
~~~~~~~~~~

When transitioning from node ``t → v → x``, the probability of choosing ``x`` is biased:

- **If x == t** (return to previous): ``weight / p``
- **If x is neighbor of t** (stay close): ``weight / 1``
- **If x is not neighbor of t** (explore): ``weight / q``

**Parameter Effects:**

- **p > 1**: Less likely to return to previous node (explore forward)
- **p < 1**: More likely to return (backtrack)
- **q > 1**: Less likely to explore distant nodes (stay local, BFS-like)
- **q < 1**: More likely to explore distant nodes (venture far, DFS-like)
- **p = q = 1**: Equivalent to basic random walk

Basic Usage
~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import node2vec_walk
    import networkx as nx
    
    G = nx.karate_club_graph()
    
    # Balanced walk (p=1, q=1)
    walk_balanced = node2vec_walk(G, 0, walk_length=20, p=1.0, q=1.0, seed=42)
    
    # BFS-like walk (stay local)
    walk_bfs = node2vec_walk(G, 0, walk_length=20, p=1.0, q=2.0, seed=42)
    
    # DFS-like walk (explore outward)
    walk_dfs = node2vec_walk(G, 0, walk_length=20, p=1.0, q=0.5, seed=42)

Exploring vs Backtracking
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import node2vec_walk
    import networkx as nx
    
    # Triangle graph
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2), (2, 0)])
    
    # Low p, high q: tends to backtrack
    walk_backtrack = node2vec_walk(G, 0, walk_length=20, p=0.1, q=10.0, seed=42)
    
    # High p, low q: tends to explore outward
    walk_explore = node2vec_walk(G, 0, walk_length=20, p=10.0, q=0.1, seed=42)
    
    # Count backtracking patterns
    backtracks = sum(1 for i in range(2, len(walk_backtrack)) 
                     if walk_backtrack[i] == walk_backtrack[i-2])
    print(f"Backtracks: {backtracks}")

Multiple Walk Generation
-------------------------

Generate multiple walks efficiently with deterministic seeding.

Generate Walks from All Nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks
    import networkx as nx
    
    G = nx.karate_club_graph()
    
    # Generate 10 walks from each node
    walks = generate_walks(
        G,
        num_walks=10,
        walk_length=10,
        seed=42
    )
    
    print(f"Total walks: {len(walks)}")  # 340 (34 nodes × 10 walks)
    print(f"First walk: {walks[0]}")

Generate from Specific Nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks
    import networkx as nx
    
    G = nx.karate_club_graph()
    
    # Generate walks only from nodes 0, 1, 2
    walks = generate_walks(
        G,
        num_walks=5,
        walk_length=15,
        start_nodes=[0, 1, 2],
        seed=42
    )
    
    print(f"Total walks: {len(walks)}")  # 15 (3 nodes × 5 walks)

Node2Vec-Style Walks
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks
    import networkx as nx
    
    G = nx.karate_club_graph()
    
    # Generate biased walks with p=0.5, q=2.0
    walks = generate_walks(
        G,
        num_walks=10,
        walk_length=20,
        p=0.5,
        q=2.0,
        seed=42
    )

Edge Sequences
~~~~~~~~~~~~~~

Return walks as edge sequences instead of node sequences:

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks
    import networkx as nx
    
    G = nx.karate_club_graph()
    
    # Generate edge sequences
    edge_walks = generate_walks(
        G,
        num_walks=5,
        walk_length=10,
        return_edges=True,
        seed=42
    )
    
    # First walk is a list of edges
    print(edge_walks[0])  # [(0, 3), (3, 2), (2, 1), ...]

Multilayer Network Walks
-------------------------

Perform random walks on multilayer networks with layer constraints.

Layer-Constrained Walks
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import layer_specific_random_walk
    from py3plex.core import multinet
    
    # Create multilayer network
    network = multinet.multi_layer_network()
    network.add_layer("social")
    network.add_layer("biological")
    
    network.add_nodes([
        ("A", "social"), ("B", "social"), ("C", "social"),
        ("A", "biological"), ("B", "biological")
    ])
    
    network.add_edges([
        (("A", "social"), ("B", "social")),
        (("B", "social"), ("C", "social")),
        (("A", "biological"), ("B", "biological")),
    ])
    
    # Walk constrained to social layer
    walk = layer_specific_random_walk(
        network.core_network,
        start_node="A---social",
        walk_length=10,
        layer="social",
        cross_layer_prob=0.0,  # never cross layers
        seed=42
    )
    
    # All nodes in walk are in social layer
    print(walk)

Cross-Layer Transitions
~~~~~~~~~~~~~~~~~~~~~~~

Allow occasional transitions between layers:

.. code-block:: python

    from py3plex.algorithms.general.walkers import layer_specific_random_walk
    
    # Same network as above
    
    # Walk with 10% probability of crossing layers
    walk = layer_specific_random_walk(
        network.core_network,
        start_node="A---social",
        walk_length=20,
        layer="social",
        cross_layer_prob=0.1,  # 10% chance to cross
        seed=42
    )
    
    # May contain nodes from both layers
    print(walk)

Reproducibility
---------------

All walk functions support deterministic seeding for reproducibility.

Fixed Seed
~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import basic_random_walk
    import networkx as nx
    
    G = nx.karate_club_graph()
    
    # Same seed produces identical walks
    walk1 = basic_random_walk(G, 0, 50, seed=42)
    walk2 = basic_random_walk(G, 0, 50, seed=42)
    
    assert walk1 == walk2  # Identical

Different Seeds
~~~~~~~~~~~~~~~

.. code-block:: python

    # Different seeds produce different walks
    walk1 = basic_random_walk(G, 0, 50, seed=42)
    walk2 = basic_random_walk(G, 0, 50, seed=123)
    
    assert walk1 != walk2  # Different

Batch Reproducibility
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks
    
    G = nx.karate_club_graph()
    
    # Same seed produces identical walk sets
    walks1 = generate_walks(G, num_walks=100, walk_length=10, seed=42)
    walks2 = generate_walks(G, num_walks=100, walk_length=10, seed=42)
    
    assert walks1 == walks2

Performance Tips
----------------

Large Graphs
~~~~~~~~~~~~

For large sparse graphs (>100k nodes), use basic walks for better performance:

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks
    import networkx as nx
    
    # Large sparse graph
    G = nx.erdos_renyi_graph(100000, 0.0001, seed=42)
    
    # Use basic walk (p=1, q=1) for speed
    walks = generate_walks(
        G,
        num_walks=10,
        walk_length=100,
        p=1.0,  # No bias = faster
        q=1.0,
        seed=42
    )

Parallel Processing
~~~~~~~~~~~~~~~~~~~

For generating many walks, consider parallel processing:

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks
    import networkx as nx
    from multiprocessing import Pool
    
    G = nx.karate_club_graph()
    
    def generate_batch(seed):
        return generate_walks(G, num_walks=10, walk_length=20, seed=seed)
    
    # Generate walks in parallel
    with Pool(4) as pool:
        batch_walks = pool.map(generate_batch, range(10))
    
    # Flatten results
    all_walks = [walk for batch in batch_walks for walk in batch]

Correctness Validation
----------------------

The implementation has been validated against the following properties:

Uniformity Test
~~~~~~~~~~~~~~~

On unweighted regular graphs, transition probabilities are uniform:

.. code-block:: python

    import networkx as nx
    from py3plex.algorithms.general.walkers import basic_random_walk
    from collections import Counter
    
    # Complete graph (regular)
    G = nx.complete_graph(10)
    
    # Count visits to neighbors from node 0
    visits = Counter()
    for i in range(10000):
        walk = basic_random_walk(G, 0, 1, weighted=False, seed=i)
        if len(walk) > 1:
            visits[walk[1]] += 1
    
    # All neighbors should be visited roughly equally
    print(visits)
    # Expected: ~1111 visits to each of 9 neighbors

Conservation Test
~~~~~~~~~~~~~~~~~

Sum of transition probabilities equals 1.0 (within machine epsilon):

.. code-block:: python

    import networkx as nx
    import numpy as np
    
    G = nx.karate_club_graph()
    
    # For each node, verify probability conservation
    for node in G.nodes():
        neighbors = list(G.neighbors(node))
        if len(neighbors) > 0:
            weights = np.array([G[node][n].get('weight', 1.0) for n in neighbors])
            probs = weights / weights.sum()
            assert abs(probs.sum() - 1.0) < 1e-10  # Machine epsilon

Bias Consistency Test
~~~~~~~~~~~~~~~~~~~~~

Node2Vec parameters p and q produce expected biases:

.. code-block:: python

    import networkx as nx
    from py3plex.algorithms.general.walkers import node2vec_walk
    
    # Triangle graph
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2), (2, 0)])
    
    # Low p should encourage backtracking
    backtracks_low_p = 0
    for i in range(1000):
        walk = node2vec_walk(G, 0, 10, p=0.1, q=1.0, seed=i)
        for j in range(2, len(walk)):
            if walk[j] == walk[j-2]:
                backtracks_low_p += 1
    
    # High p should discourage backtracking
    backtracks_high_p = 0
    for i in range(1000):
        walk = node2vec_walk(G, 0, 10, p=10.0, q=1.0, seed=i)
        for j in range(2, len(walk)):
            if walk[j] == walk[j-2]:
                backtracks_high_p += 1
    
    assert backtracks_low_p > backtracks_high_p * 2  # Significantly more

Edge Weight Test
~~~~~~~~~~~~~~~~

Visit frequency matches edge weight ratios:

.. code-block:: python

    import networkx as nx
    from py3plex.algorithms.general.walkers import basic_random_walk
    from collections import Counter
    
    G = nx.Graph()
    G.add_weighted_edges_from([
        (0, 1, 1.0),
        (0, 2, 2.0),
        (0, 3, 3.0),
    ])
    
    visits = Counter()
    for i in range(10000):
        walk = basic_random_walk(G, 0, 1, weighted=True, seed=i)
        if len(walk) > 1:
            visits[walk[1]] += 1
    
    # Expected ratio: 1:2:3
    total = sum(visits.values())
    ratios = [visits[1]/total, visits[2]/total, visits[3]/total]
    expected = [1/6, 2/6, 3/6]
    
    # Within 5% tolerance
    for obs, exp in zip(ratios, expected):
        assert abs(obs - exp) < 0.05

References
----------

**Node2Vec:**
  Grover, A., & Leskovec, J. (2016). node2vec: Scalable feature learning for networks.
  *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 855-864.
  https://doi.org/10.1145/2939672.2939754

**DeepWalk:**
  Perozzi, B., Al-Rfou, R., & Skiena, S. (2014). DeepWalk: Online learning of social representations.
  *Proceedings of the 20th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 701-710.
  https://doi.org/10.1145/2623330.2623732

**Random Walks on Graphs:**
  Lovász, L. (1993). Random walks on graphs: A survey.
  *Combinatorics, Paul Erdős is Eighty*, 2, 1-46.

API Reference
-------------

See :mod:`py3plex.algorithms.general.walkers` for complete API documentation.

Examples
--------

Complete examples can be found in:

- ``examples/example_random_walks.py`` - Basic usage examples
- ``tests/test_random_walks.py`` - Comprehensive test suite

Repository: https://github.com/SkBlaz/py3plex
