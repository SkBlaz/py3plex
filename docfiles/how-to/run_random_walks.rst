How to Run Random Walk Algorithms
==================================

**Goal:** Generate network embeddings and node representations using random walk algorithms.

**Prerequisites:** A loaded network (see :doc:`load_and_build_networks`).

All embedding helpers in py3plex return a mapping from ``(node_id, layer)`` tuples to dense vectors of length ``dimensions``. Single-layer inputs still keep the layer entry so you can tell layers apart in multiplex graphs.

.. note:: Where to find this data
   
   Examples in this guide create networks programmatically for clarity. You can also:
   
   * Use built-in generators: ``from py3plex.algorithms import random_generators``
   * Load from repository files: ``datasets/multiedgelist.txt``
   * Fetch real-world datasets: ``from py3plex.datasets import fetch_multilayer``

Node2Vec Embeddings
-------------------

Node2Vec generates vector representations of nodes by simulating biased random walks:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.wrappers import train_node2vec
    
    # Create a sample network
    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Charlie', 'friends', 1],
        ['Alice', 'colleagues', 'Charlie', 'colleagues', 1],
    ], input_type="list")
    
    # Train Node2Vec
    embeddings = train_node2vec(
        network,
        dimensions=128,    # Embedding dimensionality
        walk_length=80,    # Length of each walk
        num_walks=10,      # Walks per node
        p=1.0,            # Return parameter
        q=1.0,            # In-out parameter
        workers=4
    )
    
    # Access embeddings
    node = ('Alice', 'friends')
    vector = embeddings[node]
    print(f"Embedding dimension: {len(vector)}")

**Expected output:**

.. code-block:: text

    Embedding dimension: 128

The `p` and `q` parameters control the walk behavior:

* **p** (return parameter): Cost of immediately revisiting the previous node (low ``p`` = easy to backtrack; high ``p`` = discouraged)
* **q** (in-out parameter): Balance between staying near the previous node versus exploring new territory (``q > 1`` ≈ breadth-first/local, ``q < 1`` ≈ depth-first/outward)

Think of ``p`` as controlling backtracking and ``q`` as controlling locality; tune them together to steer walks toward either local neighborhoods or long-range exploration.

DeepWalk Embeddings
-------------------

DeepWalk is a special case of Node2Vec with ``p=1, q=1``:

.. code-block:: python

    from py3plex.wrappers import train_deepwalk
    
    embeddings = train_deepwalk(
        network,
        dimensions=128,
        walk_length=80,
        num_walks=10,
        workers=4
    )

Using Embeddings for Downstream Tasks
--------------------------------------

The following examples assume you already computed ``embeddings`` with Node2Vec or DeepWalk; adjust names if you generate multiple embedding sets.

Node Classification
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    import numpy as np
    
    # Prepare data
    nodes = list(embeddings.keys())
    X = np.array([embeddings[node] for node in nodes])
    
    # Replace with your label lookup (one label per (node, layer) tuple)
    y = np.array([get_label(node) for node in nodes])
    
    # Train classifier
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    clf = LogisticRegression()
    clf.fit(X_train, y_train)
    
    accuracy = clf.score(X_test, y_test)
    print(f"Classification accuracy: {accuracy:.2%}")

Link Prediction
~~~~~~~~~~~~~~~

Embeddings are keyed by ``(node, layer)``; compare nodes within the same layer when interpreting similarity scores.

.. code-block:: python

    from sklearn.metrics.pairwise import cosine_similarity
    
    # Compute similarity between nodes
    node1 = ('Alice', 'friends')
    node2 = ('Bob', 'friends')
    
    vec1 = embeddings[node1].reshape(1, -1)
    vec2 = embeddings[node2].reshape(1, -1)
    
    similarity = cosine_similarity(vec1, vec2)[0][0]
    print(f"Similarity: {similarity:.3f}")
    
    # Predict links for high-similarity pairs
    threshold = 0.7
    if similarity > threshold:
        print(f"High likelihood of connection between {node1} and {node2}")

Node Clustering
~~~~~~~~~~~~~~~

.. code-block:: python

    from sklearn.cluster import KMeans
    
    # Cluster nodes based on embeddings
    nodes = list(embeddings.keys())
    X = np.array([embeddings[node] for node in nodes])
    
    kmeans = KMeans(n_clusters=5, random_state=42)
    clusters = kmeans.fit_predict(X)
    
    # Map nodes to clusters
    node_clusters = dict(zip(nodes, clusters))
    
    print("Cluster assignments:")
    for node, cluster in list(node_clusters.items())[:10]:
        print(f"{node} → Cluster {cluster}")

Visualizing Embeddings
-----------------------

Use dimensionality reduction to visualize:

.. code-block:: python

    from sklearn.manifold import TSNE
    import matplotlib.pyplot as plt
    
    # Reduce to 2D
    nodes = list(embeddings.keys())
    X = np.array([embeddings[node] for node in nodes])
    
    tsne = TSNE(n_components=2, random_state=42)
    X_2d = tsne.fit_transform(X)
    
    # Plot
    plt.figure(figsize=(12, 8))
    plt.scatter(X_2d[:, 0], X_2d[:, 1], alpha=0.5)
    
    # Label a few nodes
    for i, node in enumerate(nodes[:20]):
        plt.annotate(
            str(node),
            (X_2d[i, 0], X_2d[i, 1]),
            fontsize=8
        )
    
    plt.title('Node Embeddings (t-SNE)')
    plt.savefig('embeddings_2d.png', dpi=300, bbox_inches='tight')
    plt.show()

Saving and Loading Embeddings
------------------------------

Save to File
~~~~~~~~~~~~

.. code-block:: python

    import pickle
    
    # Save embeddings
    with open('embeddings.pkl', 'wb') as f:
        pickle.dump(embeddings, f)
    
    # Load embeddings
    with open('embeddings.pkl', 'rb') as f:
        loaded_embeddings = pickle.load(f)

Export to CSV
~~~~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    
    # Convert to DataFrame
    data = []
    for node, vector in embeddings.items():
        row = {'node': str(node)}
        for i, val in enumerate(vector):
            row[f'dim_{i}'] = val
        data.append(row)
    
    df = pd.DataFrame(data)
    df.to_csv('embeddings.csv', index=False)

Parameter Tuning
----------------

Random walk hyperparameters meaningfully change embedding quality. Use small validation loops to pick settings that balance accuracy and runtime, and fix seeds (``random_state`` / ``workers``) when you want reproducibility across runs.

Grid Search for Best Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Training embeddings inside a grid search can be expensive; start with a coarse grid or a small subgraph, then refine around promising regions.

.. code-block:: python

    from sklearn.model_selection import cross_val_score
    from sklearn.linear_model import LogisticRegression
    import numpy as np
    
    param_grid = {
        'dimensions': [64, 128, 256],
        'walk_length': [40, 80, 120],
        'num_walks': [5, 10, 20]
    }
    
    best_score = 0
    best_params = None
    
    for dims in param_grid['dimensions']:
        for walk_len in param_grid['walk_length']:
            for num_walks in param_grid['num_walks']:
                # Train embeddings
                emb = train_node2vec(
                    network,
                    dimensions=dims,
                    walk_length=walk_len,
                    num_walks=num_walks
                )
                
                # Evaluate (assuming you have labels)
                nodes = list(emb.keys())
                labels = [get_label(n) for n in nodes]  # Provide labels keyed by (node, layer)
                X = np.array([emb[n] for n in nodes])
                y = np.array(labels)
                scores = cross_val_score(
                    LogisticRegression(),
                    X, y, cv=5
                )
                
                mean_score = scores.mean()
                if mean_score > best_score:
                    best_score = mean_score
                    best_params = {
                        'dimensions': dims,
                        'walk_length': walk_len,
                        'num_walks': num_walks
                    }
    
    print(f"Best parameters: {best_params}")
    print(f"Best score: {best_score:.3f}")

Layer-Specific Embeddings
--------------------------

Generate embeddings for individual layers:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    layer_embeddings = {}
    
    for layer in network.get_layers():
        # Extract layer subgraph
        subgraph = Q.edges().from_layers(L[layer]).execute(network)
        
        # Train embeddings on this layer
        emb = train_node2vec(subgraph, dimensions=128)
        layer_embeddings[layer] = emb
        
        print(f"Generated embeddings for layer: {layer}")

Query and Filter Nodes Before Embedding with DSL
-------------------------------------------------

**Goal:** Use py3plex's DSL to select specific node subsets for targeted embedding generation.

Random walks and embeddings on large networks can be computationally expensive. The DSL allows you to filter and extract subnetworks before running embedding algorithms, focusing on nodes of interest.

Filter High-Degree Nodes
~~~~~~~~~~~~~~~~~~~~~~~~~

**Generate embeddings only for hub nodes:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.wrappers import train_node2vec
    from py3plex.dsl import Q, execute_query
    
    # Load network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "py3plex/datasets/_data/synthetic_multilayer.edges",
        input_type="multiedgelist"
    )
    
    # Use DSL to find high-degree nodes (hubs)
    hubs = (
        Q.nodes()
         .compute("degree")
         .where(degree__gt=8)  # Degree > 8
         .execute(network)
    )
    
    print(f"Found {len(hubs)} hub nodes")
    
    # Extract subgraph containing only hubs
    hub_subgraph = network.core_network.subgraph(hubs.keys())
    
    # Train embeddings on hub subgraph
    hub_network = multinet.multi_layer_network(directed=False)
    hub_network.core_network = hub_subgraph.copy()
    
    hub_embeddings = train_node2vec(
        hub_network,
        dimensions=64,
        walk_length=40,
        num_walks=10
    )
    
    print(f"Generated embeddings for {len(hub_embeddings)} hubs")

**Expected output:**

.. code-block:: text

    Found 15 hub nodes
    Generated embeddings for 15 hubs

Layer-Specific Node Selection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Generate embeddings for nodes active in multiple layers:**

.. code-block:: python

    from py3plex.dsl import Q, L
    from collections import Counter
    
    # Count layer participation for each node
    node_layers = Counter()
    for node, layer in network.get_nodes():
        node_layers[node] += 1
    
    # Find nodes in 2+ layers
    multilayer_nodes = {
        node for node, count in node_layers.items()
        if count >= 2
    }
    
    print(f"Nodes in 2+ layers: {len(multilayer_nodes)}")
    
    # Convert back to (node, layer) tuples
    multilayer_node_tuples = [
        (node, layer)
        for node, layer in network.get_nodes()
        if node in multilayer_nodes
    ]
    
    # Extract subgraph
    multi_subgraph = network.core_network.subgraph(multilayer_node_tuples)
    
    # Generate embeddings
    multi_network = multinet.multi_layer_network(directed=False)
    multi_network.core_network = multi_subgraph.copy()
    
    multi_embeddings = train_node2vec(multi_network, dimensions=64)
    print(f"Generated embeddings for {len(multi_embeddings)} multilayer nodes")

**Expected output:**

.. code-block:: text

    Nodes in 2+ layers: 35
    Generated embeddings for 105 multilayer nodes

Query Nodes by Centrality
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Focus embeddings on central nodes:**

.. code-block:: python

    from py3plex.dsl import Q
    
    # Find nodes with high betweenness centrality
    central_nodes = (
        Q.nodes()
         .compute("betweenness_centrality", "degree")
         .where(betweenness_centrality__gt=0.01)
         .execute(network)
    )
    
    print(f"High-centrality nodes: {len(central_nodes)}")
    
    # Extract and embed
    central_subgraph = network.core_network.subgraph(central_nodes.keys())
    central_network = multinet.multi_layer_network(directed=False)
    central_network.core_network = central_subgraph.copy()
    
    central_embeddings = train_node2vec(
        central_network,
        dimensions=128,
        walk_length=80,
        num_walks=10
    )
    
    # Compare embedding similarity for central nodes
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    
    node_list = list(central_embeddings.keys())[:5]
    vectors = np.array([central_embeddings[n] for n in node_list])
    
    sim_matrix = cosine_similarity(vectors)
    print("\nSimilarity matrix (first 5 central nodes):")
    print(sim_matrix)

Combine Embeddings with Node Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Query embedded nodes with specific properties:**

.. code-block:: python

    import numpy as np

    # After generating embeddings, attach them as attributes
    for node, vector in embeddings.items():
        # Store embedding norm as an attribute
        embedding_norm = np.linalg.norm(vector)
        network.core_network.nodes[node]['embedding_norm'] = embedding_norm
    
    # Query nodes with large embedding norms
    large_norm_nodes = execute_query(
        network,
        'SELECT nodes WHERE embedding_norm > 10.0'
    )
    
    norm_matches = large_norm_nodes.get("nodes", [])
    count = large_norm_nodes.get("count", len(norm_matches))
    print(f"Nodes with large embedding norms: {count}")

Layer-Specific Embedding Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Compare embeddings across layers:**

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Generate embeddings per layer
    layer_embeddings = {}
    layer_stats = {}
    
    for layer in network.get_layers():
        # Extract layer
        layer_nodes = Q.nodes().from_layers(L[layer]).execute(network)
        layer_edges = Q.edges().from_layers(L[layer]).execute(network)
        
        print(f"\nLayer: {layer}")
        print(f"  Nodes: {len(layer_nodes)}")
        print(f"  Edges: {len(layer_edges)}")
        
        # Extract layer subgraph
        layer_subgraph = network.core_network.subgraph(layer_nodes.keys())
        
        # Skip if too few nodes
        if len(layer_nodes) < 5:
            print(f"  [SKIP] Too few nodes")
            continue
        
        # Create layer network
        layer_net = multinet.multi_layer_network(directed=False)
        layer_net.core_network = layer_subgraph.copy()
        
        # Generate embeddings
        try:
            emb = train_node2vec(
                layer_net,
                dimensions=64,
                walk_length=40,
                num_walks=10,
                workers=1
            )
            
            layer_embeddings[layer] = emb
            
            # Compute statistics
            vectors = np.array(list(emb.values()))
            mean_norm = np.mean([np.linalg.norm(v) for v in vectors])
            
            layer_stats[layer] = {
                'n_nodes': len(emb),
                'mean_embedding_norm': mean_norm
            }
            
            print(f"  ✓ Embeddings generated: {len(emb)} nodes")
            print(f"  Mean embedding norm: {mean_norm:.2f}")
        except Exception as e:
            print(f"  [ERROR] {e}")

**Expected output:**

.. code-block:: text

    Layer: layer1
      Nodes: 40
      Edges: 95
      ✓ Embeddings generated: 40 nodes
      Mean embedding norm: 12.34
    
    Layer: layer2
      Nodes: 40
      Edges: 87
      ✓ Embeddings generated: 40 nodes
      Mean embedding norm: 11.89
    
    Layer: layer3
      Nodes: 40
      Edges: 102
      ✓ Embeddings generated: 40 nodes
      Mean embedding norm: 13.01

Export Embeddings with Metadata Using DSL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Create analysis-ready embedding exports:**

.. code-block:: python

    import pandas as pd
    from py3plex.dsl import Q
    
    # Compute node metrics
    metrics = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    # Combine embeddings with metrics
    data = []
    for node in embeddings.keys():
        row = {
            'node': node[0],
            'layer': node[1],
            'degree': metrics[node]['degree'],
            'betweenness': metrics[node]['betweenness_centrality']
        }
        
        # Add embedding dimensions
        for i, val in enumerate(embeddings[node]):
            row[f'emb_{i}'] = val
        
        data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Export
    df.to_csv('embeddings_with_metrics.csv', index=False)
    print(f"Exported {len(df)} node embeddings with metadata")

**Why use DSL for embedding workflows?**

* **Targeted embedding:** Focus on relevant node subsets, reducing computation time
* **Layer-aware:** Generate layer-specific embeddings seamlessly
* **Metric integration:** Combine embeddings with centrality and other network metrics
* **Filtering:** Select nodes by degree, centrality, or custom attributes before embedding
* **Reproducible:** Declarative queries document node selection criteria

**Next steps with DSL:**

* **Full DSL tutorial:** :doc:`query_with_dsl` - Comprehensive guide with advanced patterns
* **Community detection:** :doc:`run_community_detection` - Use embeddings for community analysis
* **Dynamics analysis:** :doc:`simulate_dynamics` - Combine embeddings with dynamics results

Next Steps
----------

* **Use embeddings for ML tasks:** See sklearn documentation
* **Visualize networks:** :doc:`visualize_networks`
* **Understand algorithms:** :doc:`../concepts/algorithm_landscape`
* **API reference:** :doc:`../reference/algorithm_reference`
