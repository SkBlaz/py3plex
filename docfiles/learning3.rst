Node Embeddings
================

Node embeddings transform network structure into continuous vector representations, enabling the application of machine learning algorithms to graph data. Each node is mapped to a fixed-length vector in a latent space where similar nodes (by network structure) are placed close together.

Why Use Node Embeddings?
------------------------

Node embeddings bridge the gap between graph-structured data and traditional machine learning:

**Feature Extraction:** Instead of manually engineering network features (degree, clustering coefficient, centrality), embeddings learn features automatically from the network structure. These learned features often capture complex structural patterns that are difficult to encode manually.

**Downstream Tasks:** Once nodes are embedded as vectors, you can use standard ML algorithms:

- **Classification:** Predict node labels using logistic regression or neural networks
- **Clustering:** Group similar nodes using k-means or hierarchical clustering
- **Link Prediction:** Predict missing edges using vector similarity
- **Visualization:** Project embeddings to 2D/3D for visual exploration

**Scalability:** Modern embedding algorithms like Node2Vec and DeepWalk scale to networks with millions of nodes, making them practical for large-scale analysis.

Node2Vec and DeepWalk Overview
-------------------------------

The two most popular embedding methods are based on random walks:

**DeepWalk:** Performs uniform random walks on the network, treating each walk as a "sentence" of nodes. These walks are fed to Word2Vec to learn node embeddings. Nodes that appear in similar walk contexts get similar embeddings.

**Node2Vec:** Extends DeepWalk with biased random walks controlled by parameters p (return parameter) and q (in-out parameter). This allows the algorithm to balance between exploring local neighborhoods (BFS-like) and discovering global structure (DFS-like).

.. note::

    Node2Vec binary is no longer bundled with py3plex.
    
    **Options:**
    
    - Use pure Python alternatives: ``pip install node2vec`` or ``pip install pecanpy``
    - Download C++ binary from: https://github.com/snap-stanford/snap
    - Use py3plex's built-in random walk implementation with external Word2Vec

Basic Usage
-----------

The following example demonstrates the complete embedding workflow: loading a network, generating embeddings, and visualizing the result:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.wrappers import train_node2vec_embedding
    from py3plex.visualization.embedding_visualization import embedding_visualization
    
    # Load network
    # IMDB dataset: actors connected if they appeared in the same movie
    network = multinet.multi_layer_network().load_network(
        "../datasets/imdb_gml.gml", directed=True, input_type="gml")
    
    # Save as edgelist for Node2Vec
    # Node2Vec expects a simple edge list format: "source target" per line
    network.save_network("../datasets/test.edgelist")
    
    try:
        # Generate embedding (assumes node2vec binary is in PATH)
        # This runs the external Node2Vec implementation
        train_node2vec_embedding.call_node2vec_binary(
            "../datasets/test.edgelist",      # Input graph
            "../datasets/test_embedding.emb", # Output embedding file
            binary="node2vec",                # Binary name
            weighted=False)                   # Unweighted edges
        
        # Load the generated embedding back into the network object
        network.load_embedding("../datasets/test_embedding.emb")
        
        # Visualize using t-SNE or PCA projection
        # Similar nodes (by network position) cluster together
        embedding_visualization.visualize_embedding(network)
    except FileNotFoundError:
        print("Node2Vec binary not found. Install with: pip install node2vec")

**Understanding the Workflow:**

1. **Load Network:** Import your network in any supported format
2. **Export Edgelist:** Node2Vec expects simple edge list input
3. **Generate Embedding:** Run the Node2Vec algorithm (external binary or Python package)
4. **Load Embedding:** Import the embedding vectors back into py3plex
5. **Visualize/Use:** Apply dimensionality reduction for visualization or use vectors for ML

Embedding Parameters
--------------------

When generating embeddings, several parameters control the quality and properties:

- **dimensions** (default: 128): Length of embedding vectors. Larger dimensions capture more information but require more memory.
- **walk_length** (default: 80): Number of steps per random walk. Longer walks capture more global structure.
- **num_walks** (default: 10): Number of walks starting from each node. More walks provide better sampling.
- **p** (Node2Vec only, default: 1): Return parameter. Lower values encourage backtracking.
- **q** (Node2Vec only, default: 1): In-out parameter. Lower values encourage exploration.

**Tuning Tips:**

- For community detection: Use lower q (explore structure)
- For local similarity: Use higher q (stay close)
- For large networks: Use shorter walks and fewer dimensions to reduce computation time

Using Py3plex's Built-in Random Walks
-------------------------------------

If you prefer a pure-Python solution without external binaries, combine py3plex's random walk implementation with gensim's Word2Vec:

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks
    from gensim.models import Word2Vec
    
    # Generate walks using py3plex
    walks = generate_walks(
        network.core_network,
        num_walks=10,
        walk_length=80,
        p=1.0, q=1.0,  # Node2Vec parameters
        seed=42
    )
    
    # Convert node tuples to strings for Word2Vec
    walks_str = [[str(node) for node in walk] for walk in walks]
    
    # Train Word2Vec model on walks
    model = Word2Vec(
        walks_str,
        vector_size=128,  # Embedding dimension
        window=10,        # Context window
        min_count=1,      # Include all nodes
        workers=4,        # Parallel processing
        epochs=10         # Training iterations
    )
    
    # Access embedding for a specific node
    node_embedding = model.wv[str(('node_id', 'layer_id'))]

Examples and Further Reading
----------------------------

For complete embedding examples and advanced use cases, see:

- ``example_n2v_embedding.py`` - Node2Vec embedding workflow
- ``example_embedding_visualization.py`` - Visualizing embeddings with t-SNE
- ``example_embedding_construction.py`` - Building custom embeddings
- ``example_link_prediction.py`` - Using embeddings for link prediction
- ``example_node_classification.py`` - Using embeddings for classification

**Academic References:**

- **DeepWalk:** Perozzi, B., et al. (2014). "DeepWalk: Online Learning of Social Representations." KDD.
- **Node2Vec:** Grover, A., & Leskovec, J. (2016). "node2vec: Scalable Feature Learning for Networks." KDD.

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
