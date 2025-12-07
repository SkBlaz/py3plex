How to Run Random Walk Algorithms
==================================

**Goal:** Generate network embeddings and node representations using random walk algorithms.

**Prerequisites:** A loaded network (see :doc:`load_and_build_networks`).

Node2Vec Embeddings
-------------------

Node2Vec generates vector representations of nodes by simulating biased random walks:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.wrappers import train_node2vec
    
    # Load network
    network = multinet.multi_layer_network()
    network.load_network("data.multiedgelist", input_type="multiedgelist")
    
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

* **p** (return parameter): Likelihood of returning to previous node
* **q** (in-out parameter): Likelihood of exploring outward vs. staying local

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

Node Classification
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    import numpy as np
    
    # Prepare data
    nodes = list(embeddings.keys())
    X = np.array([embeddings[node] for node in nodes])
    
    # Assuming you have labels
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

Grid Search for Best Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
                X = np.array([emb[n] for n in nodes])
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

Next Steps
----------

* **Use embeddings for ML tasks:** See sklearn documentation
* **Visualize networks:** :doc:`visualize_networks`
* **Understand algorithms:** :doc:`../concepts/algorithm_landscape`
* **API reference:** :doc:`../reference/algorithm_reference`
