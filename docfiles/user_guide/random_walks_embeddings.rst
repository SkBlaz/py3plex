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

- [OK] Basic random walks with proper edge weight handling
- [OK] Second-order (biased) random walks following Node2Vec logic
- [OK] Multiple simultaneous walks with deterministic seeding
- [OK] Support for directed, weighted, and multigraphs
- [OK] Multilayer network-aware walks with layer constraints
- [OK] Efficient sparse adjacency matrix handling
- [OK] Comprehensive test suite validating correctness properties

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

Complete Embedding Workflow
---------------------------

This section provides a complete, end-to-end workflow for generating node embeddings from a multilayer network and using them for downstream machine learning tasks.

Step 1: Prepare the Network
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    import numpy as np
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Load your multilayer network
    network = multinet.multi_layer_network().load_network(
        "your_network.multiedgelist",
        input_type="multiedgelist",
        directed=False
    )
    
    # Verify the network
    network.basic_stats()
    
    # Get the core NetworkX graph
    G = network.core_network

Step 2: Generate Random Walks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks
    
    # Generate walks with Node2Vec-style biased sampling
    # Recommended starting parameters
    walks = generate_walks(
        G,
        num_walks=10,       # 10 walks per node (more = better embeddings, slower)
        walk_length=80,     # 80 steps per walk (adjust based on graph diameter)
        p=1.0,              # Return parameter (1.0 = balanced)
        q=1.0,              # In-out parameter (1.0 = balanced)
        seed=42             # For reproducibility
    )
    
    print(f"Generated {len(walks)} walks")
    print(f"Sample walk: {walks[0][:10]}...")  # First 10 nodes of first walk

Step 3: Train Embedding Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Requires gensim: pip install gensim
    from gensim.models import Word2Vec
    
    # Convert walks to strings (Word2Vec expects string tokens)
    walks_str = [[str(node) for node in walk] for walk in walks]
    
    # Train the embedding model
    model = Word2Vec(
        walks_str,
        vector_size=128,    # Embedding dimension (64-256 typical)
        window=5,           # Context window size
        min_count=1,        # Include nodes that appear at least once
        sg=1,               # Use skip-gram (1) vs CBOW (0)
        workers=4,          # Parallel training threads
        epochs=5,           # Training epochs
        seed=42             # Reproducibility
    )
    
    print(f"Trained embeddings for {len(model.wv)} nodes")
    print(f"Embedding dimension: {model.wv.vector_size}")

Step 4: Extract and Use Embeddings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import numpy as np
    
    # Get all node IDs
    node_ids = list(model.wv.index_to_key)
    
    # Create embedding matrix
    embeddings = np.array([model.wv[node_id] for node_id in node_ids])
    print(f"Embedding matrix shape: {embeddings.shape}")
    
    # Get embedding for a specific node
    sample_node = node_ids[0]
    node_embedding = model.wv[sample_node]
    print(f"Embedding for {sample_node}: {node_embedding[:5]}... (dim={len(node_embedding)})")
    
    # Find similar nodes
    similar_nodes = model.wv.most_similar(sample_node, topn=5)
    print(f"\nMost similar to {sample_node}:")
    for node, similarity in similar_nodes:
        print(f"  {node}: {similarity:.4f}")

Step 5: Downstream Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~

**Node Clustering:**

.. code-block:: python

    from sklearn.cluster import KMeans
    import numpy as np
    
    # Cluster nodes based on embeddings
    n_clusters = 5
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(embeddings)
    
    # Assign clusters to nodes
    node_clusters = dict(zip(node_ids, clusters))
    
    print("Cluster distribution:")
    from collections import Counter
    for cluster, count in sorted(Counter(clusters).items()):
        print(f"  Cluster {cluster}: {count} nodes")

**Node Classification:**

.. code-block:: python

    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, classification_report
    
    # Assume you have labels for nodes
    # labels = {node_id: label for node_id, label in your_label_data}
    
    # For demonstration, create synthetic labels based on layer
    labels = {}
    for node_id in node_ids:
        # Extract layer from node-layer tuple string representation
        # Adjust this based on your actual node ID format
        if 'layer1' in str(node_id):
            labels[node_id] = 0
        elif 'layer2' in str(node_id):
            labels[node_id] = 1
        else:
            labels[node_id] = 2
    
    # Prepare data
    X = embeddings
    y = np.array([labels[node_id] for node_id in node_ids])
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train classifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Classification accuracy: {accuracy:.4f}")

**Link Prediction:**

.. code-block:: python

    from sklearn.linear_model import LogisticRegression
    import numpy as np
    
    def edge_embedding(node1, node2, method='hadamard'):
        """Compute edge embedding from node embeddings."""
        emb1 = model.wv[str(node1)]
        emb2 = model.wv[str(node2)]
        
        if method == 'hadamard':
            return emb1 * emb2
        elif method == 'average':
            return (emb1 + emb2) / 2
        elif method == 'concat':
            return np.concatenate([emb1, emb2])
        else:
            raise ValueError(f"Unknown method: {method}")
    
    # Get existing edges (positive examples)
    existing_edges = list(G.edges())[:100]  # Sample for demo
    
    # Generate negative examples (non-edges)
    nodes = list(G.nodes())
    negative_edges = []
    while len(negative_edges) < len(existing_edges):
        n1 = nodes[np.random.randint(len(nodes))]
        n2 = nodes[np.random.randint(len(nodes))]
        if n1 != n2 and not G.has_edge(n1, n2):
            negative_edges.append((n1, n2))
    
    # Create training data
    X_edges = []
    y_edges = []
    
    for edge in existing_edges:
        try:
            X_edges.append(edge_embedding(edge[0], edge[1]))
            y_edges.append(1)  # Positive
        except KeyError:
            pass  # Skip if node not in vocabulary
    
    for edge in negative_edges:
        try:
            X_edges.append(edge_embedding(edge[0], edge[1]))
            y_edges.append(0)  # Negative
        except KeyError:
            pass
    
    X_edges = np.array(X_edges)
    y_edges = np.array(y_edges)
    
    # Train link prediction model
    X_train, X_test, y_train, y_test = train_test_split(
        X_edges, y_edges, test_size=0.2, random_state=42
    )
    
    clf = LogisticRegression(random_state=42)
    clf.fit(X_train, y_train)
    
    accuracy = clf.score(X_test, y_test)
    print(f"Link prediction accuracy: {accuracy:.4f}")

Step 6: Save and Load Embeddings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Save embeddings in Word2Vec format
    model.wv.save_word2vec_format("node_embeddings.txt", binary=False)
    print("Embeddings saved to node_embeddings.txt")
    
    # Save as NumPy arrays (for sklearn compatibility)
    np.save("embedding_matrix.npy", embeddings)
    np.save("node_ids.npy", np.array(node_ids))
    print("Embeddings saved as NumPy arrays")
    
    # Load embeddings later
    from gensim.models import KeyedVectors
    loaded_embeddings = KeyedVectors.load_word2vec_format("node_embeddings.txt")
    print(f"Loaded embeddings for {len(loaded_embeddings)} nodes")

Parameter Tuning Guide
----------------------

Walk Length Guidelines
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 20 30 30

   * - Network Size
     - walk_length
     - Reasoning
     - Trade-off
   * - Small (<1K nodes)
     - 40-80
     - Shorter walks sufficient
     - Speed vs coverage
   * - Medium (1K-10K)
     - 80-120
     - Standard choice
     - Balanced
   * - Large (>10K)
     - 80-100
     - Longer walks costly
     - Memory/time vs quality

**Rule of thumb:** ``walk_length`` should be at least 2-3× the network diameter.

Number of Walks Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 20 30 30

   * - Task
     - num_walks
     - Reasoning
     - Trade-off
   * - Exploration
     - 5-10
     - Quick results
     - Speed vs quality
   * - Standard
     - 10-20
     - Good balance
     - Recommended
   * - High-quality
     - 20-50
     - Better embeddings
     - Time vs quality
   * - Research
     - 50-100
     - Maximum quality
     - Very slow

**Rule of thumb:** More walks = better embeddings, but with diminishing returns after ~20.

P and Q Parameter Effects
~~~~~~~~~~~~~~~~~~~~~~~~~~

The p and q parameters control the walk's exploration behavior:

**Return parameter p:**

* **p < 1:** More likely to backtrack (return to previous node)
  
  * Use when: Local structure is important; you want to capture tight clusters

* **p = 1:** Balanced (equivalent to basic random walk for backtracking)
  
  * Use when: No prior about network structure

* **p > 1:** Less likely to backtrack (move forward)
  
  * Use when: You want walks to explore broadly

**In-out parameter q:**

* **q < 1:** More likely to explore distant nodes (DFS-like)
  
  * Use when: You want to capture global structure, find communities

* **q = 1:** Balanced exploration
  
  * Use when: No prior about network structure

* **q > 1:** More likely to stay in local neighborhood (BFS-like)
  
  * Use when: You want to capture local structure, homophily

**Common presets:**

.. code-block:: python

    # Local/homophily-focused (similar to BFS)
    p, q = 1.0, 2.0
    
    # Global/structural (similar to DFS)
    p, q = 1.0, 0.5
    
    # Balanced (DeepWalk-like)
    p, q = 1.0, 1.0
    
    # Strong local focus
    p, q = 0.5, 2.0
    
    # Strong exploration
    p, q = 2.0, 0.5

Common Failure Modes
--------------------

Disconnected Graph
~~~~~~~~~~~~~~~~~~~

**Problem:** Walk gets stuck or terminates early because node has no neighbors.

**Symptoms:**

* Walks shorter than expected
* Some nodes never appear in walks
* Embeddings missing for some nodes

**Solutions:**

.. code-block:: python

    import networkx as nx
    
    # Check connectivity
    if not nx.is_connected(G.to_undirected()):
        print("Graph is disconnected!")
        
        # Option 1: Use largest connected component
        largest_cc = max(nx.connected_components(G.to_undirected()), key=len)
        G_connected = G.subgraph(largest_cc).copy()
        
        # Option 2: Add small random edges to connect components
        # (use with caution - changes graph structure)

Highly Skewed Degree Distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** High-degree hub nodes dominate walks; low-degree nodes underrepresented.

**Symptoms:**

* Most walks pass through the same few nodes
* Embeddings for peripheral nodes are poor quality
* Similarity to hub nodes is overestimated

**Solutions:**

.. code-block:: python

    # Option 1: Use more walks per node
    walks = generate_walks(G, num_walks=30, walk_length=80, seed=42)
    
    # Option 2: Add node-specific walks for low-degree nodes
    low_degree_nodes = [n for n in G.nodes() if G.degree(n) < 5]
    extra_walks = generate_walks(
        G, 
        num_walks=20,
        walk_length=80,
        start_nodes=low_degree_nodes,
        seed=42
    )
    walks.extend(extra_walks)
    
    # Option 3: Use weighted walks that downweight high-degree nodes
    # (requires custom implementation)

Isolated Nodes
~~~~~~~~~~~~~~~

**Problem:** Nodes with degree 0 cannot be walked from.

**Symptoms:**

* KeyError when looking up embeddings
* Missing nodes in similarity queries

**Solutions:**

.. code-block:: python

    # Remove isolated nodes before generating walks
    isolated = list(nx.isolates(G))
    G_filtered = G.copy()
    G_filtered.remove_nodes_from(isolated)
    
    # Generate walks on filtered graph
    walks = generate_walks(G_filtered, num_walks=10, walk_length=80, seed=42)
    
    # Handle isolated nodes separately (e.g., assign zero embedding)

Very Small Graph
~~~~~~~~~~~~~~~~~

**Problem:** With few nodes, walks become repetitive quickly.

**Symptoms:**

* Walks cycle through the same nodes repeatedly
* All nodes have similar embeddings
* Poor discriminative power

**Solutions:**

.. code-block:: python

    # Use shorter walks for small graphs
    if G.number_of_nodes() < 100:
        walk_length = min(40, G.number_of_nodes() * 2)
    
    # Use fewer walks (avoid redundancy)
    num_walks = min(10, G.number_of_nodes())
    
    # Consider direct matrix-based methods for very small graphs
    # (spectral embeddings, Laplacian eigenvectors)

Memory Issues with Large Graphs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Storing all walks in memory causes OOM errors.

**Symptoms:**

* MemoryError during walk generation
* System becomes unresponsive

**Solutions:**

.. code-block:: python

    # Option 1: Generate walks in batches
    all_walks = []
    nodes = list(G.nodes())
    batch_size = 1000
    
    for i in range(0, len(nodes), batch_size):
        batch_nodes = nodes[i:i+batch_size]
        batch_walks = generate_walks(
            G,
            num_walks=10,
            walk_length=80,
            start_nodes=batch_nodes,
            seed=42+i
        )
        all_walks.extend(batch_walks)
        print(f"Processed {i+batch_size}/{len(nodes)} nodes")
    
    # Option 2: Stream walks directly to Word2Vec
    # (requires custom iterator implementation)
    
    # Option 3: Use disk-based storage
    # Write walks to file, then load for training

Native Multilayer Embedding API
-------------------------------

Beyond low-level walker primitives, py3plex exposes first-class embedding models
for multilayer and multiplex networks in ``py3plex.ml.embedding`` and via
``multi_layer_network.embed(...)``.

Available multilayer-focused methods include:

- ``supra_node2vec`` (:class:`py3plex.ml.embedding.SupraNode2VecEmbedding`)
- ``supra_spectral`` (:class:`py3plex.ml.embedding.SupraSpectralEmbedding`)
- ``supra_netmf`` (:class:`py3plex.ml.embedding.SupraNetMFEmbedding`)
- ``mne`` (:class:`py3plex.ml.embedding.MNEEmbedding`)
- ``mell`` (:class:`py3plex.ml.embedding.MELLEmbedding`)
- ``multilayer_gnn`` (:class:`py3plex.ml.embedding.MultiLayerGNNEmbedding`, experimental scaffold)

These models use ``(node, layer)`` state nodes as the canonical internal target.
Physical-node embeddings can be derived with ``target="both"`` and
``node_reduce="mean" | "sum" | "max"``.

.. code-block:: python

    from py3plex.ml.embedding import SupraNode2VecEmbedding

    model = SupraNode2VecEmbedding(
        dimensions=128,
        walk_length=80,
        num_walks=10,
        cross_layer_prob=0.2,
        target="both",
        node_reduce="mean",
        seed=42,
    )
    result_state = model.fit_transform(net)
    result_node = model.node_embeddings()

You can access the same models through ``multi_layer_network.embed``:

.. code-block:: python

    result = net.embed(
        method="supra_node2vec",
        dimensions=128,
        walk_length=80,
        num_walks=10,
        seed=42,
    )

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

- ``examples/advanced/example_random_walks.py`` - Basic usage examples
- ``tests/test_random_walks.py`` - Comprehensive test suite

Repository: https://github.com/SkBlaz/py3plex
