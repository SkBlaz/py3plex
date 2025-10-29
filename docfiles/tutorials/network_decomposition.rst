Network Decomposition Tutorial
===============================

This tutorial demonstrates network decomposition techniques for heterogeneous and multilayer networks using py3plex.

Overview
--------

Network decomposition transforms complex heterogeneous networks into structured feature representations that can be used for:

* Node classification
* Link prediction
* Network comparison
* Feature extraction for machine learning

py3plex's HINMINE module provides methods for decomposing heterogeneous information networks (HINs) based on:

* **Meta-paths** - Typed paths connecting node pairs
* **Cycles** - Closed walks of specific types
* **Structural patterns** - Subgraph patterns and motifs

What is Network Decomposition?
-------------------------------

Heterogeneous Information Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A **heterogeneous information network (HIN)** contains multiple node types and edge types.

Example - Academic Network:

* **Node types:** Authors, Papers, Venues
* **Edge types:** Author-Paper (writes), Paper-Venue (published_in), Paper-Paper (cites)

Meta-paths
~~~~~~~~~~

A **meta-path** is a sequence of node and edge types defining a composite relation.

Examples:

* Author → Paper → Author (co-authorship)
* Author → Paper → Venue → Paper → Author (same venue)
* Paper → Paper → Paper (citation path of length 2)

HINMINE Decomposition
---------------------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

    from py3plex.core.HINMINE import decomposition
    from py3plex.core import multinet
    
    # Load heterogeneous network
    network = multinet.multi_layer_network()
    network.load_network("academic_network.graphml", input_type="graphml")
    
    # Perform decomposition
    decomposer = decomposition.HINMINE()
    features = decomposer.run_decomposition(
        network,
        target_node_type='author',
        max_path_length=3
    )
    
    # Features is a matrix: (num_nodes, num_meta_paths)
    print(f"Feature matrix shape: {features.shape}")

Parameters
~~~~~~~~~~

.. code-block:: python

    features = decomposer.run_decomposition(
        network,
        target_node_type='author',     # Node type to extract features for
        max_path_length=3,              # Maximum meta-path length
        include_cycles=True,            # Include closed walks
        normalize=True                  # Normalize features
    )

Meta-Path Extraction
--------------------

Enumerate Meta-Paths
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get all meta-paths up to length 3
    meta_paths = decomposer.enumerate_meta_paths(
        network,
        max_length=3,
        node_types=['author', 'paper', 'venue']
    )
    
    print(f"Found {len(meta_paths)} meta-paths")
    for mp in meta_paths[:5]:
        print(mp)

Example output::

    author-paper-author
    author-paper-venue-paper-author
    paper-paper
    paper-author-paper
    venue-paper-venue

Compute Meta-Path Instances
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Count instances of specific meta-paths:

.. code-block:: python

    # Define a meta-path
    meta_path = ['author', 'paper', 'author']
    
    # Count instances for each node
    instances = decomposer.compute_meta_path_instances(
        network,
        meta_path,
        source_nodes=['author1', 'author2']
    )
    
    for node, count in instances.items():
        print(f"{node}: {count} instances")

Cycle Enumeration
-----------------

Extract Cycles
~~~~~~~~~~~~~~

Find closed walks (cycles) in the network:

.. code-block:: python

    # Enumerate all cycles up to length 4
    cycles = decomposer.enumerate_cycles(
        network,
        max_length=4,
        starting_node_type='author'
    )
    
    print(f"Found {len(cycles)} cycle types")

Common Cycles
~~~~~~~~~~~~~

Examples of meaningful cycles in academic networks:

* **Triangle:** Author → Paper → Venue → Paper → Author → Paper
* **Square:** Paper → Cites → Paper → Cites → Paper → Cites → Paper
* **Collaboration cycle:** Author → Paper → Author → Paper → Author

Feature Matrix Construction
----------------------------

Build Classification Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Build feature matrix for author classification
    features = decomposer.build_feature_matrix(
        network,
        target_nodes=['author1', 'author2', 'author3'],
        meta_paths=[
            ['author', 'paper', 'author'],           # Co-authorship
            ['author', 'paper', 'venue'],            # Publishing venues
            ['author', 'paper', 'paper'],            # Citation patterns
        ],
        normalize=True
    )
    
    # Features shape: (3, 3) for 3 nodes, 3 meta-paths
    print(features)

Normalization Options
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # L1 normalization (sum to 1)
    features_l1 = decomposer.normalize_features(features, method='l1')
    
    # L2 normalization (unit length)
    features_l2 = decomposer.normalize_features(features, method='l2')
    
    # Min-max scaling (0-1 range)
    features_minmax = decomposer.normalize_features(features, method='minmax')
    
    # Z-score standardization (mean 0, std 1)
    features_zscore = decomposer.normalize_features(features, method='zscore')

Node Classification Example
----------------------------

Complete Workflow
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score
    
    # 1. Load network with node labels
    network = multinet.multi_layer_network()
    network.load_network("labeled_network.graphml", input_type="graphml")
    
    # 2. Extract features via decomposition
    decomposer = decomposition.HINMINE()
    features = decomposer.run_decomposition(
        network,
        target_node_type='author',
        max_path_length=3
    )
    
    # 3. Get labels
    labels = network.labels  # Assuming labels are stored in network
    
    # 4. Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.3, random_state=42
    )
    
    # 5. Train classifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    # 6. Evaluate
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    print(f"Accuracy: {accuracy:.3f}")
    print(f"F1-score: {f1:.3f}")

Feature Importance
~~~~~~~~~~~~~~~~~~

Analyze which meta-paths are most informative:

.. code-block:: python

    import matplotlib.pyplot as plt
    
    # Get feature importances from trained model
    importances = clf.feature_importances_
    meta_path_names = decomposer.get_meta_path_names()
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.barh(range(len(importances)), importances)
    plt.yticks(range(len(importances)), meta_path_names)
    plt.xlabel('Feature Importance')
    plt.title('Meta-Path Importance for Classification')
    plt.tight_layout()
    plt.show()

Link Prediction Example
-----------------------

Predict Missing Edges
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from sklearn.linear_model import LogisticRegression
    
    # 1. Sample node pairs (positive and negative examples)
    positive_pairs = []  # Actual edges
    negative_pairs = []  # Non-edges (sampled)
    
    for u, v in network.core_network.edges():
        positive_pairs.append((u, v))
    
    # Sample negative examples
    import random
    nodes = list(network.get_nodes())
    while len(negative_pairs) < len(positive_pairs):
        u, v = random.sample(nodes, 2)
        if not network.core_network.has_edge(u, v):
            negative_pairs.append((u, v))
    
    # 2. Extract features for node pairs
    def pair_features(u, v, features, node_to_idx):
        idx_u = node_to_idx[u]
        idx_v = node_to_idx[v]
        # Concatenate, multiply, or subtract features
        return features[idx_u] * features[idx_v]
    
    # Build dataset
    X_pos = [pair_features(u, v, features, node_to_idx) for u, v in positive_pairs]
    X_neg = [pair_features(u, v, features, node_to_idx) for u, v in negative_pairs]
    
    X = X_pos + X_neg
    y = [1] * len(X_pos) + [0] * len(X_neg)
    
    # 3. Train-test split and classify
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
    
    clf = LogisticRegression()
    clf.fit(X_train, y_train)
    
    # 4. Evaluate
    accuracy = clf.score(X_test, y_test)
    print(f"Link prediction accuracy: {accuracy:.3f}")

Advanced Decomposition
----------------------

Custom Meta-Paths
~~~~~~~~~~~~~~~~~

Define domain-specific meta-paths:

.. code-block:: python

    # Academic domain
    academic_meta_paths = [
        ['author', 'paper', 'author'],                    # Co-authorship
        ['author', 'paper', 'venue', 'paper', 'author'],  # Same venue
        ['author', 'paper', 'paper', 'author'],           # Citation-based
        ['venue', 'paper', 'author', 'paper', 'venue'],   # Venue similarity
    ]
    
    features = decomposer.build_feature_matrix(
        network,
        target_nodes=author_nodes,
        meta_paths=academic_meta_paths
    )

Weighted Meta-Paths
~~~~~~~~~~~~~~~~~~~

Assign importance weights to different meta-paths:

.. code-block:: python

    # Define meta-paths with weights
    meta_path_weights = {
        'author-paper-author': 2.0,           # High importance
        'author-paper-venue': 1.0,            # Normal importance
        'author-paper-paper-author': 0.5      # Lower importance
    }
    
    # Apply weights to features
    weighted_features = decomposer.apply_weights(features, meta_path_weights)

Temporal Decomposition
~~~~~~~~~~~~~~~~~~~~~~

For temporal networks with timestamps:

.. code-block:: python

    # Decompose network at different time slices
    time_slices = [2018, 2019, 2020, 2021]
    
    temporal_features = []
    for year in time_slices:
        # Filter network to specific time period
        subnetwork = network.filter_by_time(year)
        
        # Decompose
        features = decomposer.run_decomposition(subnetwork, 'author')
        temporal_features.append(features)
    
    # Stack temporal features
    import numpy as np
    full_features = np.hstack(temporal_features)

Performance Optimization
------------------------

Caching Results
~~~~~~~~~~~~~~~

HINMINE automatically caches decomposition results:

.. code-block:: python

    # First run: computes and caches
    features1 = decomposer.run_decomposition(network, 'author')
    
    # Second run: loads from cache (much faster)
    features2 = decomposer.run_decomposition(network, 'author')

Cache is stored in ``.{md5_hash}`` files based on network content.

Parallel Processing
~~~~~~~~~~~~~~~~~~~

For large networks, process meta-paths in parallel:

.. code-block:: python

    from joblib import Parallel, delayed
    
    # Compute meta-path instances in parallel
    results = Parallel(n_jobs=-1)(
        delayed(decomposer.compute_meta_path_instances)(
            network, mp, target_nodes
        )
        for mp in meta_paths
    )

Sparse Representations
~~~~~~~~~~~~~~~~~~~~~~

Use sparse matrices for large feature spaces:

.. code-block:: python

    from scipy.sparse import csr_matrix
    
    # Convert to sparse format
    sparse_features = csr_matrix(features)
    
    # Use with scikit-learn
    from sklearn.svm import LinearSVC
    clf = LinearSVC()
    clf.fit(sparse_features, labels)

Best Practices
--------------

Meta-Path Selection
~~~~~~~~~~~~~~~~~~~

1. **Start simple** - Begin with short meta-paths (length 2-3)
2. **Domain knowledge** - Use meaningful paths for your domain
3. **Feature importance** - Analyze which paths are most informative
4. **Avoid redundancy** - Remove highly correlated meta-paths

Normalization
~~~~~~~~~~~~~

* **L1 normalization** - Good for interpretability (sum to 1)
* **L2 normalization** - Good for distance-based methods
* **Min-max scaling** - Good for neural networks
* **Z-score** - Good for algorithms sensitive to scale

Validation
~~~~~~~~~~

Always validate decomposition quality:

1. **Feature coverage** - Check that features capture relevant patterns
2. **Downstream performance** - Evaluate on actual task (classification, prediction)
3. **Interpretability** - Verify features are meaningful
4. **Computational cost** - Balance accuracy vs. efficiency

References
----------

**HINMINE:**

Kralj, J., Robnik-Šikonja, M., & Lavrač, N. (2018). HINMINE: heterogeneous information network mining with information retrieval heuristics. *Journal of Intelligent Information Systems*, 50(1), 29-61.

**Meta-paths:**

Sun, Y., Han, J., Yan, X., Yu, P. S., & Wu, T. (2011). PathSim: Meta path-based top-k similarity search in heterogeneous information networks. *VLDB*, 4(11), 992-1003.

**HIN Classification:**

Shi, C., Li, Y., Zhang, J., Sun, Y., & Philip, S. Y. (2016). A survey of heterogeneous information network analysis. *IEEE TKDE*, 29(1), 17-37.

Next Steps
----------

* :doc:`community_detection` - Community detection tutorial
* :doc:`multilayer_centrality` - Centrality measures
* :doc:`../algorithm_guide` - Algorithm selection
* Examples in ``examples/decomposition_and_classification/example_decomposition_and_classification.py``
