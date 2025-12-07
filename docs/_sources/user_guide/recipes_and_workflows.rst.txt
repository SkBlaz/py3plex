.. _recipes:

****************************
Analysis Recipes & Workflows
****************************

This guide provides **practical recipes** for **common analysis workflows** in py3plex. 
Each recipe is a **complete, ready-to-use solution** for a real-world task.

.. admonition:: DSL for Rapid Analysis
   :class: dsl-example

   Many recipes can be expressed concisely using the DSL:

   .. code-block:: python

       from py3plex.dsl import Q, L

       # Quick hub identification
       hubs = (
           Q.nodes()
            .where(degree__gt=5)
            .compute("betweenness_centrality")
            .order_by("-betweenness_centrality")
            .limit(10)
            .execute(network)
       )

       # Multi-layer comparison
       for layer_name in ["social", "work", "family"]:
           result = (
               Q.nodes()
                .from_layers(L[layer_name])
                .compute("degree", "clustering")
                .execute(network)
           )
           print(f"{layer_name}: {result.count} nodes")

   See the DSL recipes section below for more patterns!

**Related Example Scripts:**

Many recipes have corresponding runnable example scripts in the repository:

* I/O examples: ``examples/io_and_data/example_IO.py``, ``examples/io_and_data/example_new_io.py``
* Community detection: ``examples/communities/example_community_detection.py``
* Network statistics: ``examples/network_analysis/example_multilayer_statistics.py``
* Visualization: ``examples/visualization/example_multilayer_visualization.py``
* DSL queries: ``examples/network_analysis/example_dsl_queries.py``
* Complete pipelines: ``examples/pipelines/example_6_complex_pipeline.py``

.. contents:: Recipe Index
   :local:
   :depth: 2

========================
Data Import & Setup
========================

Recipe 1: Load Network from Multiple File Formats
==================================================

**Task:** Load **multilayer networks** from various **file formats** (edgelist, GraphML, CSV).

**Script:** ``examples/io_and_data/example_IO.py``

.. code-block:: python

    from py3plex.core import multinet
    
    # From multiedgelist (node1, layer1, node2, layer2, weight)
    network = multinet.multi_layer_network().load_network(
        "data/network.txt",
        input_type="multiedgelist",
        directed=False
    )
    
    # From GraphML
    network = multinet.multi_layer_network().load_network(
        "data/network.graphml",
        input_type="graphml"
    )
    
    # From edges list programmatically
    network = multinet.multi_layer_network()
    network.add_edges([
        ['A', 'layer1', 'B', 'layer1', 1.0],
        ['B', 'layer1', 'C', 'layer1', 1.0],
        ['A', 'layer2', 'C', 'layer2', 0.5],
    ], input_type="list")
    
    # Verify the network
    network.basic_stats()

**Expected Output:**

.. code-block:: text

    Number of nodes: 3
    Number of edges: 3
    Number of unique nodes (as node-layer tuples): 5
    Number of unique node IDs (across all layers): 3
    Nodes per layer:
      Layer 'layer1': 3 nodes
      Layer 'layer2': 2 nodes

**When to use:** Starting any **analysis project** with external data.


Recipe 2: Create Synthetic Benchmark Networks
==============================================

**Task:** Generate **synthetic multilayer networks** for **testing algorithms**.

**Script:** ``examples/getting_started/example_random_generator.py``

.. code-block:: python

    from py3plex.core.random_generators import random_multilayer_ER
    import numpy as np
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Create a random Erdős-Rényi multilayer network
    # Parameters: n_nodes, n_layers, edge_probability
    network = random_multilayer_ER(
        n=100,        # 100 nodes
        L=3,          # 3 layers
        p=0.1,        # 10% edge probability
        directed=False
    )
    
    network.basic_stats()

**When to use:** **Algorithm validation**, **testing**, **benchmarking**, or when real data is unavailable.


Recipe 3: Convert Between Network Formats
==========================================

**Task:** Export networks to **different formats** for use in **other tools**.

.. code-block:: python

    from py3plex.core import multinet
    
    # Load network
    network = multinet.multi_layer_network().load_network(
        "input.txt",
        input_type="multiedgelist"
    )
    
    # Save as GraphML (standard format, compatible with Gephi, Cytoscape)
    network.save_network("output.graphml", output_type="graphml")
    
    # Save as edge list with node mapping
    inverse_map = network.serialize_to_edgelist("output_edges.txt")
    
    # Save as pickle (preserves all Python objects)
    import pickle
    with open("network.pkl", "wb") as f:
        pickle.dump(network, f)

**When to use:** Sharing data with collaborators, importing to visualization tools, or archiving results.


========================================
Network Exploration & Analysis
========================================

Recipe 4: Quick Network Summary
================================

**Task:** Get comprehensive overview of network structure.

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network().load_network(
        "data/network.txt",
        input_type="multiedgelist"
    )
    
    # Basic statistics
    print("=== Basic Statistics ===")
    network.basic_stats()
    
    # Layer information
    layers = network.get_layers()
    print(f"\nLayers: {layers}")
    print(f"Number of layers: {len(layers)}")
    
    # Node and edge counts
    nodes = list(network.get_nodes())
    edges = list(network.get_edges())
    print(f"Total nodes: {len(nodes)}")
    print(f"Total edges: {len(edges)}")
    
    # Get unique nodes (nodes may appear in multiple layers)
    unique_nodes = set([n[0] for n in nodes])
    print(f"Unique nodes: {len(unique_nodes)}")

**Expected Output:**

.. code-block:: text

    === Basic Statistics ===
    Number of nodes: 250
    Number of edges: 180
    Number of unique nodes (as node-layer tuples): 250
    Number of unique node IDs (across all layers): 120
    Nodes per layer:
      Layer 'collaboration': 85 nodes
      Layer 'citation': 90 nodes
      Layer 'coauthor': 75 nodes
    
    Layers: ['collaboration', 'citation', 'coauthor']
    Number of layers: 3
    Total nodes: 250
    Total edges: 180
    Unique nodes: 120

**When to use:** Initial data exploration, quality checks, reporting.


Recipe 5: Layer-by-Layer Analysis
==================================

**Task:** Analyze each layer independently and compare properties.

.. code-block:: python

    from py3plex.core import multinet
    import networkx as nx
    
    network = multinet.multi_layer_network().load_network(
        "data/network.txt",
        input_type="multiedgelist"
    )
    
    # Analyze each layer
    layers = network.get_layers()
    layer_stats = {}
    
    for layer_name in layers:
        # Extract single layer
        layer = network.subnetwork([layer_name], subset_by="layers")
        
        # Compute layer statistics
        stats = {}
        stats['nodes'] = len(list(layer.get_nodes()))
        stats['edges'] = len(list(layer.get_edges()))
        
        # NetworkX metrics on layer
        G = layer.core_network
        if len(G) > 0:  # Check if layer has nodes
            stats['density'] = nx.density(G)
            stats['avg_degree'] = sum(dict(G.degree()).values()) / len(G)
            
            # Check connectivity
            if not layer.directed:
                stats['connected'] = nx.is_connected(G)
                if stats['connected']:
                    stats['diameter'] = nx.diameter(G)
            
        layer_stats[layer_name] = stats
        
    # Display results
    print("\n=== Layer-by-Layer Analysis ===")
    for layer, stats in layer_stats.items():
        print(f"\nLayer: {layer}")
        for metric, value in stats.items():
            print(f"  {metric}: {value}")

**When to use:** Understanding layer-specific properties, identifying important layers.


Recipe 6: Compute Multilayer Statistics
========================================

**Task:** Calculate multilayer-specific metrics that account for cross-layer structure.

**Script:** ``examples/network_analysis/example_multilayer_statistics.py``

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    network = multinet.multi_layer_network().load_network(
        "data/network.txt",
        input_type="multiedgelist"
    )
    
    layers = network.get_layers()
    
    # === Layer-Level Statistics ===
    print("=== Layer Statistics ===")
    for layer in layers:
        density = mls.layer_density(network, layer)
        print(f"Layer {layer} density: {density:.4f}")
    
    # Layer diversity
    entropy = mls.entropy_of_multiplexity(network)
    print(f"\nLayer diversity (entropy): {entropy:.4f} bits")
    
    # === Node-Level Statistics ===
    print("\n=== Node Activity ===")
    sample_nodes = list(network.get_nodes())[:5]
    for node_tuple in sample_nodes:
        node = node_tuple[0]  # Extract node name
        activity = mls.node_activity(network, node)
        print(f"Node {node} active in {activity*100:.1f}% of layers")
    
    # === Cross-Layer Analysis ===
    if len(layers) >= 2:
        print("\n=== Cross-Layer Similarity ===")
        layer1, layer2 = str(layers[0]), str(layers[1])
        
        # Cosine similarity of adjacency matrices
        similarity = mls.layer_similarity(network, layer1, layer2, method='cosine')
        print(f"Cosine similarity ({layer1} vs {layer2}): {similarity:.4f}")
        
        # Jaccard similarity of edge sets
        overlap = mls.edge_overlap(network, layer1, layer2)
        print(f"Edge overlap (Jaccard): {overlap:.4f}")
    
    # === Versatility Analysis ===
    print("\n=== Node Versatility (Cross-Layer Importance) ===")
    versatility = mls.versatility_centrality(network, centrality_type='degree')
    top_nodes = sorted(versatility.items(), key=lambda x: x[1], reverse=True)[:5]
    for node, score in top_nodes:
        print(f"  {node}: {score:.4f}")

**When to use:** Quantifying multilayer structure, comparing layers, identifying versatile nodes.


========================================
Centrality & Node Importance
========================================

Recipe 7: Single-Layer Centrality Analysis
===========================================

**Task:** Identify important nodes within individual layers.

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network().load_network(
        "data/network.txt",
        input_type="multiedgelist"
    )
    
    # Select a layer
    layers = network.get_layers()
    target_layer = [str(layers[0])]
    layer = network.subnetwork(target_layer, subset_by="layers")
    
    # Compute multiple centrality measures
    centrality_measures = {
        'degree': layer.monoplex_nx_wrapper("degree_centrality"),
        'betweenness': layer.monoplex_nx_wrapper("betweenness_centrality"),
        'closeness': layer.monoplex_nx_wrapper("closeness_centrality"),
        'eigenvector': layer.monoplex_nx_wrapper("eigenvector_centrality"),
    }
    
    # Display top nodes for each measure
    print(f"=== Centrality Analysis for Layer {target_layer[0]} ===\n")
    for measure_name, scores in centrality_measures.items():
        print(f"{measure_name.capitalize()} Centrality (Top 5):")
        top_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
        for node, score in top_nodes:
            print(f"  {node}: {score:.4f}")
        print()

**When to use:** Identifying influential nodes, hub detection, network simplification.


Recipe 8: Multiplex Participation Coefficient
==============================================

**Task:** Measure how evenly nodes participate across layers in a multiplex network.

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.multicentrality import multiplex_participation_coefficient
    
    # Load or create multiplex network (same nodes across all layers)
    network = multinet.multi_layer_network().load_network(
        "data/multiplex_network.txt",
        input_type="multiedgelist"
    )
    
    # Compute MPC (requires true multiplex: identical node set per layer)
    try:
        mpc = multiplex_participation_coefficient(
            network,
            normalized=True,
            check_multiplex=True
        )
        
        # Display results
        print("=== Multiplex Participation Coefficient ===")
        print("(0 = active in one layer only, 1 = equally active across all layers)\n")
        
        # Sort by MPC score
        sorted_nodes = sorted(mpc.items(), key=lambda x: x[1], reverse=True)
        
        print("Top 10 most versatile nodes:")
        for node, score in sorted_nodes[:10]:
            print(f"  {node}: {score:.4f}")
        
        print("\nTop 10 most specialized nodes:")
        for node, score in sorted_nodes[-10:]:
            print(f"  {node}: {score:.4f}")
            
    except ValueError as e:
        print(f"Error: {e}")
        print("Network is not a true multiplex (layers have different node sets)")

**When to use:** Analyzing multiplex networks, identifying cross-layer hubs, understanding node specialization.


========================================
Community Detection
========================================

Recipe 9: Multilayer Community Detection
=========================================

**Task:** Detect communities that span multiple layers.

**Script:** ``examples/communities/example_community_detection.py``

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    from collections import Counter
    
    network = multinet.multi_layer_network().load_network(
        "data/network.txt",
        input_type="multiedgelist"
    )
    
    # Run multilayer Louvain algorithm
    # gamma: resolution parameter (higher = more communities)
    # omega: inter-layer coupling strength (higher = communities span layers)
    partition = louvain_multilayer(
        network,
        gamma=1.0,      # Standard resolution
        omega=1.0,      # Standard coupling
        random_state=42 # For reproducibility
    )
    
    # Analyze results
    num_communities = len(set(partition.values()))
    print(f"Detected {num_communities} communities")
    
    # Community size distribution
    community_sizes = Counter(partition.values())
    print("\nTop 10 communities by size:")
    for comm_id, size in community_sizes.most_common(10):
        print(f"  Community {comm_id}: {size} nodes")
    
    # Check which nodes are in largest community
    largest_comm = community_sizes.most_common(1)[0][0]
    largest_comm_nodes = [node for node, comm in partition.items() 
                          if comm == largest_comm]
    print(f"\nNodes in largest community: {largest_comm_nodes[:10]}...")

**When to use:** Understanding network organization, identifying functional modules, clustering nodes.


Recipe 10: Compare Community Detection Algorithms
==================================================

**Task:** Run multiple community detection methods and compare results.

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection import community_wrapper as cw
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    from collections import Counter
    import numpy as np
    
    network = multinet.multi_layer_network().load_network(
        "data/network.txt",
        input_type="multiedgelist"
    )
    
    # Method 1: Single-layer Louvain on aggregated network
    partition_louvain = cw.louvain_communities(network)
    
    # Method 2: Multilayer Louvain
    partition_multilayer = louvain_multilayer(
        network,
        gamma=1.0,
        omega=1.0,
        random_state=42
    )
    
    # Compare results
    print("=== Community Detection Comparison ===\n")
    print(f"Single-layer Louvain: {len(set(partition_louvain.values()))} communities")
    print(f"Multilayer Louvain: {len(set(partition_multilayer.values()))} communities")
    
    # Calculate normalized mutual information (if sklearn available)
    try:
        from sklearn.metrics import normalized_mutual_info_score
        
        # Align node sets
        common_nodes = set(partition_louvain.keys()) & set(partition_multilayer.keys())
        labels1 = [partition_louvain[n] for n in common_nodes]
        labels2 = [partition_multilayer[n] for n in common_nodes]
        
        nmi = normalized_mutual_info_score(labels1, labels2)
        print(f"\nNormalized Mutual Information: {nmi:.4f}")
        print("(1.0 = identical partitions, 0.0 = independent)")
    except ImportError:
        print("\nInstall scikit-learn to compute NMI: pip install scikit-learn")

**When to use:** Method validation, algorithm selection, robustness analysis.


========================================
Visualization
========================================

Recipe 11: Basic Network Visualization
=======================================

**Task:** Create publication-ready network visualizations.

**Script:** ``examples/visualization/example_multilayer_visualization.py``

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.visualization.multilayer import hairball_plot
    import matplotlib
    matplotlib.use('Agg')  # For non-interactive environments
    import matplotlib.pyplot as plt
    
    network = multinet.multi_layer_network().load_network(
        "data/network.txt",
        input_type="multiedgelist"
    )
    
    # Get network in visualization format
    network_colors, graph = network.get_layers(style="hairball")
    
    # Create visualization
    plt.figure(figsize=(12, 12))
    hairball_plot(
        graph,
        network_colors,
        layout_algorithm="force",        # Options: "force", "circular", "spring"
        layout_parameters={"iterations": 100},
        node_size=5,
        edge_width=0.5,
        alpha_channel=0.8,
        scale_by_size=True
    )
    plt.title("Multilayer Network", fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig("network_viz.png", dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    print("Visualization saved to network_viz.png")

**When to use:** Presentations, papers, reports, exploratory analysis.


Recipe 12: Visualize Communities on Network
============================================

**Task:** Color nodes by community membership in network plot.

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.visualization.multilayer import hairball_plot
    from py3plex.visualization.colors import colors_default
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    from collections import Counter
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    
    network = multinet.multi_layer_network().load_network(
        "data/network.txt",
        input_type="multiedgelist"
    )
    
    # Detect communities
    partition = louvain_multilayer(network, gamma=1.0, omega=1.0, random_state=42)
    
    # Select top N communities to color
    top_n = 10
    community_counts = Counter(partition.values())
    top_communities = [c for c, _ in community_counts.most_common(top_n)]
    
    # Create color mapping
    color_map = dict(zip(top_communities, colors_default[:top_n]))
    
    # Assign colors to nodes
    network_colors = [
        color_map.get(partition.get(node), "lightgray")
        for node in network.get_nodes()
    ]
    
    # Get network for visualization
    _, graph = network.get_layers(style="hairball")
    
    # Create plot
    plt.figure(figsize=(14, 14))
    hairball_plot(
        graph,
        network_colors,
        layout_algorithm="force",
        layout_parameters={"iterations": 150},
        node_size=8,
        edge_width=0.5,
        alpha_channel=0.7,
        scale_by_size=True
    )
    plt.title(f"Network with {top_n} Largest Communities", 
              fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig("network_communities.png", dpi=150, 
                bbox_inches='tight', facecolor='white')
    plt.close()
    print("Community visualization saved to network_communities.png")

**When to use:** Visualizing analysis results, understanding community structure.


========================================
Advanced Workflows
========================================

Recipe 13: Complete Analysis Pipeline
======================================

**Task:** Full workflow from data loading to results export.

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    from collections import Counter
    import json
    import numpy as np
    
    # Set random seed
    np.random.seed(42)
    
    # === 1. Load Data ===
    print("=== Loading Network ===")
    network = multinet.multi_layer_network().load_network(
        "data/network.txt",
        input_type="multiedgelist",
        directed=False
    )
    network.basic_stats()
    
    # === 2. Compute Statistics ===
    print("\n=== Computing Multilayer Statistics ===")
    layers = network.get_layers()
    
    stats = {
        'num_layers': len(layers),
        'layer_densities': {},
        'layer_diversity': mls.entropy_of_multiplexity(network),
    }
    
    for layer in layers:
        stats['layer_densities'][str(layer)] = mls.layer_density(network, layer)
    
    # Versatility
    versatility = mls.versatility_centrality(network, centrality_type='degree')
    top_versatile = sorted(versatility.items(), key=lambda x: x[1], reverse=True)[:10]
    stats['top_versatile_nodes'] = {str(k): float(v) for k, v in top_versatile}
    
    # === 3. Community Detection ===
    print("\n=== Detecting Communities ===")
    partition = louvain_multilayer(network, gamma=1.0, omega=1.0, random_state=42)
    community_sizes = Counter(partition.values())
    
    stats['num_communities'] = len(set(partition.values()))
    stats['community_sizes'] = dict(community_sizes.most_common(10))
    
    # === 4. Export Results ===
    print("\n=== Exporting Results ===")
    
    # Save statistics as JSON
    with open("analysis_results.json", "w") as f:
        json.dump(stats, f, indent=2)
    print("Statistics saved to analysis_results.json")
    
    # Save community assignments
    with open("communities.txt", "w") as f:
        for node, comm in partition.items():
            f.write(f"{node}\t{comm}\n")
    print("Communities saved to communities.txt")
    
    # Save processed network
    network.save_network("processed_network.graphml", output_type="graphml")
    print("Network saved to processed_network.graphml")
    
    print("\n=== Analysis Complete ===")

**When to use:** Reproducible research workflows, batch processing, automated analysis.


Recipe 14: Network Comparison Study
====================================

**Task:** Compare multiple networks systematically.

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    import pandas as pd
    import numpy as np
    
    # List of networks to compare
    network_files = [
        ("Network A", "data/network_a.txt"),
        ("Network B", "data/network_b.txt"),
        ("Network C", "data/network_c.txt"),
    ]
    
    results = []
    
    for name, filepath in network_files:
        print(f"\nAnalyzing {name}...")
        
        # Load network
        network = multinet.multi_layer_network().load_network(
            filepath,
            input_type="multiedgelist",
            directed=False
        )
        
        # Compute metrics
        layers = network.get_layers()
        nodes = list(network.get_nodes())
        edges = list(network.get_edges())
        
        metrics = {
            'Network': name,
            'Layers': len(layers),
            'Total Nodes': len(nodes),
            'Unique Nodes': len(set([n[0] for n in nodes])),
            'Total Edges': len(edges),
            'Layer Diversity': mls.entropy_of_multiplexity(network),
        }
        
        # Average layer density
        densities = [mls.layer_density(network, layer) for layer in layers]
        metrics['Avg Layer Density'] = np.mean(densities)
        metrics['Std Layer Density'] = np.std(densities)
        
        results.append(metrics)
    
    # Create comparison table
    df = pd.DataFrame(results)
    print("\n=== Network Comparison ===")
    print(df.to_string(index=False))
    
    # Save to CSV
    df.to_csv("network_comparison.csv", index=False)
    print("\nComparison saved to network_comparison.csv")

**When to use:** Comparative studies, evaluating datasets, selecting networks for analysis.


Recipe 15: Random Walks for Node Embeddings
============================================

**Task:** Generate node embeddings using random walks (Node2Vec approach).

**Script:** ``examples/advanced/example_random_walks.py``

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.general.walkers import generate_walks, node2vec_walk
    import numpy as np
    
    # Set random seed
    np.random.seed(42)
    
    network = multinet.multi_layer_network().load_network(
        "data/network.txt",
        input_type="multiedgelist"
    )
    
    # Get core NetworkX graph
    G = network.core_network
    
    # Generate random walks
    # p: return parameter (higher = less likely to return to previous node)
    # q: in-out parameter (higher = more BFS-like, lower = more DFS-like)
    walks = generate_walks(
        G,
        num_walks=10,      # Number of walks per node
        walk_length=80,    # Length of each walk
        p=1.0,             # Return parameter
        q=1.0,             # In-out parameter
        seed=42
    )
    
    print(f"Generated {len(walks)} random walks")
    print(f"First walk (truncated): {walks[0][:10]}...")
    
    # Use walks for downstream tasks:
    # 1. Train Word2Vec model (if gensim available)
    try:
        from gensim.models import Word2Vec
        
        # Convert walks to strings for Word2Vec
        walks_str = [[str(node) for node in walk] for walk in walks]
        
        # Train embedding model
        model = Word2Vec(
            walks_str,
            vector_size=128,    # Embedding dimension
            window=5,           # Context window
            min_count=1,
            sg=1,               # Skip-gram
            workers=4,
            epochs=5,
            seed=42
        )
        
        print(f"\nTrained embedding model with {len(model.wv)} nodes")
        
        # Get embedding for a node
        sample_node = str(list(G.nodes())[0])
        if sample_node in model.wv:
            embedding = model.wv[sample_node]
            print(f"Embedding for node {sample_node}: {embedding[:5]}... (dim={len(embedding)})")
            
            # Find similar nodes
            similar = model.wv.most_similar(sample_node, topn=5)
            print(f"\nMost similar nodes to {sample_node}:")
            for node, similarity in similar:
                print(f"  {node}: {similarity:.4f}")
        
        # Save embeddings
        model.wv.save_word2vec_format("node_embeddings.txt")
        print("\nEmbeddings saved to node_embeddings.txt")
        
    except ImportError:
        print("\nInstall gensim for embedding generation: pip install gensim")

**When to use:** Node classification, link prediction, network clustering, feature extraction.


========================================
Performance & Optimization
========================================

Recipe 16: Handle Large Networks Efficiently
=============================================

**Task:** Process large multilayer networks without running out of memory.

.. code-block:: python

    from py3plex.core import multinet
    import gc
    
    # === 1. Load network efficiently ===
    # Use generators instead of loading all at once
    network = multinet.multi_layer_network()
    
    # For very large files, load in chunks or stream
    # (This is a conceptual example - actual implementation may vary)
    
    # === 2. Process layers independently ===
    layers = network.get_layers()
    
    layer_results = {}
    for layer_name in layers:
        print(f"Processing layer {layer_name}...")
        
        # Extract and process one layer at a time
        layer = network.subnetwork([layer_name], subset_by="layers")
        
        # Compute statistics for this layer
        nodes = len(list(layer.get_nodes()))
        edges = len(list(layer.get_edges()))
        
        layer_results[str(layer_name)] = {'nodes': nodes, 'edges': edges}
        
        # Clean up to free memory
        del layer
        gc.collect()
    
    print("\n=== Results ===")
    for layer, stats in layer_results.items():
        print(f"{layer}: {stats['nodes']} nodes, {stats['edges']} edges")
    
    # === 3. Use sparse representations ===
    # When computing supra-adjacency matrix
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)
    print(f"\nSupra-adjacency matrix: {supra_adj.shape} (sparse)")
    
    # === 4. Sample for exploratory analysis ===
    # For visualization or initial exploration, work with a sample
    all_nodes = list(network.get_nodes())
    import random
    random.seed(42)
    sample_size = min(1000, len(all_nodes))
    sampled_nodes = random.sample(all_nodes, sample_size)
    
    # Create subnetwork with sampled nodes
    # (Implementation depends on network structure)
    print(f"\nSampled {sample_size} nodes for exploratory analysis")

**When to use:** Networks with >10,000 nodes, limited RAM, large-scale studies.

**Tips:**
- Process layers sequentially rather than all at once
- Use sparse matrices for large supra-adjacency representations
- Sample networks for visualization and initial exploration
- Save intermediate results to disk
- Use generators and iterators instead of lists


Recipe 17: Benchmark and Profile Your Analysis
===============================================

**Task:** Measure performance and identify bottlenecks.

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    import time
    import psutil
    import os
    
    def get_memory_usage():
        """Get current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    # Load network
    print("=== Performance Benchmarking ===\n")
    start_mem = get_memory_usage()
    
    start = time.time()
    network = multinet.multi_layer_network().load_network(
        "data/network.txt",
        input_type="multiedgelist"
    )
    load_time = time.time() - start
    load_mem = get_memory_usage() - start_mem
    
    print(f"Network loading:")
    print(f"  Time: {load_time:.3f} seconds")
    print(f"  Memory: {load_mem:.2f} MB")
    
    # Benchmark statistics computation
    start = time.time()
    network.basic_stats()
    stats_time = time.time() - start
    print(f"\nBasic statistics:")
    print(f"  Time: {stats_time:.3f} seconds")
    
    # Benchmark community detection
    start_mem = get_memory_usage()
    start = time.time()
    partition = louvain_multilayer(network, gamma=1.0, omega=1.0, random_state=42)
    comm_time = time.time() - start
    comm_mem = get_memory_usage() - start_mem
    
    print(f"\nCommunity detection:")
    print(f"  Time: {comm_time:.3f} seconds")
    print(f"  Memory: {comm_mem:.2f} MB")
    print(f"  Communities found: {len(set(partition.values()))}")
    
    # Total resource usage
    print(f"\n=== Total Performance ===")
    print(f"Total time: {load_time + stats_time + comm_time:.3f} seconds")
    print(f"Peak memory: {get_memory_usage():.2f} MB")

**When to use:** Optimizing workflows, comparing algorithms, capacity planning.

**Note:** Requires ``psutil`` package: ``pip install psutil``


========================================
Tips & Best Practices
========================================

General Tips
============

1. **Always set random seeds** for reproducibility::

    import numpy as np
    np.random.seed(42)

2. **Verify network structure** after loading::

    network.basic_stats()  # Quick sanity check

3. **Handle errors gracefully**::

    try:
        result = network.some_operation()
    except Exception as e:
        print(f"Operation failed: {e}")

4. **Save intermediate results** for long analyses::

    import pickle
    with open("checkpoint.pkl", "wb") as f:
        pickle.dump(results, f)

5. **Use appropriate file formats**:
   
   - GraphML: Standard, compatible with other tools
   - Pickle: Fast, preserves Python objects, not portable
   - Edgelist: Simple, human-readable, large file size


Performance Tips
================

1. **For large networks**, process layers independently
2. **Use sparse matrices** when working with supra-adjacency
3. **Sample networks** for visualization (>1000 nodes gets crowded)
4. **Profile your code** to find bottlenecks
5. **Close plots** after saving to free memory: ``plt.close()``


Visualization Tips
==================

1. **Choose layout carefully**:
   
   - Force-directed: General purpose, slow for >5000 nodes
   - Circular: Fast, good for small networks
   - Spring: Balance between quality and speed

2. **Adjust node size** based on network size::

    node_size = max(1, 100 / np.sqrt(num_nodes))

3. **Use alpha channel** for edge-dense networks::

    alpha_channel=0.3  # More transparent

4. **Save high-resolution** for publications::

    plt.savefig("figure.png", dpi=300)


Community Detection Tips
=========================

1. **Tune resolution parameter** (gamma):
   
   - Higher gamma → more, smaller communities
   - Lower gamma → fewer, larger communities

2. **Tune coupling parameter** (omega) for multilayer:
   
   - Higher omega → communities span layers
   - Lower omega → layer-specific communities

3. **Run multiple times** with different random seeds to check stability

4. **Compare multiple algorithms** to validate findings


========================================
Common Issues & Solutions
========================================

Issue: "Network appears to be empty"
=====================================

**Cause:** Incorrect file format or delimiter.

**Solution:**::

    # Check file format
    with open("data.txt", "r") as f:
        print(f.readlines()[:5])  # Inspect first lines
    
    # Try different input_type
    network = multinet.multi_layer_network().load_network(
        "data.txt",
        input_type="multiedgelist"  # or "edgelist", "graphml"
    )


Issue: "No module named 'community'"
=====================================

**Cause:** Optional dependency not installed.

**Solution:**::

    pip install python-louvain


Issue: "Visualization doesn't appear"
======================================

**Cause:** Using non-interactive backend or missing display.

**Solution:**::

    import matplotlib
    matplotlib.use('Agg')  # For saving files
    import matplotlib.pyplot as plt
    
    # ... create plot ...
    plt.savefig("output.png")  # Save instead of show


Issue: "Memory error with large network"
=========================================

**Cause:** Loading entire network into RAM at once.

**Solution:** See Recipe 16 for memory-efficient processing.


Issue: "Community detection is slow"
=====================================

**Cause:** Large network or complex structure.

**Solution:**::

    # Use simpler algorithm for quick results
    from py3plex.algorithms.community_detection import community_wrapper as cw
    partition = cw.louvain_communities(network)  # Faster than multilayer


========================================
Further Reading
========================================

**Documentation:**

- Installation guide - See main documentation
- Quick start tutorial - See main documentation  
- Core concepts - See main documentation
- Algorithm selection guide - See main documentation

**Examples:**

See ``examples/`` directory for 50+ complete, working examples covering all major functionality.

**Research:**

- Kivelä et al. (2014) - Multilayer networks theory
- De Domenico et al. (2013) - Mathematical framework
- See Citations section in main documentation for complete reference list

========================
DSL Query Recipes
========================

The py3plex DSL provides powerful, concise syntax for network queries. These recipes showcase common patterns.

Recipe 18: Hub Identification with DSL
=======================================

**Task:** Find and rank influential nodes across layers using the DSL.

.. admonition:: DSL Example: Hub Identification
   :class: dsl-example

   .. code-block:: python

       from py3plex.core import multinet
       from py3plex.dsl import Q, L

       # Load network
       network = multinet.multi_layer_network().load_network(
           "data/network.txt", input_type="multiedgelist"
       )

       # Find top 20 hubs by betweenness centrality
       hubs = (
           Q.nodes()
            .where(degree__gt=3)  # Pre-filter by degree for efficiency
            .compute("betweenness_centrality", "degree", "clustering")
            .order_by("-betweenness_centrality")
            .limit(20)
            .export_csv("top_hubs.csv")
            .execute(network)
       )

       # Display results
       df = hubs.to_pandas()
       print(df)

**When to use:** Identifying key players, finding bridge nodes, influence analysis.


Recipe 19: Multi-Layer Comparative Analysis
============================================

**Task:** Compare network structure across different layers using DSL.

.. admonition:: DSL Example: Layer Comparison
   :class: dsl-example

   .. code-block:: python

       from py3plex.dsl import Q, L
       import pandas as pd

       # Analyze each layer separately
       layers = ["social", "work", "family"]
       results = []

       for layer_name in layers:
           result = (
               Q.nodes()
                .from_layers(L[layer_name])
                .compute("degree", "betweenness_centrality", "clustering")
                .execute(network)
           )
           
           # Calculate layer-level statistics
           df = result.to_pandas()
           layer_stats = {
               'layer': layer_name,
               'nodes': result.count,
               'avg_degree': df['degree'].mean(),
               'max_centrality': df['betweenness_centrality'].max(),
               'avg_clustering': df['clustering'].mean(),
           }
           results.append(layer_stats)

       # Create comparison table
       comparison_df = pd.DataFrame(results)
       print(comparison_df)

**When to use:** Understanding layer-specific properties, detecting structural differences.


Recipe 20: Advanced Filtering and Export
=========================================

**Task:** Complex multi-criteria filtering with automated export.

.. admonition:: DSL Example: Advanced Filtering
   :class: dsl-example

   .. code-block:: python

       from py3plex.dsl import Q, L

       # Find nodes that meet multiple criteria
       result = (
           Q.nodes()
            # Combine layers using set operations
            .from_layers(L["social"] + L["work"] - L["bots"])
            # Multiple filter conditions
            .where(degree__gte=5, clustering__gt=0.3)
            # Compute multiple measures
            .compute("betweenness_centrality", "pagerank", "degree")
            # Sort and limit
            .order_by("-pagerank")
            .limit(50)
            # Export in multiple formats
            .export_json("filtered_nodes.json", orient="records")
            .execute(network)
       )

       # Also available as pandas DataFrame
       df = result.to_pandas()
       
       # Or as NetworkX subgraph
       subgraph = result.to_networkx(network)

**When to use:** Targeted analysis, automated reporting, filtering complex networks.


Recipe 21: Parameterized Query Templates
=========================================

**Task:** Create reusable query templates for systematic analysis.

.. admonition:: DSL Example: Query Templates
   :class: dsl-info

   .. code-block:: python

       from py3plex.dsl import Q, L, Param

       # Define a reusable query template
       def find_top_nodes(layer_name, degree_threshold, top_n):
           """Reusable template for finding top nodes in a layer"""
           return (
               Q.nodes()
                .from_layers(L[layer_name])
                .where(degree__gt=degree_threshold)
                .compute("betweenness_centrality", "pagerank")
                .order_by("-betweenness_centrality")
                .limit(top_n)
           )

       # Use the template with different parameters
       social_hubs = find_top_nodes("social", 5, 10).execute(network)
       work_hubs = find_top_nodes("work", 3, 20).execute(network)

       # Alternative: Use Param for dynamic parameter binding
       query = (
           Q.nodes()
            .from_layers(L[Param.str("layer")])
            .where(degree__gt=Param.int("min_degree"))
            .compute("betweenness_centrality")
            .limit(Param.int("top_n"))
       )

       # Execute with different parameters
       result1 = query.execute(network, layer="social", min_degree=5, top_n=10)
       result2 = query.execute(network, layer="work", min_degree=3, top_n=20)

**When to use:** Batch analysis, systematic parameter sweeps, reproducible workflows.


Recipe 22: DSL with EXPLAIN Mode
=================================

**Task:** Optimize queries before execution on large networks.

.. admonition:: DSL Example: Query Optimization
   :class: dsl-info

   .. code-block:: python

       from py3plex.dsl import Q, L

       # Build a potentially expensive query
       query = (
           Q.nodes()
            .compute("betweenness_centrality")  # O(n³) operation!
            .order_by("-betweenness_centrality")
            .limit(10)
       )

       # Check the execution plan first
       plan = query.explain().execute(network)
       
       print("Query Execution Plan:")
       for step in plan.steps:
           print(f"- {step.description}")
           print(f"  Complexity: {step.estimated_complexity}")

       # Check for warnings
       if plan.warnings:
           print("\nWarnings:")
           for warning in plan.warnings:
               print(f"⚠️  {warning}")

       # Optimized version: filter first to reduce computation
       optimized_query = (
           Q.nodes()
            .where(degree__gt=5)  # Pre-filter to reduce nodes
            .compute("betweenness_centrality")
            .order_by("-betweenness_centrality")
            .limit(10)
       )

       # Execute the optimized query
       result = optimized_query.execute(network)

**When to use:** Large networks, expensive centrality computations, performance optimization.
