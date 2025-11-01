Advanced Learning and Algorithms
==================================

This guide covers advanced topics for learning on networks, including random network generation, semi-supervised learning, and node embeddings.

.. contents:: Table of Contents
   :local:
   :depth: 2

Random Network Generation
=========================

Generate **synthetic multilayer networks** for testing and benchmarking.

.. code-block:: python

    from py3plex.core import random_generators
    
    # Generate Erdős-Rényi multilayer network
    network = random_generators.random_multilayer_ER(
        num_nodes=200, 
        num_layers=6, 
        probability=0.09, 
        directed=True)
    
    network.visualize_network(show=True, no_labels=True)

Use Cases
---------

* **Testing algorithms** on networks with known properties
* **Benchmarking performance** across different network sizes
* **Generating synthetic datasets** for validation
* **Creating baseline networks** for comparison

Examples
--------

See: ``example_random_generator.py``

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples

Label Propagation
==================

Semi-supervised learning on networks using label propagation.

Overview
--------

Label propagation is a **semi-supervised learning** algorithm that classifies nodes based on:

* **Labeled nodes** (training set)
* **Network structure** (edges between nodes)
* **Feature similarity** (optional node attributes)

The algorithm propagates labels through the network, assigning classes to unlabeled nodes based on their neighbors.

Basic Usage
-----------

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.network_classification import validate_label_propagation
    
    network = multinet.multi_layer_network().load_network(
        "../datasets/cora.mat", directed=False, input_type="sparse")
    
    # Run label propagation with different normalization schemes
    results = validate_label_propagation(
        network.core_network,
        network.labels,
        dataset_name="cora",
        repetitions=5,
        normalization_scheme="freq")

Normalization Schemes
---------------------

* **freq**: Frequency-based normalization
* **uniform**: Uniform weight distribution
* **standard**: Standard normalization

Applications
------------

* **Document classification** (citation networks)
* **Node classification** in social networks
* **Semi-supervised learning** with limited labeled data
* **Community-aware classification**

Examples
--------

See: ``example_label_propagation.py``

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples

Node Embeddings
================

Generate node embeddings using Node2Vec and visualize them.

Overview
--------

Node embeddings are **low-dimensional vector representations** of nodes that preserve:

* **Network structure** (neighborhood similarity)
* **Community structure** (cluster membership)
* **Path information** (random walk patterns)

These embeddings can be used for:

* **Node classification**
* **Link prediction**
* **Visualization** in 2D/3D space
* **Downstream machine learning tasks**

Basic Usage
-----------

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.wrappers import train_node2vec_embedding
    from py3plex.visualization.embedding_visualization import embedding_visualization
    
    # Load network
    network = multinet.multi_layer_network().load_network(
        "../datasets/imdb_gml.gml", directed=True, input_type="gml")
    
    # Save as edgelist for Node2Vec
    network.save_network("../datasets/test.edgelist")
    
    # Generate embedding
    train_node2vec_embedding.call_node2vec_binary(
        "../datasets/test.edgelist",
        "../datasets/test_embedding.emb",
        binary="../bin/node2vec",
        weighted=False)
    
    # Load and visualize
    network.load_embedding("../datasets/test_embedding.emb")
    embedding_visualization.visualize_embedding(network)

Embedding Methods
-----------------

py3plex supports multiple embedding methods:

Node2Vec
~~~~~~~~

* **Random walk-based** sampling
* **Flexible** exploration (BFS vs DFS bias)
* **Scalable** to large networks

DeepWalk
~~~~~~~~

* **Uniform random walks**
* **Simple** and fast
* **Good baseline** method

Custom Embeddings
~~~~~~~~~~~~~~~~~

You can also load custom embeddings from:

* **External tools** (GraRep, LINE, etc.)
* **Pre-trained embeddings**
* **Domain-specific methods**

Visualization
-------------

Embeddings can be visualized in 2D or 3D space:

.. code-block:: python

    from py3plex.visualization.embedding_visualization import embedding_visualization
    
    # 2D visualization with t-SNE
    embedding_visualization.visualize_embedding(
        network, 
        method="tsne",
        dimension=2)
    
    # 3D visualization with PCA
    embedding_visualization.visualize_embedding(
        network,
        method="pca", 
        dimension=3)

Examples
--------

See:

- ``example_n2v_embedding.py`` - Node2Vec embeddings
- ``example_embedding_visualization.py`` - Embedding visualization
- ``example_embedding_construction.py`` - Custom embeddings

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
