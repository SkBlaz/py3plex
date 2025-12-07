How to Run Community Detection on Multilayer Networks
======================================================

**Goal:** Identify groups of densely connected nodes in multilayer networks.

**Prerequisites:** A loaded network with multiple layers (see :doc:`load_and_build_networks`).

Quick Start: Louvain Algorithm
-------------------------------

The Louvain algorithm is fast and works well for most multilayer networks:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection import louvain_communities
    
    # Load network
    network = multinet.multi_layer_network()
    network.load_network("data.multiedgelist", input_type="multiedgelist")
    
    # Run Louvain
    communities = louvain_communities(network)
    
    # View results
    print(f"Found {len(set(communities.values()))} communities")
    
    for node, comm_id in list(communities.items())[:10]:
        print(f"Node {node} → Community {comm_id}")

**Expected output:**

.. code-block:: text

    Found 4 communities
    Node ('Alice', 'friends') → Community 0
    Node ('Bob', 'friends') → Community 0
    Node ('Carol', 'work') → Community 1

Multilayer-Specific: Multilayer Louvain
----------------------------------------

Optimizes multilayer modularity, accounting for inter-layer connections:

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_louvain import (
        multilayer_louvain
    )
    
    # Run multilayer Louvain
    communities = multilayer_louvain(
        network,
        omega=0.5  # Inter-layer coupling strength
    )
    
    print(f"Found {len(set(communities.values()))} communities")

The `omega` parameter controls how much inter-layer connections influence communities:

* ``omega=0``: Layers are independent (same as single-layer on each layer)
* ``omega=1``: Strong coupling (communities span layers)

Infomap Algorithm
-----------------

Infomap finds communities by minimizing information flow description:

.. code-block:: python

    from py3plex.algorithms.community_detection import infomap_communities
    
    communities = infomap_communities(network)
    
    print(f"Found {len(set(communities.values()))} communities")

Label Propagation
-----------------

Fast algorithm for large networks:

.. code-block:: python

    from py3plex.algorithms.community_detection import label_propagation
    
    communities = label_propagation(network)
    
    print(f"Found {len(set(communities.values()))} communities")

Analyzing Community Structure
------------------------------

Count Nodes Per Community
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from collections import Counter
    
    comm_sizes = Counter(communities.values())
    
    print("Community sizes:")
    for comm_id, size in comm_sizes.most_common():
        print(f"Community {comm_id}: {size} nodes")

Visualize Communities
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization import visualize_communities
    
    visualize_communities(
        network,
        communities,
        output_file="communities.png",
        show=True
    )

Export Communities
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    
    # Convert to DataFrame
    data = []
    for (node, layer), comm_id in communities.items():
        data.append({
            'node': node,
            'layer': layer,
            'community': comm_id
        })
    
    df = pd.DataFrame(data)
    df.to_csv("communities.csv", index=False)

Compare Algorithms
------------------

Run multiple algorithms and compare:

.. code-block:: python

    from py3plex.algorithms.community_detection import (
        louvain_communities,
        infomap_communities,
        label_propagation
    )
    from sklearn.metrics import adjusted_rand_score
    
    # Run algorithms
    louvain_comms = louvain_communities(network)
    infomap_comms = infomap_communities(network)
    label_prop_comms = label_propagation(network)
    
    # Compare (using adjusted Rand index)
    # Convert to lists in same order
    nodes = list(louvain_comms.keys())
    louvain_labels = [louvain_comms[n] for n in nodes]
    infomap_labels = [infomap_comms[n] for n in nodes]
    
    similarity = adjusted_rand_score(louvain_labels, infomap_labels)
    print(f"Louvain vs Infomap similarity: {similarity:.3f}")

Layer-Specific Communities
---------------------------

Detect communities in individual layers:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    layer = 'friends'
    
    # Extract single layer
    subgraph = Q.edges().from_layers(L[layer]).execute(network)
    
    # Run community detection on this layer
    layer_communities = louvain_communities(subgraph)
    
    print(f"Found {len(set(layer_communities.values()))} communities in {layer}")

Cross-Layer Community Analysis
-------------------------------

Check if communities are consistent across layers:

.. code-block:: python

    # Get communities for multiple layers
    layer_communities = {}
    
    for layer in network.get_layers():
        subgraph = Q.edges().from_layers(L[layer]).execute(network)
        layer_communities[layer] = louvain_communities(subgraph)
    
    # Compare community assignments across layers
    from sklearn.metrics import normalized_mutual_information_score as nmi
    
    layers = list(layer_communities.keys())
    for i in range(len(layers)):
        for j in range(i + 1, len(layers)):
            layer1, layer2 = layers[i], layers[j]
            
            # Get common nodes
            nodes1 = set(layer_communities[layer1].keys())
            nodes2 = set(layer_communities[layer2].keys())
            common = nodes1 & nodes2
            
            if common:
                labels1 = [layer_communities[layer1][n] for n in common]
                labels2 = [layer_communities[layer2][n] for n in common]
                
                similarity = nmi(labels1, labels2)
                print(f"{layer1} vs {layer2}: NMI = {similarity:.3f}")

Quality Metrics
---------------

Compute Modularity
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import calculate_modularity
    
    modularity = calculate_modularity(network, communities)
    print(f"Modularity: {modularity:.3f}")

Higher modularity (closer to 1) indicates better community structure.

Next Steps
----------

* **Visualize results:** :doc:`visualize_networks`
* **Understand algorithms:** :doc:`../concepts/algorithm_landscape`
* **API reference:** :doc:`../reference/algorithm_reference`
