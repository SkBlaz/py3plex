Node Embeddings
================

Generate node embeddings using Node2Vec and visualize them.

.. note::

    Node2Vec binary is no longer bundled with py3plex.
    
    **Options:**
    
    - Use pure Python alternatives: ``pip install node2vec`` or ``pip install pecanpy``
    - Download C++ binary from: https://github.com/snap-stanford/snap
    - Use py3plex's built-in random walk implementation

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.wrappers import train_node2vec_embedding
    from py3plex.visualization.embedding_visualization import embedding_visualization
    
    # Load network
    network = multinet.multi_layer_network().load_network(
        "../datasets/imdb_gml.gml", directed=True, input_type="gml")
    
    # Save as edgelist for Node2Vec
    network.save_network("../datasets/test.edgelist")
    
    try:
        # Generate embedding (assumes node2vec binary is in PATH)
        train_node2vec_embedding.call_node2vec_binary(
            "../datasets/test.edgelist",
            "../datasets/test_embedding.emb",
            binary="node2vec",
            weighted=False)
        
        # Load and visualize
        network.load_embedding("../datasets/test_embedding.emb")
        embedding_visualization.visualize_embedding(network)
    except FileNotFoundError:
        print("Node2Vec binary not found. Install with: pip install node2vec")

Examples
--------

See:

- ``example_n2v_embedding.py`` - Node2Vec embeddings
- ``example_embedding_visualization.py`` - Embedding visualization
- ``example_embedding_construction.py`` - Custom embeddings

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
