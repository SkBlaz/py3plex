How to Run Community Detection on Multilayer Networks
======================================================

**Goal:** This guide demonstrates how to apply community detection algorithms to multilayer networks and interpret their results. Community detection identifies *mesoscale structure*—groups of nodes that are more densely connected internally than to the rest of the network. In multilayer networks, communities can exist within single layers, span multiple layers, or emerge from inter-layer coupling patterns. This analysis is essential for understanding functional modules, organizational structure, and hierarchical clustering in complex systems.

.. admonition:: 📓 Run this guide online
   :class: tip

   You can run this tutorial in your browser without any local installation:
   
   .. image:: https://colab.research.google.com/assets/colab-badge.svg
      :target: https://colab.research.google.com/github/SkBlaz/py3plex/blob/master/notebooks/community_detection.ipynb
      :alt: Open in Google Colab
   
   Or see the full executable example: :download:`example_community_detection.py <../../examples/communities/example_community_detection.py>`

**Prerequisites:** 

* A loaded multilayer network (see :doc:`load_and_build_networks`)
* Basic familiarity with network terminology (nodes, edges, layers)
* Understanding of modularity as a quality metric (covered in this guide)

**When to use community detection:**

* Identifying functional modules in biological networks
* Detecting organizational units in social networks
* Finding coherent topics in multi-relational knowledge graphs
* Analyzing temporal evolution of communities across time-sliced networks
* Discovering cross-layer relationships in multiplex systems

Quick Start: Louvain Algorithm
-------------------------------

**What is Louvain?**

The Louvain algorithm (Blondel et al., 2008) is a fast, greedy method that optimizes *modularity*, defined as:

.. math::

    Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)

where :math:`A_{ij}` is the adjacency matrix, :math:`k_i` is node degree, :math:`m` is total edges, and :math:`\delta(c_i, c_j)=1` if nodes :math:`i,j` are in the same community. Higher :math:`Q` indicates stronger community structure.

**How it works:**

1. Initialize: each node starts in its own community
2. For each node, compute :math:`\Delta Q` from moving to each neighbor's community
3. Move the node to the community with maximum positive :math:`\Delta Q`
4. Aggregate: collapse communities into super-nodes and repeat
5. Stop when no further improvement is possible

**Time complexity:** :math:`O(n \log n)` for sparse networks

**Basic example:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.community_wrapper import louvain_communities
    
    # Load multilayer network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "datasets/synthetic_multilayer.txt",
        input_type="multiedgelist"
    )
    
    # Run Louvain (operates on flattened network by default)
    communities = louvain_communities(network)
    
    # Analyze results
    from collections import Counter
    comm_sizes = Counter(communities.values())
    
    print(f"Number of communities: {len(comm_sizes)}")
    print(f"Largest community: {max(comm_sizes.values())} nodes")
    print(f"Smallest community: {min(comm_sizes.values())} nodes")
    print(f"Average size: {sum(comm_sizes.values())/len(comm_sizes):.1f}")
    
    # Sample assignments
    for node, comm_id in list(communities.items())[:5]:
        print(f"  {node} → Community {comm_id}")

**Expected output:**

.. code-block:: text

    Number of communities: 4
    Largest community: 45 nodes
    Smallest community: 8 nodes
    Average size: 22.8
      ('A1', 'layer1') → Community 0
      ('A2', 'layer1') → Community 0
      ('B1', 'layer1') → Community 1
      ('B2', 'layer2') → Community 1
      ('C1', 'layer2') → Community 2

**Note:** The standard ``louvain_communities`` function flattens the multilayer network into a single-layer graph: each node-layer pair becomes a single node and inter-layer coupling is ignored (layer names remain as part of the node labels). For layer-aware detection, use ``louvain_multilayer`` (see next section).

Multilayer-Specific: Multilayer Louvain
----------------------------------------

**What makes multilayer community detection different?**

Standard Louvain treats a multilayer network as a single flattened graph, losing layer identity. **Multilayer Louvain** (Mucha et al., 2010) optimizes the *multilayer modularity*:

.. math::

    Q_{\text{multi}} = \frac{1}{2\mu} \sum_{ij\alpha\beta} \left[ \left(A^\alpha_{ij} - \gamma^\alpha \frac{k_i^\alpha k_j^\alpha}{2m_\alpha}\right)\delta_{\alpha\beta} + \delta_{ij}\omega_{\alpha\beta} \right] \delta(g_{i\alpha}, g_{j\beta})

where:

* :math:`A^\alpha_{ij}`: adjacency in layer :math:`\alpha`
* :math:`k_i^\alpha`: degree (or strength) of node :math:`i` in layer :math:`\alpha`
* :math:`m_\alpha`: total edge weight in layer :math:`\alpha` (:math:`2m_\alpha = \sum_{ij} A_{ij}^\alpha`)
* :math:`\gamma^\alpha`: resolution parameter for layer :math:`\alpha` (default 1.0)
* :math:`\omega_{\alpha\beta}`: inter-layer coupling strength (default 1.0)
* :math:`\delta_{ij}=1` if :math:`i=j` (inter-layer edges connect same node across layers)
* :math:`\delta_{\alpha\beta}=1` if :math:`\alpha=\beta` (restricts intra-layer term)
* :math:`\delta(g_{i\alpha}, g_{j\beta})=1` if node :math:`i` in layer :math:`\alpha` and node :math:`j` in layer :math:`\beta` are in the same community
* :math:`\mu`: total weight in the supra-network (:math:`2\mu = \sum_\alpha 2 m_\alpha + \sum_{\alpha\neq\beta}\omega_{\alpha\beta}`)

**Key insight:** The coupling term :math:`\omega_{\alpha\beta}` controls whether communities span layers:

* **ω = 0:** Layers are independent → separate communities per layer
* **ω → ∞:** Strong coupling → communities span all layers
* **0 < ω < ∞:** Partial coupling → communities can span some layers

**Full workflow example:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.multilayer_modularity import (
        louvain_multilayer,
        multilayer_modularity
    )
    from collections import Counter, defaultdict
    
    # Load multilayer network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "datasets/synthetic_multilayer.txt",
        input_type="multiedgelist"
    )
    
    print("Network structure:")
    print(f"  Layers: {network.get_layers()}")
    print(f"  Nodes: {len(network.get_nodes())}")
    print(f"  Edges (total): {network.number_of_edges()}")
    
    # Run multilayer Louvain with different coupling strengths
    for omega in [0.0, 0.5, 1.0, 2.0]:
        print(f"\n--- Coupling ω={omega} ---")
        
        communities = louvain_multilayer(
            network,
            gamma=1.0,        # Resolution (default)
            omega=omega,      # Inter-layer coupling
            random_state=42   # For reproducibility
        )
        
        # Count communities
        n_communities = len(set(communities.values()))
        
        # Calculate multilayer modularity
        Q = multilayer_modularity(network, communities, gamma=1.0, omega=omega)
        
        # Analyze layer coverage
        layer_coverage = defaultdict(set)  # community -> set of layers
        for (node, layer), comm_id in communities.items():
            layer_coverage[comm_id].add(layer)
        
        cross_layer = sum(1 for layers in layer_coverage.values() if len(layers) > 1)
        single_layer = len(layer_coverage) - cross_layer
        
        print(f"  Communities: {n_communities}")
        print(f"  Modularity Q: {Q:.4f}")
        print(f"  Cross-layer communities: {cross_layer}")
        print(f"  Single-layer communities: {single_layer}")
        
        # Size distribution
        comm_sizes = Counter(communities.values())
        avg_size = sum(comm_sizes.values()) / len(comm_sizes)
        print(f"  Average community size: {avg_size:.1f} node-layers")

**Expected output:**

.. code-block:: text

    Network structure:
      Layers: ['layer1', 'layer2', 'layer3']
      Nodes: 120 (40 nodes × 3 layers)
      Edges (total): 284
    
    --- Coupling ω=0.0 ---
      Communities: 12
      Modularity Q: 0.3456
      Cross-layer communities: 0
      Single-layer communities: 12
      Average community size: 10.0 node-layers
    
    --- Coupling ω=0.5 ---
      Communities: 8
      Modularity Q: 0.4123
      Cross-layer communities: 3
      Single-layer communities: 5
      Average community size: 15.0 node-layers
    
    --- Coupling ω=1.0 ---
      Communities: 5
      Modularity Q: 0.4589
      Cross-layer communities: 4
      Single-layer communities: 1
      Average community size: 24.0 node-layers
    
    --- Coupling ω=2.0 ---
      Communities: 4
      Modularity Q: 0.4234
      Cross-layer communities: 4
      Single-layer communities: 0
      Average community size: 30.0 node-layers

**Interpretation:**

* **ω=0.0:** Each layer has independent communities (useful for baseline)
* **ω=0.5-1.0:** Balanced trade-off, some communities span layers
* **ω>1.0:** Forces global communities across all layers (may over-integrate)

**Choosing ω:**

* Use **domain knowledge**: biological function (high ω), temporal snapshots (low ω)
* **Grid search**: try ω ∈ [0.1, 0.5, 1.0, 2.0, 5.0] and pick maximum Q
* **Consensus clustering**: aggregate results across multiple ω values

Infomap Algorithm
-----------------

**What is Infomap?**

Infomap (Rosvall & Bergstrom, 2008) uses information theory to find communities by minimizing the *map equation*:

.. math::

    L(M) = q_\curvearrowright H(Q) + \sum_{i=1}^m p_{\circlearrowright}^i H(P^i)

where:

* :math:`q_\curvearrowright`: probability of switching between modules (inter-module flow)
* :math:`H(Q)`: entropy of module codebook  
* :math:`p_{\circlearrowright}^i`: probability of staying within module :math:`i` (intra-module flow)
* :math:`H(P^i)`: entropy of nodes within module :math:`i`

**Key insight:** Infomap simulates a random walker and finds communities that compress the *description length* of the walker's trajectory. Communities are regions where the walker gets "trapped" for extended periods.

**Pros/cons vs. Louvain:**

* **Pros:** Often finds better communities for flow-based systems (e.g., citation networks, web graphs)
* **Cons:** Requires external binary (not pure Python), slower than Louvain, harder to interpret parameters

**Installation:**

Infomap requires the standalone binary from https://www.mapequation.org/infomap/:

.. code-block:: bash

    # Download and install
    wget https://www.mapequation.org/downloads/Infomap.zip
    unzip Infomap.zip
    cd Infomap
    make
    sudo cp Infomap /usr/local/bin/infomap
    
    # Or install Python wrapper (alternative)
    pip install infomap

**Basic usage:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.community_wrapper import infomap_communities
    import os
    
    # Load network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "datasets/synthetic_multilayer.txt",
        input_type="multiedgelist"
    )
    
    # Check if binary exists
    binary_path = "/usr/local/bin/infomap"  # Adjust to your installation
    if not os.path.exists(binary_path):
        print(f"Infomap binary not found at {binary_path}")
        print("Please install from: https://www.mapequation.org/infomap/")
        print("Falling back to Louvain...")
        # Use Louvain as fallback
        from py3plex.algorithms.community_detection.community_wrapper import louvain_communities
        communities = louvain_communities(network)
    else:
        # Run Infomap
        communities = infomap_communities(
            network,
            binary=binary_path,
            multiplex=True,      # Use multiplex mode for multilayer networks
            iterations=1000,     # More iterations = better convergence
            seed=42,             # For reproducibility
            verbose=False        # Set True to see Infomap output
        )
    
    # Analyze results
    from collections import Counter
    comm_sizes = Counter(communities.values())
    
    print(f"Number of communities: {len(comm_sizes)}")
    print(f"Largest community: {max(comm_sizes.values())} nodes")
    print(f"Average size: {sum(comm_sizes.values())/len(comm_sizes):.1f}")

**Expected output:**

.. code-block:: text

    Number of communities: 6
    Largest community: 38 nodes
    Average size: 20.0

**Multiplex mode:**

When ``multiplex=True``, Infomap treats layers as separate networks but allows random walkers to switch layers (implicitly modeling inter-layer coupling). This is different from Louvain's explicit :math:`\omega` parameter.

**Comparison workflow:**

.. code-block:: python

    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    
    # Run both algorithms
    louvain_comms = louvain_communities(network)
    infomap_comms = infomap_communities(network, binary=binary_path, seed=42)
    
    # Convert to aligned label vectors
    nodes = list(louvain_comms.keys())
    louvain_labels = [louvain_comms[n] for n in nodes]
    infomap_labels = [infomap_comms[n] for n in nodes]
    
    # Compute similarity
    ari = adjusted_rand_score(louvain_labels, infomap_labels)
    nmi = normalized_mutual_info_score(louvain_labels, infomap_labels)
    
    print(f"Agreement between Louvain and Infomap:")
    print(f"  ARI: {ari:.3f}  (1.0 = perfect agreement)")
    print(f"  NMI: {nmi:.3f}  (1.0 = perfect agreement)")

**Expected output:**

.. code-block:: text

    Agreement between Louvain and Infomap:
      ARI: 0.723  (1.0 = perfect agreement)
      NMI: 0.815  (1.0 = perfect agreement)

**When to use Infomap:**

* Citation/web networks with clear flow patterns
* Networks where you care about information diffusion
* When Louvain gives unsatisfying results (try both and compare)
* When you have the binary installed (otherwise, stick with Louvain)

Label Propagation
-----------------

**What is Label Propagation?**

Label propagation (Raghavan et al., 2007) is an extremely fast, near-linear time algorithm that works by iteratively assigning each node to the most common community among its neighbors.

**Algorithm:**

1. Initialize: each node gets a unique label (community ID)
2. **For t=1 to T iterations:**
   
   a. Randomize node order
   b. For each node :math:`i`:
      
      * Count neighbor labels: :math:`n_c = |\{j \in N(i) : c_j = c\}|`
      * Assign :math:`c_i = \arg\max_c n_c` (ties broken randomly)

3. Stop when labels stabilize or max iterations reached

**Time complexity:** :math:`O(m)` per iteration (linear in edges)

**Pros/cons:**

* **Pros:** Very fast, scales to millions of nodes, no parameters to tune
* **Cons:** Non-deterministic (order-dependent), lower quality than Louvain/Infomap, may not converge

**Implementation note:**

py3plex uses NetworkX's label propagation for single-layer networks:

.. code-block:: python

    from py3plex.core import multinet
    import networkx as nx
    from networkx.algorithms.community import asyn_lpa_communities
    from collections import defaultdict
    
    # Load network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "datasets/synthetic_multilayer.txt",
        input_type="multiedgelist"
    )
    
    # Convert to NetworkX (flattened single-layer graph)
    G = nx.Graph()
    for edge in network.core_network.edges():
        G.add_edge(edge[0], edge[1])
    
    # Run label propagation
    communities_list = asyn_lpa_communities(G, seed=42)
    
    # Convert to dict format: node -> community_id
    communities = {}
    for comm_id, comm_nodes in enumerate(communities_list):
        for node in comm_nodes:
            communities[node] = comm_id
    
    # Analyze results
    from collections import Counter
    comm_sizes = Counter(communities.values())
    
    print(f"Number of communities: {len(comm_sizes)}")
    print(f"Largest community: {max(comm_sizes.values())} nodes")
    print(f"Average size: {sum(comm_sizes.values())/len(comm_sizes):.1f}")
    
    # Run multiple times to check stability
    print("\nStability check (5 runs with same seed):")
    for run in range(5):
        comms_run = list(asyn_lpa_communities(G, seed=42))
        n_comms = len(comms_run)
        print(f"  Run {run+1}: {n_comms} communities")

**Expected output:**

.. code-block:: text

    Number of communities: 7
    Largest community: 34 nodes
    Average size: 17.1
    
    Stability check (5 runs with same seed):
      Run 1: 7 communities
      Run 2: 7 communities
      Run 3: 7 communities
      Run 4: 8 communities
      Run 5: 7 communities

**Layer-aware label propagation (custom implementation):**

For multilayer networks, you can implement layer-aware label propagation:

.. code-block:: python

    import random
    from collections import Counter
    
    def multilayer_label_propagation(network, max_iter=100, seed=42):
        """
        Layer-aware label propagation for multilayer networks.
        Propagates labels within each layer independently.
        """
        random.seed(seed)
        
        # Initialize: each node-layer gets unique label
        labels = {nl: i for i, nl in enumerate(network.get_nodes())}
        
        # Get layer-specific edges
        layer_edges = {}
        for layer in network.get_layers():
            layer_edges[layer] = [
                (e[0], e[1]) for e in network.core_network.edges()
                if e[0][1] == layer and e[1][1] == layer
            ]
        
        # Iterate
        for iteration in range(max_iter):
            changed = False
            nodes = list(labels.keys())
            random.shuffle(nodes)
            
            for node, layer in nodes:
                # Get neighbors in same layer
                neighbors = [
                    target for source, target in layer_edges.get(layer, [])
                    if source == (node, layer)
                ] + [
                    source for source, target in layer_edges.get(layer, [])
                    if target == (node, layer)
                ]
                
                if not neighbors:
                    continue
                
                # Count neighbor labels
                neighbor_labels = [labels[n] for n in neighbors]
                label_counts = Counter(neighbor_labels)
                
                # Assign most common label (ties broken randomly)
                most_common = label_counts.most_common()
                max_count = most_common[0][1]
                candidates = [lbl for lbl, cnt in most_common if cnt == max_count]
                new_label = random.choice(candidates)
                
                if new_label != labels[(node, layer)]:
                    labels[(node, layer)] = new_label
                    changed = True
            
            if not changed:
                print(f"Converged after {iteration+1} iterations")
                break
        
        # Renumber communities
        unique_labels = sorted(set(labels.values()))
        label_map = {old: new for new, old in enumerate(unique_labels)}
        return {nl: label_map[lbl] for nl, lbl in labels.items()}
    
    # Run custom implementation
    communities = multilayer_label_propagation(network, max_iter=100, seed=42)
    
    comm_sizes = Counter(communities.values())
    print(f"\nLayer-aware label propagation:")
    print(f"  Communities: {len(comm_sizes)}")
    print(f"  Average size: {sum(comm_sizes.values())/len(comm_sizes):.1f}")

**Expected output:**

.. code-block:: text

    Converged after 23 iterations
    
    Layer-aware label propagation:
      Communities: 9
      Average size: 13.3

**When to use label propagation:**

* **Very large networks** (>100k nodes) where Louvain is too slow
* **Exploratory analysis** where you need quick initial results
* **Streaming settings** where you process edges incrementally
* **Not recommended** for publication-quality results (use Louvain or Infomap instead)

Analyzing Community Structure
------------------------------

After detecting communities, you need to **analyze** and **interpret** the results. This section shows robust workflows for understanding community properties.

Count Nodes Per Community
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Basic counting:**

.. code-block:: python

    from collections import Counter
    import numpy as np
    
    # Assuming 'communities' is a dict: node -> community_id
    comm_sizes = Counter(communities.values())
    
    print(f"Total communities: {len(comm_sizes)}")
    print(f"\nTop 10 largest communities:")
    for comm_id, size in comm_sizes.most_common(10):
        print(f"  Community {comm_id}: {size} nodes")
    
    # Size statistics
    sizes = np.array(list(comm_sizes.values()))
    print(f"\nSize distribution:")
    print(f"  Mean: {np.mean(sizes):.2f}")
    print(f"  Median: {np.median(sizes):.2f}")
    print(f"  Std dev: {np.std(sizes):.2f}")
    print(f"  Min: {np.min(sizes)}")
    print(f"  Max: {np.max(sizes)}")
    print(f"  Q1/Q3: {np.percentile(sizes, 25):.0f} / {np.percentile(sizes, 75):.0f}")

**Expected output:**

.. code-block:: text

    Total communities: 5
    
    Top 10 largest communities:
      Community 0: 45 nodes
      Community 1: 38 nodes
      Community 2: 22 nodes
      Community 3: 10 nodes
      Community 4: 5 nodes
    
    Size distribution:
      Mean: 24.00
      Median: 22.00
      Std dev: 15.87
      Min: 5
      Max: 45
      Q1/Q3: 10 / 38

**Layer coverage analysis (for multilayer networks):**

.. code-block:: python

    from collections import defaultdict
    
    # communities: {(node, layer): comm_id}
    layer_coverage = defaultdict(lambda: defaultdict(set))  # comm -> layer -> nodes
    
    for (node, layer), comm_id in communities.items():
        layer_coverage[comm_id][layer].add(node)
    
    print("Community layer coverage:")
    for comm_id in sorted(layer_coverage.keys()):
        layers = layer_coverage[comm_id]
        total_size = sum(len(nodes) for nodes in layers.values())
        print(f"\nCommunity {comm_id} (total: {total_size} node-layers):")
        for layer, nodes in sorted(layers.items()):
            print(f"  {layer}: {len(nodes)} nodes")
        
        # Cross-layer nodes (nodes appearing in multiple layers within same community)
        all_nodes = set()
        for nodes in layers.values():
            all_nodes.update(nodes)
        unique_nodes = len(all_nodes)
        redundancy = total_size / unique_nodes if unique_nodes > 0 else 0
        print(f"  Unique nodes: {unique_nodes}, Redundancy: {redundancy:.2f}x")

**Expected output:**

.. code-block:: text

    Community layer coverage:
    
    Community 0 (total: 45 node-layers):
      layer1: 18 nodes
      layer2: 15 nodes
      layer3: 12 nodes
      Unique nodes: 15, Redundancy: 3.00x
    
    Community 1 (total: 38 node-layers):
      layer1: 20 nodes
      layer2: 18 nodes
      Unique nodes: 20, Redundancy: 1.90x
    
    Community 2 (total: 22 node-layers):
      layer3: 22 nodes
      Unique nodes: 22, Redundancy: 1.00x

Visualize Communities
~~~~~~~~~~~~~~~~~~~~~

**Hairball plot with community colors:**

.. code-block:: python

    from py3plex.visualization.multilayer import hairball_plot
    import matplotlib.pyplot as plt
    from py3plex.visualization.colors import colors_default
    
    # Select top N communities to color
    top_n = 8
    top_communities = [c for c, _ in comm_sizes.most_common(top_n)]
    
    # Create color mapping
    color_map = dict(zip(
        top_communities,
        colors_default[:top_n]
    ))
    
    # Assign colors to nodes
    node_colors = []
    for node in network.get_nodes():
        comm_id = communities.get(node, -1)
        if comm_id in color_map:
            node_colors.append(color_map[comm_id])
        else:
            node_colors.append('lightgray')  # Small communities
    
    # Plot
    plt.figure(figsize=(12, 10))
    hairball_plot(
        network.core_network,
        color_list=node_colors,
        layout_algorithm='force',
        layout_parameters={'iterations': 500},
        scale_by_size=True,
        legend=False
    )
    plt.title('Community Structure (Top 8 Communities Colored)', fontsize=16)
    plt.tight_layout()
    plt.savefig('community_hairball.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("Visualization saved to: community_hairball.png")

**Size distribution histogram:**

.. code-block:: python

    import matplotlib.pyplot as plt
    import numpy as np
    
    sizes = list(comm_sizes.values())
    
    plt.figure(figsize=(10, 6))
    plt.hist(sizes, bins=20, edgecolor='black', alpha=0.7)
    plt.xlabel('Community Size (number of nodes)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title(f'Community Size Distribution (n={len(sizes)} communities)', fontsize=14)
    plt.axvline(np.mean(sizes), color='red', linestyle='--', label=f'Mean: {np.mean(sizes):.1f}')
    plt.axvline(np.median(sizes), color='blue', linestyle='--', label=f'Median: {np.median(sizes):.1f}')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('community_size_distribution.png', dpi=300)
    plt.show()

**Layer-specific visualization:**

For multilayer networks, visualize community composition across layers:

.. code-block:: python

    import pandas as pd
    import seaborn as sns
    
    # Build matrix: communities × layers
    layers = network.get_layers()
    comm_ids = sorted(set(communities.values()))
    
    matrix = np.zeros((len(comm_ids), len(layers)))
    for (node, layer), comm_id in communities.items():
        layer_idx = layers.index(layer)
        comm_idx = comm_ids.index(comm_id)
        matrix[comm_idx, layer_idx] += 1
    
    # Heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        matrix,
        xticklabels=layers,
        yticklabels=[f'C{i}' for i in comm_ids],
        cmap='YlOrRd',
        annot=True,
        fmt='.0f',
        cbar_kws={'label': 'Number of nodes'}
    )
    plt.xlabel('Layer', fontsize=12)
    plt.ylabel('Community', fontsize=12)
    plt.title('Community × Layer Composition Heatmap', fontsize=14)
    plt.tight_layout()
    plt.savefig('community_layer_heatmap.png', dpi=300)
    plt.show()

Export Communities
~~~~~~~~~~~~~~~~~~

**CSV export (most common):**

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
    
    # Add community size
    size_map = dict(comm_sizes)
    df['community_size'] = df['community'].map(size_map)
    
    # Sort by community, then layer, then node
    df = df.sort_values(['community', 'layer', 'node'])
    
    # Save
    df.to_csv('communities.csv', index=False)
    print(f"Exported {len(df)} node-layer assignments to communities.csv")
    print(f"\nFirst few rows:")
    print(df.head(10))

**Expected output:**

.. code-block:: text

    Exported 120 node-layer assignments to communities.csv
    
    First few rows:
        node   layer  community  community_size
    0     A1  layer1          0              45
    1     A1  layer2          0              45
    2     A1  layer3          0              45
    3     A2  layer1          0              45
    4     A2  layer2          0              45
    5     B1  layer1          1              38
    6     B1  layer2          1              38
    7     B2  layer1          1              38
    8     C1  layer3          2              22
    9     C2  layer3          2              22

**JSON export (for web apps):**

.. code-block:: python

    import json
    
    # Group by community
    community_dict = defaultdict(list)
    for (node, layer), comm_id in communities.items():
        community_dict[str(comm_id)].append({
            'node': node,
            'layer': layer
        })
    
    # Add metadata
    output = {
        'num_communities': len(community_dict),
        'num_nodes': len(set(node for node, _ in communities.keys())),
        'num_layers': len(network.get_layers()),
        'communities': dict(community_dict)
    }
    
    with open('communities.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("Exported to communities.json")

**Cytoscape format (for visualization):**

.. code-block:: python

    # Node table
    node_df = pd.DataFrame([
        {
            'node_id': f"{node}_{layer}",
            'node': node,
            'layer': layer,
            'community': communities.get((node, layer), -1)
        }
        for node, layer in network.get_nodes()
    ])
    node_df.to_csv('cytoscape_nodes.csv', index=False)
    
    # Edge table
    edge_data = []
    for source, target in network.core_network.edges():
        edge_data.append({
            'source': f"{source[0]}_{source[1]}",
            'target': f"{target[0]}_{target[1]}",
            'source_community': communities.get(source, -1),
            'target_community': communities.get(target, -1),
            'is_intra_community': communities.get(source, -1) == communities.get(target, -1)
        })
    edge_df = pd.DataFrame(edge_data)
    edge_df.to_csv('cytoscape_edges.csv', index=False)
    
    print("Exported to cytoscape_nodes.csv and cytoscape_edges.csv")
    print("Import these into Cytoscape for interactive visualization")

Query Communities with DSL
---------------------------

**Goal:** Use py3plex's Domain-Specific Language (DSL) to query and analyze community-detected networks efficiently.

The DSL provides a declarative, SQL-like interface for querying multilayer networks. After detecting communities, you can use DSL queries to filter nodes by community membership, compute community-level statistics, and extract subnetworks.

**Prerequisites:** 

* Community detection results (e.g., from ``louvain_communities()``)
* Familiarity with DSL basics (see :doc:`query_with_dsl` for full tutorial)

DSL Basics for Communities
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**String Syntax - SQL-like queries:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.community_wrapper import louvain_communities
    from py3plex.dsl import execute_query
    
    # Load network and detect communities
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "py3plex/datasets/_data/synthetic_multilayer.edges",
        input_type="multiedgelist"
    )
    
    communities = louvain_communities(network)
    
    # Attach community labels as node attributes
    for (node, layer), comm_id in communities.items():
        network.core_network.nodes[(node, layer)]['community'] = comm_id
    
    # DSL Query: Find nodes in community 0
    result = execute_query(
        network, 
        'SELECT nodes WHERE community=0'
    )
    
    nodes_in_comm0 = result.get("nodes", [])
    
    print(f"Nodes in community 0: {len(nodes_in_comm0)}")
    for node in nodes_in_comm0[:5]:
        print(f"  {node}")

**Note:** ``execute_query`` returns a dictionary; access node matches via ``result["nodes"]`` (not the dict length) to avoid counting metadata keys.

**Expected output:**

.. code-block:: text

    Nodes in community 0: 18
      ('node1', 'layer1')
      ('node1', 'layer2')
      ('node2', 'layer1')
      ('node3', 'layer1')
      ('node3', 'layer3')

**Builder API - Chainable operations:**

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Find high-degree nodes in a specific community
    result = (
        Q.nodes()
         .where(community=0)
         .compute("degree")
         .where(degree__gt=5)
         .order_by("degree", reverse=True)
         .execute(network)
    )
    
    # Convert to pandas for analysis
    import pandas as pd
    df = pd.DataFrame([
        {
            'node': node[0],
            'layer': node[1],
            'degree': data['degree'],
            'community': data.get('community', -1)
        }
        for node, data in result.items()
    ])
    
    print("High-degree nodes in community 0:")
    print(df.head(10))

**Expected output:**

.. code-block:: text

    High-degree nodes in community 0:
          node   layer  degree  community
    0    node1  layer1      12          0
    1    node1  layer2      10          0
    2    node2  layer1       9          0
    3    node5  layer1       8          0
    4    node5  layer3       7          0

Community-Level Queries
~~~~~~~~~~~~~~~~~~~~~~~

**Count nodes per community:**

.. code-block:: python

    # Get all communities
    community_ids = set(communities.values())
    
    for comm_id in sorted(community_ids):
        result = execute_query(
            network,
            f'SELECT nodes WHERE community={comm_id}'
        )
        print(f"Community {comm_id}: {result.get('count', 0)} nodes")

**Find inter-community edges:**

.. code-block:: python

    from py3plex.dsl import Q
    
    # Attach community labels to edges based on endpoint communities
    for edge in network.core_network.edges():
        source, target = edge
        source_comm = communities.get(source, -1)
        target_comm = communities.get(target, -1)
        network.core_network.edges[edge]['source_community'] = source_comm
        network.core_network.edges[edge]['target_community'] = target_comm
        network.core_network.edges[edge]['is_intra_community'] = (source_comm == target_comm)
    
    # Query inter-community edges
    inter_comm_edges = (
        Q.edges()
         .where(is_intra_community=False)
         .execute(network)
    )
    
    intra_comm_edges = (
        Q.edges()
         .where(is_intra_community=True)
         .execute(network)
    )
    
    intra_len = len(intra_comm_edges)
    inter_len = len(inter_comm_edges)
    ratio = inter_len / intra_len if intra_len else 0
    
    print(f"Intra-community edges: {intra_len}")
    print(f"Inter-community edges: {inter_len}")
    print(f"Ratio: {ratio:.3f} (inter / intra)")

**Expected output:**

.. code-block:: text

    Intra-community edges: 245
    Inter-community edges: 39
    Ratio: 0.159

Layer-Specific Community Queries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Find nodes in a specific community and layer:**

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Community 0 nodes in layer1 only
    result = (
        Q.nodes()
         .from_layers(L["layer1"])
         .where(community=0)
         .compute("degree")
         .execute(network)
    )
    
    count = len(result)
    avg_degree = sum(d['degree'] for d in result.values())/count if count else 0
    print(f"Community 0 in layer1: {count} nodes")
    print(f"Average degree: {avg_degree:.2f}")

**Compare community structure across layers:**

.. code-block:: python

    layers = network.get_layers()
    
    for layer in layers:
        # Count communities present in this layer
        layer_nodes = (
            Q.nodes()
             .from_layers(L[layer])
             .execute(network)
        )
        
        layer_communities = set(
            communities.get(node, -1) 
            for node in layer_nodes
        )
        
        print(f"{layer}: {len(layer_communities)} communities, {len(layer_nodes)} nodes")

**Expected output:**

.. code-block:: text

    layer1: 5 communities, 40 nodes
    layer2: 4 communities, 40 nodes
    layer3: 3 communities, 40 nodes

Extract Community Subnetworks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Extract a single community as a subnetwork:**

.. code-block:: python

    from py3plex.dsl import Q
    
    # Extract community 0
    comm_0_result = execute_query(
        network,
        'SELECT nodes WHERE community=0'
    )
    
    comm_0_nodes = comm_0_result.get("nodes", [])
    
    # Get induced subgraph
    subgraph = network.core_network.subgraph(comm_0_nodes)
    
    # Convert to new multilayer network
    community_network = multinet.multi_layer_network(directed=False)
    community_network.core_network = subgraph.copy()
    
    print(f"Community 0 subnetwork:")
    print(f"  Nodes: {community_network.number_of_nodes()}")
    print(f"  Edges: {community_network.number_of_edges()}")
    print(f"  Layers: {community_network.get_layers()}")

**Expected output:**

.. code-block:: text

    Community 0 subnetwork:
      Nodes: 18
      Edges: 67
      Layers: ['layer1', 'layer2', 'layer3']

Compute Community-Level Statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Average centrality per community:**

.. code-block:: python

    from py3plex.dsl import Q
    from collections import defaultdict
    
    # Compute centrality for all nodes
    result = (
        Q.nodes()
         .compute("betweenness_centrality", "degree")
         .execute(network)
    )
    
    # Group by community
    comm_stats = defaultdict(list)
    for node, data in result.items():
        comm_id = data.get('community', -1)
        comm_stats[comm_id].append({
            'degree': data['degree'],
            'betweenness': data['betweenness_centrality']
        })
    
    # Calculate averages
    print("Community-level statistics:")
    print(f"{'Community':<12} {'Nodes':<8} {'Avg Degree':<12} {'Avg Betweenness':<18}")
    print("-" * 50)
    
    for comm_id in sorted(comm_stats.keys()):
        stats = comm_stats[comm_id]
        n_nodes = len(stats)
        avg_degree = sum(s['degree'] for s in stats) / n_nodes
        avg_betw = sum(s['betweenness'] for s in stats) / n_nodes
        print(f"{comm_id:<12} {n_nodes:<8} {avg_degree:<12.2f} {avg_betw:<18.6f}")

**Expected output:**

.. code-block:: text

    Community-level statistics:
    Community    Nodes    Avg Degree   Avg Betweenness    
    --------------------------------------------------
    0            18       7.44         0.012345          
    1            15       6.13         0.008234          
    2            12       5.25         0.005678          
    3            8        4.50         0.003456          
    4            7        3.86         0.002123          

Complex DSL Workflows
~~~~~~~~~~~~~~~~~~~~~

**Multi-step analysis: Find bridge nodes between communities:**

.. code-block:: python

    from py3plex.dsl import Q
    
    # Bridge nodes: high betweenness + connect multiple communities
    # First, compute betweenness
    result = (
        Q.nodes()
         .compute("betweenness_centrality", "degree")
         .execute(network)
    )
    
    # Identify potential bridges (high betweenness)
    bridges = [
        (node, data['betweenness_centrality'])
        for node, data in result.items()
        if data['betweenness_centrality'] > 0.01  # Threshold
    ]
    
    print(f"Potential bridge nodes (betweenness > 0.01): {len(bridges)}")
    
    # For each bridge, check which communities its neighbors belong to
    for node, betw in sorted(bridges, key=lambda x: x[1], reverse=True)[:5]:
        # Get neighbors
        neighbors = list(network.core_network.neighbors(node))
        neighbor_comms = set(communities.get(n, -1) for n in neighbors)
        
        print(f"  {node}: betweenness={betw:.6f}, connects {len(neighbor_comms)} communities")

**Expected output:**

.. code-block:: text

    Potential bridge nodes (betweenness > 0.01): 12
      ('node7', 'layer1'): betweenness=0.045678, connects 3 communities
      ('node12', 'layer2'): betweenness=0.034567, connects 2 communities
      ('node3', 'layer1'): betweenness=0.023456, connects 3 communities
      ('node15', 'layer3'): betweenness=0.019876, connects 2 communities
      ('node8', 'layer2'): betweenness=0.015432, connects 2 communities

**Temporal community analysis (for time-sliced networks):**

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Assuming layers represent time slices: t1, t2, t3
    time_layers = ['t1', 't2', 't3']
    
    # Track specific nodes across time
    tracked_nodes = ['Alice', 'Bob', 'Carol']
    
    print("Community membership over time:")
    for node in tracked_nodes:
        print(f"\n{node}:")
        for t_layer in time_layers:
            node_key = (node, t_layer)
            comm_id = communities.get(node_key, None)
            if comm_id is not None:
                print(f"  {t_layer}: Community {comm_id}")
            else:
                print(f"  {t_layer}: Not present")

**Why use DSL for community analysis?**

* **Declarative:** Express *what* you want, not *how* to compute it
* **Composable:** Chain operations to build complex queries
* **Efficient:** DSL optimizes query execution internally
* **Readable:** SQL-like syntax is self-documenting
* **Interoperable:** Results integrate seamlessly with pandas, NumPy, and visualization tools

**Next steps with DSL:**

* **Full DSL tutorial:** :doc:`query_with_dsl` - Comprehensive guide with advanced patterns
* **Builder API reference:** :doc:`../reference/dsl_api` - Complete API documentation
* **Temporal queries:** :doc:`query_with_dsl` (Temporal Queries section) - Time-varying networks

Compare Algorithms
------------------

Different algorithms optimize different objective functions and may produce different community structures. **Comparing multiple algorithms** helps validate findings and understand algorithm-specific biases.

**Metrics for comparing partitions:**

1. **Adjusted Rand Index (ARI)**: Measures similarity adjusted for chance
   
   * Range: [-1, 1], where 1 = perfect agreement, 0 = random
   * Adjusted for cluster size imbalance

2. **Normalized Mutual Information (NMI)**: Information-theoretic similarity
   
   * Range: [0, 1], where 1 = perfect agreement
   * Symmetric, handles different number of communities well

3. **Variation of Information (VI)**: Distance metric (lower = more similar)
   
   * Range: [0, ∞], where 0 = identical partitions

**Full comparison workflow:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.community_wrapper import (
        louvain_communities,
        infomap_communities
    )
    from py3plex.algorithms.community_detection.multilayer_modularity import (
        louvain_multilayer,
        multilayer_modularity
    )
    from py3plex.algorithms.community_detection.community_louvain import modularity
    import networkx as nx
    from networkx.algorithms.community import asyn_lpa_communities
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    from scipy.spatial.distance import jensenshannon
    import numpy as np
    from collections import Counter
    
    # Load network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "datasets/synthetic_multilayer.txt",
        input_type="multiedgelist"
    )
    
    print("=" * 70)
    print("COMMUNITY DETECTION ALGORITHM COMPARISON")
    print("=" * 70)
    
    # Run multiple algorithms
    print("\n1. Running algorithms...")
    
    # Louvain (flattened)
    louvain_comms = louvain_communities(network)
    
    # Multilayer Louvain (ω=1.0)
    multilayer_comms = louvain_multilayer(
        network, gamma=1.0, omega=1.0, random_state=42
    )
    
    # Label propagation (flattened NetworkX graph)
    G = nx.Graph()
    for edge in network.core_network.edges():
        G.add_edge(edge[0], edge[1])
    lpa_comms_list = asyn_lpa_communities(G, seed=42)
    lpa_comms = {}
    for comm_id, nodes in enumerate(lpa_comms_list):
        for node in nodes:
            lpa_comms[node] = comm_id
    
    # (Optional) Infomap - skip if binary not available
    try:
        infomap_comms = infomap_communities(
            network, binary="/usr/local/bin/infomap",
            seed=42, verbose=False
        )
        has_infomap = True
    except Exception:
        has_infomap = False
        print("  [SKIP] Infomap not available")
    
    # Store results
    algorithms = {
        'Louvain (flat)': louvain_comms,
        'Louvain (multilayer)': multilayer_comms,
        'Label Propagation': lpa_comms,
    }
    if has_infomap:
        algorithms['Infomap'] = infomap_comms
    
    # 2. Basic statistics
    print("\n2. Basic statistics:")
    print(f"{'Algorithm':<25} {'#Comm':<10} {'Largest':<10} {'Avg Size':<10}")
    print("-" * 70)
    
    for name, comms in algorithms.items():
        sizes = Counter(comms.values())
        n_comms = len(sizes)
        largest = max(sizes.values())
        avg_size = sum(sizes.values()) / n_comms
        print(f"{name:<25} {n_comms:<10} {largest:<10} {avg_size:<10.1f}")
    
    # 3. Modularity scores
    print("\n3. Modularity scores:")
    print(f"{'Algorithm':<25} {'Modularity (Q)':<15}")
    print("-" * 70)
    
    for name, comms in algorithms.items():
        if name == 'Louvain (multilayer)':
            # Use multilayer modularity
            Q = multilayer_modularity(network, comms, gamma=1.0, omega=1.0)
        else:
            # Use single-layer modularity on flattened graph
            Q = modularity(comms, G, weight='weight')
        print(f"{name:<25} {Q:<15.4f}")
    
    # 4. Pairwise agreement
    print("\n4. Pairwise agreement (ARI / NMI):")
    
    # Align all partitions to same node set
    alg_names = list(algorithms.keys())
    alg_labels = {}
    
    # Get common nodes (for multilayer, use node-layer pairs)
    all_nodes = set()
    for comms in algorithms.values():
        all_nodes.update(comms.keys())
    common_nodes = sorted(all_nodes)
    
    # Convert to label vectors
    for name, comms in algorithms.items():
        alg_labels[name] = [comms.get(node, -1) for node in common_nodes]
    
    # Compute pairwise metrics
    print(f"\n{'Pair':<45} {'ARI':<10} {'NMI':<10}")
    print("-" * 70)
    
    for i in range(len(alg_names)):
        for j in range(i+1, len(alg_names)):
            name1, name2 = alg_names[i], alg_names[j]
            labels1 = alg_labels[name1]
            labels2 = alg_labels[name2]
            
            ari = adjusted_rand_score(labels1, labels2)
            nmi = normalized_mutual_info_score(labels1, labels2)
            
            print(f"{name1} vs {name2:<25} {ari:<10.3f} {nmi:<10.3f}")
    
    # 5. Size distribution comparison
    print("\n5. Size distribution similarity:")
    
    # Normalize size distributions
    def normalize_sizes(comms):
        sizes = list(Counter(comms.values()).values())
        sizes_array = np.array(sorted(sizes, reverse=True))
        # Pad to same length
        max_len = max(len(Counter(c.values())) for c in algorithms.values())
        padded = np.zeros(max_len)
        padded[:len(sizes_array)] = sizes_array
        return padded / padded.sum()
    
    size_dists = {name: normalize_sizes(comms) for name, comms in algorithms.items()}
    
    print(f"{'Pair':<45} {'JS Divergence':<15}")
    print("-" * 70)
    
    for i in range(len(alg_names)):
        for j in range(i+1, len(alg_names)):
            name1, name2 = alg_names[i], alg_names[j]
            js_div = jensenshannon(size_dists[name1], size_dists[name2])
            print(f"{name1} vs {name2:<25} {js_div:<15.4f}")

**Expected output:**

.. code-block:: text

    ======================================================================
    COMMUNITY DETECTION ALGORITHM COMPARISON
    ======================================================================
    
    1. Running algorithms...
      [SKIP] Infomap not available
    
    2. Basic statistics:
    Algorithm                 #Comm      Largest    Avg Size  
    ----------------------------------------------------------------------
    Louvain (flat)            5          45         24.0      
    Louvain (multilayer)      4          52         30.0      
    Label Propagation         7          38         17.1      
    
    3. Modularity scores:
    Algorithm                 Modularity (Q)
    ----------------------------------------------------------------------
    Louvain (flat)            0.4234     
    Louvain (multilayer)      0.4589     
    Label Propagation         0.3891     
    
    4. Pairwise agreement (ARI / NMI):
    
    Pair                                          ARI        NMI       
    ----------------------------------------------------------------------
    Louvain (flat) vs Louvain (multilayer)        0.812      0.878     
    Louvain (flat) vs Label Propagation           0.623      0.745     
    Louvain (multilayer) vs Label Propagation     0.589      0.712     
    
    5. Size distribution similarity:
    Pair                                          JS Divergence  
    ----------------------------------------------------------------------
    Louvain (flat) vs Louvain (multilayer)        0.1234     
    Louvain (flat) vs Label Propagation           0.2456     
    Louvain (multilayer) vs Label Propagation     0.2789     

**Interpretation:**

* **High ARI/NMI (>0.8):** Algorithms agree strongly → robust communities
* **Medium ARI/NMI (0.5-0.8):** Partial agreement → sensitive to algorithm choice
* **Low ARI/NMI (<0.5):** Strong disagreement → no clear community structure or algorithm-specific artifacts

**Consensus clustering:**

When algorithms disagree, use consensus clustering to find stable communities:

.. code-block:: python

    from collections import defaultdict
    
    # Build co-occurrence matrix: how often do pairs of nodes appear together?
    co_occurrence = defaultdict(int)
    n_algorithms = len(algorithms)
    
    for comms in algorithms.values():
        # For each community in this partition
        comm_groups = defaultdict(list)
        for node, comm_id in comms.items():
            comm_groups[comm_id].append(node)
        
        # Increment co-occurrence for all pairs in same community
        for nodes in comm_groups.values():
            for i, node1 in enumerate(nodes):
                for node2 in nodes[i+1:]:
                    pair = tuple(sorted([node1, node2]))
                    co_occurrence[pair] += 1
    
    # Threshold: keep pairs that co-occur in ≥50% of algorithms
    threshold = n_algorithms * 0.5
    stable_pairs = {pair for pair, count in co_occurrence.items() if count >= threshold}
    
    print(f"\nConsensus clustering:")
    print(f"  Total node pairs: {len(co_occurrence)}")
    print(f"  Stable pairs (≥50% agreement): {len(stable_pairs)}")
    print(f"  Stability ratio: {len(stable_pairs)/len(co_occurrence):.2%}")

**Expected output:**

.. code-block:: text

    Consensus clustering:
      Total node pairs: 1845
      Stable pairs (≥50% agreement): 1234
      Stability ratio: 66.88%

Layer-Specific Communities
---------------------------

**Motivation:**

In multilayer networks, you may want to detect communities **within individual layers** and then compare them across layers. This reveals:

* Layer-specific structure (e.g., friendship communities vs. work communities)
* How community organization changes across contexts
* Which communities are stable vs. layer-dependent

**Workflow:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.community_wrapper import louvain_communities
    from py3plex.algorithms.community_detection.community_louvain import modularity
    import networkx as nx
    from collections import Counter
    
    # Load multilayer network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "datasets/synthetic_multilayer.txt",
        input_type="multiedgelist"
    )
    
    print("LAYER-SPECIFIC COMMUNITY DETECTION")
    print("=" * 70)
    
    # Extract and analyze each layer separately
    layer_communities = {}
    layer_stats = {}
    
    for layer in network.get_layers():
        print(f"\n--- Layer: {layer} ---")
        
        # Extract layer-specific edges
        layer_edges = [
            (e[0][0], e[1][0])  # (node, node) without layer info
            for e in network.core_network.edges()
            if e[0][1] == layer and e[1][1] == layer
        ]
        
        # Build single-layer graph
        G_layer = nx.Graph()
        G_layer.add_edges_from(layer_edges)
        
        print(f"  Nodes: {G_layer.number_of_nodes()}")
        print(f"  Edges: {G_layer.number_of_edges()}")
        
        if G_layer.number_of_edges() == 0:
            print(f"  [SKIP] No edges in this layer")
            continue
        
        # Run Louvain on this layer
        communities = louvain_communities(G_layer)
        layer_communities[layer] = communities
        
        # Statistics
        comm_sizes = Counter(communities.values())
        n_comms = len(comm_sizes)
        Q = modularity(communities, G_layer, weight='weight')
        
        layer_stats[layer] = {
            'n_communities': n_comms,
            'modularity': Q,
            'sizes': comm_sizes
        }
        
        print(f"  Communities: {n_comms}")
        print(f"  Modularity: {Q:.4f}")
        print(f"  Largest community: {max(comm_sizes.values())} nodes")
        print(f"  Average size: {sum(comm_sizes.values())/n_comms:.1f}")

**Expected output:**

.. code-block:: text

    LAYER-SPECIFIC COMMUNITY DETECTION
    ======================================================================
    
    --- Layer: layer1 ---
      Nodes: 40
      Edges: 95
      Communities: 4
      Modularity: 0.4123
      Largest community: 15 nodes
      Average size: 10.0
    
    --- Layer: layer2 ---
      Nodes: 40
      Edges: 102
      Communities: 5
      Modularity: 0.3876
      Largest community: 12 nodes
      Average size: 8.0
    
    --- Layer: layer3 ---
      Nodes: 40
      Edges: 87
      Communities: 3
      Modularity: 0.4456
      Largest community: 18 nodes
      Average size: 13.3

**Cross-layer stability analysis:**

Check how consistently nodes are grouped across layers:

.. code-block:: python

    from sklearn.metrics import normalized_mutual_info_score
    import pandas as pd
    
    # Build node-level community assignments per layer
    node_layer_assignments = {}
    all_nodes = set()
    
    for layer, communities in layer_communities.items():
        for node, comm_id in communities.items():
            if node not in node_layer_assignments:
                node_layer_assignments[node] = {}
            node_layer_assignments[node][layer] = comm_id
            all_nodes.add(node)
    
    # For each node, check consistency across layers
    print("\n" + "=" * 70)
    print("CROSS-LAYER STABILITY")
    print("=" * 70)
    
    layers = list(layer_communities.keys())
    
    # Pairwise NMI between layers
    print(f"\nPairwise NMI between layers:")
    print(f"{'Layer Pair':<30} {'NMI':<10} {'Interpretation'}")
    print("-" * 70)
    
    for i in range(len(layers)):
        for j in range(i+1, len(layers)):
            layer1, layer2 = layers[i], layers[j]
            
            # Get common nodes
            nodes1 = set(layer_communities[layer1].keys())
            nodes2 = set(layer_communities[layer2].keys())
            common = nodes1 & nodes2
            
            if not common:
                continue
            
            # Compute NMI
            labels1 = [layer_communities[layer1][n] for n in common]
            labels2 = [layer_communities[layer2][n] for n in common]
            nmi = normalized_mutual_info_score(labels1, labels2)
            
            # Interpret
            if nmi > 0.8:
                interp = "Very similar"
            elif nmi > 0.5:
                interp = "Moderately similar"
            else:
                interp = "Different"
            
            print(f"{layer1} vs {layer2:<20} {nmi:<10.3f} {interp}")
    
    # Node-level stability score
    print(f"\nNode-level stability:")
    
    node_stability = []
    for node in sorted(all_nodes):
        assignments = node_layer_assignments.get(node, {})
        
        # How many layers does this node appear in?
        n_layers = len(assignments)
        
        if n_layers < 2:
            continue
        
        # Are the community IDs consistent?
        # (Community IDs are arbitrary per layer; align by overlap before using this beyond a quick heuristic.)
        comm_ids = list(assignments.values())
        is_stable = len(set(comm_ids)) == 1  # All same community ID
        
        node_stability.append({
            'node': node,
            'n_layers': n_layers,
            'is_stable': is_stable,
            'assignments': assignments
        })
    
    stable_nodes = sum(1 for s in node_stability if s['is_stable'])
    print(f"  Nodes appearing in ≥2 layers: {len(node_stability)}")
    print(f"  Stable nodes (same community ID): {stable_nodes}")
    print(f"  Stability rate: {stable_nodes/len(node_stability)*100:.1f}%")
    
    # Example unstable nodes
    print(f"\n  Example unstable nodes:")
    unstable = [s for s in node_stability if not s['is_stable']][:5]
    for item in unstable:
        print(f"    {item['node']}: {item['assignments']}")

**Expected output:**

.. code-block:: text

    ======================================================================
    CROSS-LAYER STABILITY
    ======================================================================
    
    Pairwise NMI between layers:
    Layer Pair                     NMI        Interpretation
    ----------------------------------------------------------------------
    layer1 vs layer2               0.723      Moderately similar
    layer1 vs layer3               0.456      Different
    layer2 vs layer3               0.512      Moderately similar
    
    Node-level stability:
      Nodes appearing in ≥2 layers: 40
      Stable nodes (same community ID): 18
      Stability rate: 45.0%
      
      Example unstable nodes:
        A5: {'layer1': 0, 'layer2': 1, 'layer3': 0}
        B12: {'layer1': 2, 'layer2': 3}
        C3: {'layer1': 1, 'layer2': 0, 'layer3': 2}
        D7: {'layer1': 0, 'layer2': 2}
        E9: {'layer1': 3, 'layer2': 1, 'layer3': 1}

**Note:** Community labels from independent layer runs are arbitrary; align them (e.g., by maximizing overlap or NMI) before treating numeric IDs as comparable. The simple stability rate above is a heuristic sanity check, not a formal alignment.

**Visualization - Alluvial diagram:**

Show how community membership flows across layers (requires external tools or manual construction):

.. code-block:: python

    import pandas as pd
    
    # Export data for alluvial diagram (use R ggalluvial or similar)
    alluvial_data = []
    
    for node in all_nodes:
        assignments = node_layer_assignments.get(node, {})
        if len(assignments) >= 2:
            row = {'node': node}
            for layer in layers:
                row[f'comm_{layer}'] = assignments.get(layer, -1)
            alluvial_data.append(row)
    
    df_alluvial = pd.DataFrame(alluvial_data)
    df_alluvial.to_csv('alluvial_data.csv', index=False)
    print("\nExported alluvial_data.csv for visualization in R/Python")
    print("Example R code:")
    print("  library(ggalluvial)")
    print("  ggplot(data, aes(axis1=comm_layer1, axis2=comm_layer2, axis3=comm_layer3)) +")
    print("    geom_alluvium(aes(fill=node)) + geom_stratum()")

**When to use layer-specific detection:**

* **Exploratory analysis:** Understand layer-specific structure before multilayer methods
* **Heterogeneous layers:** Layers represent fundamentally different relationships (e.g., co-authorship vs. citation)
* **Baseline comparison:** Compare layer-specific vs. multilayer results to quantify benefit of multilayer methods
* **Dynamic networks:** Detect communities in temporal snapshots and track evolution

Cross-Layer Community Analysis
-------------------------------

**Motivation:**

After detecting communities in the full multilayer network, you want to understand:

* Do communities span multiple layers?
* Which layers contribute most to each community?
* Are there inter-layer bridges (nodes connecting different layer-specific communities)?

**Community × Layer composition:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    from collections import defaultdict
    import numpy as np
    import pandas as pd
    
    # Load network and detect communities
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "datasets/synthetic_multilayer.txt",
        input_type="multiedgelist"
    )
    
    communities = louvain_multilayer(network, gamma=1.0, omega=1.0, random_state=42)
    
    print("CROSS-LAYER COMMUNITY ANALYSIS")
    print("=" * 70)
    
    # Build composition matrix: community × layer
    layers = network.get_layers()
    comm_ids = sorted(set(communities.values()))
    
    composition = defaultdict(lambda: defaultdict(int))
    for (node, layer), comm_id in communities.items():
        composition[comm_id][layer] += 1
    
    # Convert to DataFrame for easier manipulation
    data = []
    for comm_id in comm_ids:
        row = {'community': comm_id}
        for layer in layers:
            row[layer] = composition[comm_id][layer]
        row['total'] = sum(composition[comm_id].values())
        data.append(row)
    
    df_comp = pd.DataFrame(data)
    
    print("\nCommunity × Layer composition:")
    print(df_comp.to_string(index=False))
    
    # Calculate layer entropy for each community
    print("\n" + "-" * 70)
    print("Community layer diversity (entropy):")
    print(f"{'Community':<12} {'Entropy':<10} {'Interpretation'}")
    print("-" * 70)
    
    for comm_id in comm_ids:
        # Calculate entropy: H = -Σ p_i log(p_i)
        counts = [composition[comm_id][layer] for layer in layers]
        total = sum(counts)
        
        if total == 0:
            continue
        
        probs = np.array(counts) / total
        probs = probs[probs > 0]  # Remove zeros
        entropy = -np.sum(probs * np.log2(probs))
        max_entropy = np.log2(len(layers))  # Maximum possible entropy
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        # Interpret
        if normalized_entropy > 0.9:
            interp = "Highly dispersed (spans all layers)"
        elif normalized_entropy > 0.5:
            interp = "Moderately dispersed (multi-layer)"
        else:
            interp = "Concentrated (layer-specific)"
        
        print(f"C{comm_id:<11} {entropy:<10.3f} {interp}")

**Expected output:**

.. code-block:: text

    CROSS-LAYER COMMUNITY ANALYSIS
    ======================================================================
    
    Community × Layer composition:
     community  layer1  layer2  layer3  total
             0      15      14      16     45
             1      18      20       0     38
             2       0       0      22     22
             3       7       6       2     15
    
    ----------------------------------------------------------------------
    Community layer diversity (entropy):
    Community    Entropy    Interpretation
    ----------------------------------------------------------------------
    C0           1.585      Highly dispersed (spans all layers)
    C1           0.997      Moderately dispersed (multi-layer)
    C2           0.000      Concentrated (layer-specific)
    C3           1.252      Moderately dispersed (multi-layer)

**Inter-layer bridges:**

Identify nodes that connect different communities across layers:

.. code-block:: python

    print("\n" + "=" * 70)
    print("INTER-LAYER BRIDGE ANALYSIS")
    print("=" * 70)
    
    # For each node, check if it belongs to different communities in different layers
    node_communities = defaultdict(dict)  # node -> layer -> comm_id
    
    for (node, layer), comm_id in communities.items():
        node_communities[node][layer] = comm_id
    
    # Identify bridge nodes
    bridge_nodes = []
    for node, layer_comms in node_communities.items():
        if len(layer_comms) < 2:
            continue
        
        # Check if community IDs differ across layers
        comm_ids = set(layer_comms.values())
        if len(comm_ids) > 1:
            bridge_nodes.append({
                'node': node,
                'n_layers': len(layer_comms),
                'n_communities': len(comm_ids),
                'assignments': dict(layer_comms)
            })
    
    print(f"\nBridge nodes (spanning multiple communities across layers):")
    print(f"  Total nodes: {len(node_communities)}")
    print(f"  Bridge nodes: {len(bridge_nodes)} ({len(bridge_nodes)/len(node_communities)*100:.1f}%)")
    
    # Show examples
    print(f"\n  Top 10 bridge nodes:")
    print(f"  {'Node':<15} {'Layers':<10} {'Communities':<15} {'Assignments'}")
    print("  " + "-" * 65)
    
    bridge_nodes_sorted = sorted(bridge_nodes, key=lambda x: x['n_communities'], reverse=True)
    for item in bridge_nodes_sorted[:10]:
        node = item['node']
        n_layers = item['n_layers']
        n_comms = item['n_communities']
        assignments = ', '.join([f"{l}:C{c}" for l, c in sorted(item['assignments'].items())])
        print(f"  {str(node):<15} {n_layers:<10} {n_comms:<15} {assignments}")

**Expected output:**

.. code-block:: text

    ======================================================================
    INTER-LAYER BRIDGE ANALYSIS
    ======================================================================
    
    Bridge nodes (spanning multiple communities across layers):
      Total nodes: 40
      Bridge nodes: 12 (30.0%)
      
      Top 10 bridge nodes:
      Node            Layers     Communities     Assignments
      -----------------------------------------------------------------
      A5              3          3               layer1:C0, layer2:C1, layer3:C2
      B12             3          2               layer1:C0, layer2:C1, layer3:C1
      C3              3          2               layer1:C1, layer2:C0, layer3:C0
      D7              2          2               layer1:C0, layer2:C3
      E9              3          2               layer1:C3, layer2:C1, layer3:C1
      F4              2          2               layer1:C1, layer2:C0
      G8              3          2               layer1:C0, layer2:C0, layer3:C2
      H2              2          2               layer1:C3, layer2:C0
      I6              3          2               layer1:C1, layer2:C1, layer3:C2
      J11             2          2               layer1:C0, layer2:C1

**Community connectivity graph:**

Build a meta-graph where nodes are communities and edges represent inter-layer bridges:

.. code-block:: python

    import networkx as nx
    import matplotlib.pyplot as plt
    
    # Build community connectivity graph
    G_meta = nx.Graph()
    
    # Add community nodes
    for comm_id in comm_ids:
        G_meta.add_node(f"C{comm_id}")
    
    # Add edges for bridge nodes
    for item in bridge_nodes:
        comms = list(item['assignments'].values())
        # Connect all pairs of communities this node bridges
        for i in range(len(comms)):
            for j in range(i+1, len(comms)):
                c1, c2 = f"C{comms[i]}", f"C{comms[j]}"
                if G_meta.has_edge(c1, c2):
                    G_meta[c1][c2]['weight'] += 1
                else:
                    G_meta.add_edge(c1, c2, weight=1)
    
    print(f"\n" + "=" * 70)
    print("COMMUNITY CONNECTIVITY")
    print("=" * 70)
    print(f"\nCommunity-level connectivity:")
    print(f"  Communities: {G_meta.number_of_nodes()}")
    print(f"  Inter-community bridges: {G_meta.number_of_edges()}")
    
    if G_meta.number_of_edges() > 0:
        print(f"\n  Strongest bridges (top 5):")
        edges_sorted = sorted(G_meta.edges(data=True), key=lambda x: x[2]['weight'], reverse=True)
        for c1, c2, data in edges_sorted[:5]:
            print(f"    {c1} ↔ {c2}: {data['weight']} bridge nodes")
        
        # Visualize meta-graph
        plt.figure(figsize=(8, 8))
        pos = nx.spring_layout(G_meta, seed=42)
        
        # Edge widths proportional to weight
        weights = [G_meta[u][v]['weight'] for u, v in G_meta.edges()]
        max_weight = max(weights) if weights else 1
        edge_widths = [3 * w / max_weight for w in weights]
        
        nx.draw_networkx_nodes(G_meta, pos, node_size=800, node_color='lightblue')
        nx.draw_networkx_labels(G_meta, pos, font_size=12, font_weight='bold')
        nx.draw_networkx_edges(G_meta, pos, width=edge_widths, alpha=0.6)
        
        # Edge labels
        edge_labels = {(u, v): f"{G_meta[u][v]['weight']}" for u, v in G_meta.edges()}
        nx.draw_networkx_edge_labels(G_meta, pos, edge_labels, font_size=8)
        
        plt.title('Community Connectivity Meta-Graph\n(Edge width = number of bridge nodes)', fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig('community_connectivity.png', dpi=300, bbox_inches='tight')
        plt.show()
        print(f"\n  Visualization saved to: community_connectivity.png")

**Expected output:**

.. code-block:: text

    ======================================================================
    COMMUNITY CONNECTIVITY
    ======================================================================
    
    Community-level connectivity:
      Communities: 4
      Inter-community bridges: 5
      
      Strongest bridges (top 5):
        C0 ↔ C1: 5 bridge nodes
        C1 ↔ C2: 3 bridge nodes
        C0 ↔ C3: 2 bridge nodes
        C1 ↔ C3: 1 bridge nodes
        C0 ↔ C2: 1 bridge nodes
      
      Visualization saved to: community_connectivity.png

**Use cases:**

* **Biological networks:** Proteins bridging functional modules across different interaction types
* **Social networks:** Individuals connecting different social circles across contexts
* **Transportation:** Transfer hubs connecting regional clusters across transport modes

Quality Metrics
---------------

**Why quality metrics matter:**

Quality metrics help you:

1. **Compare algorithms** objectively
2. **Tune parameters** (e.g., choosing optimal :math:`\omega` in multilayer Louvain)
3. **Validate results** (high Q suggests real structure, not random fluctuations)
4. **Detect overfitting** (too many tiny communities = over-segmentation)

Compute Modularity
~~~~~~~~~~~~~~~~~~

**Single-layer modularity:**

For flattened networks, use the Newman-Girvan modularity:

.. math::

    Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.community_wrapper import louvain_communities
    from py3plex.algorithms.community_detection.community_louvain import modularity
    import networkx as nx
    
    # Load network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "datasets/synthetic_multilayer.txt",
        input_type="multiedgelist"
    )
    
    # Detect communities
    communities = louvain_communities(network)
    
    # Convert to NetworkX for modularity calculation
    G = nx.Graph()
    for edge in network.core_network.edges():
        G.add_edge(edge[0], edge[1])
    
    # Calculate modularity
    Q = modularity(communities, G, weight='weight')
    
    print(f"Modularity Q: {Q:.4f}")
    
    # Interpretation
    if Q > 0.7:
        print("  Interpretation: Excellent community structure")
    elif Q > 0.4:
        print("  Interpretation: Strong community structure")
    elif Q > 0.2:
        print("  Interpretation: Moderate community structure")
    else:
        print("  Interpretation: Weak or no community structure")

**Expected output:**

.. code-block:: text

    Modularity Q: 0.4234
      Interpretation: Strong community structure

**Multilayer modularity:**

For multilayer networks, use the generalized modularity that accounts for inter-layer coupling:

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_modularity import (
        louvain_multilayer,
        multilayer_modularity
    )
    
    # Run multilayer Louvain
    communities = louvain_multilayer(
        network,
        gamma=1.0,
        omega=1.0,
        random_state=42
    )
    
    # Calculate multilayer modularity
    Q_multi = multilayer_modularity(
        network,
        communities,
        gamma=1.0,
        omega=1.0
    )
    
    print(f"Multilayer modularity Q: {Q_multi:.4f}")

**Expected output:**

.. code-block:: text

    Multilayer modularity Q: 0.4589

**Modularity resolution:**

Modularity has a **resolution limit**: in undirected graphs it struggles to detect communities much smaller than roughly :math:`\sqrt{2m}` (with :math:`m` edges). The resolution parameter :math:`\gamma` can help:

.. code-block:: python

    # Test different resolution parameters
    print("Modularity vs. resolution:")
    print(f"{'γ':<10} {'#Comm':<10} {'Q':<10} {'Avg Size':<10}")
    print("-" * 45)
    
    for gamma in [0.5, 1.0, 1.5, 2.0]:
        comms = louvain_multilayer(
            network, gamma=gamma, omega=1.0, random_state=42
        )
        n_comms = len(set(comms.values()))
        Q = multilayer_modularity(network, comms, gamma=gamma, omega=1.0)
        avg_size = len(comms) / n_comms
        
        print(f"{gamma:<10.1f} {n_comms:<10} {Q:<10.4f} {avg_size:<10.1f}")

**Expected output:**

.. code-block:: text

    Modularity vs. resolution:
    γ          #Comm      Q          Avg Size  
    ---------------------------------------------
    0.5        3          0.3456     40.0      
    1.0        5          0.4589     24.0      
    1.5        8          0.4123     15.0      
    2.0        12         0.3678     10.0      

**Interpretation:**

* **Lower γ:** Fewer, larger communities (under-segmentation)
* **Higher γ:** More, smaller communities (over-segmentation)
* **Optimal γ:** Maximum Q (but check that communities are meaningful!)

Additional Quality Metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**1. Coverage** (fraction of edges within communities):

.. code-block:: python

    def calculate_coverage(network, communities):
        """Fraction of edges within communities."""
        intra_edges = 0
        total_edges = 0
        
        for source, target in network.core_network.edges():
            total_edges += 1
            if communities.get(source) == communities.get(target):
                intra_edges += 1
        
        return intra_edges / total_edges if total_edges > 0 else 0
    
    coverage = calculate_coverage(network, communities)
    print(f"Coverage: {coverage:.4f}  (fraction of intra-community edges)")

**Expected output:**

.. code-block:: text

    Coverage: 0.8234  (fraction of intra-community edges)

**2. Performance** (combines intra-community edges and inter-community non-edges):

.. code-block:: python

    def calculate_performance(network, communities):
        """Performance metric (Fortunato 2010)."""
        nodes = list(communities.keys())
        n = len(nodes)
        
        # Count intra-community edges and inter-community non-edges
        intra_edges = 0
        inter_non_edges = 0
        total_pairs = 0
        
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                node1, node2 = nodes[i], nodes[j]
                same_community = communities[node1] == communities[node2]
                is_edge = network.core_network.has_edge(node1, node2)
                
                if same_community and is_edge:
                    intra_edges += 1
                elif not same_community and not is_edge:
                    inter_non_edges += 1
                
                total_pairs += 1
        
        return (intra_edges + inter_non_edges) / total_pairs if total_pairs > 0 else 0
    
    performance = calculate_performance(network, communities)
    print(f"Performance: {performance:.4f}")

**Expected output:**

.. code-block:: text

    Performance: 0.7456

**Tip:** The double loop is :math:`O(n^2)` over nodes; use it on moderate-size graphs or sample nodes when the network is huge.

**3. Conductance** (quality of community boundaries):

.. code-block:: python

    def calculate_conductance(network, communities, comm_id):
        """Conductance of a specific community (lower is better)."""
        comm_nodes = [n for n, c in communities.items() if c == comm_id]
        
        if not comm_nodes:
            return None
        
        # Count edges
        internal_edges = 0
        boundary_edges = 0
        
        for node in comm_nodes:
            neighbors = list(network.core_network.neighbors(node))
            for neighbor in neighbors:
                if communities.get(neighbor) == comm_id:
                    internal_edges += 0.5  # Count each edge once
                else:
                    boundary_edges += 1
        
        volume = internal_edges * 2 + boundary_edges  # Volume of the community
        return boundary_edges / volume if volume > 0 else 0
    
    # Calculate for all communities
    print("\nConductance per community (lower = better defined):")
    for comm_id in sorted(set(communities.values())):
        cond = calculate_conductance(network, communities, comm_id)
        if cond is not None:
            print(f"  Community {comm_id}: {cond:.4f}")

**Expected output:**

.. code-block:: text

    Conductance per community (lower = better defined):
      Community 0: 0.1234
      Community 1: 0.2456
      Community 2: 0.0987
      Community 3: 0.3123
      Community 4: 0.1789

**4. Null model comparison** (compare to random partitions):

.. code-block:: python

    import random
    
    # Calculate Q for real partition
    Q_real = multilayer_modularity(network, communities, gamma=1.0, omega=1.0)
    
    # Generate random partitions and calculate Q
    nodes = list(communities.keys())
    n_communities = len(set(communities.values()))
    
    Q_random = []
    for trial in range(100):
        # Random partition with same number of communities
        random_comms = {node: random.randint(0, n_communities-1) for node in nodes}
        Q_rand = multilayer_modularity(network, random_comms, gamma=1.0, omega=1.0)
        Q_random.append(Q_rand)
    
    Q_rand_mean = np.mean(Q_random)
    Q_rand_std = np.std(Q_random)
    z_score = (Q_real - Q_rand_mean) / Q_rand_std if Q_rand_std > 0 else 0
    
    print(f"\nNull model comparison:")
    print(f"  Real Q: {Q_real:.4f}")
    print(f"  Random Q (mean ± std): {Q_rand_mean:.4f} ± {Q_rand_std:.4f}")
    print(f"  Z-score: {z_score:.2f}")
    
    if z_score > 3:
        print(f"  Interpretation: Highly significant (real structure)")
    elif z_score > 2:
        print(f"  Interpretation: Significant (likely real structure)")
    else:
        print(f"  Interpretation: Not significant (could be random)")

**Expected output:**

.. code-block:: text

    Null model comparison:
      Real Q: 0.4589
      Random Q (mean ± std): 0.0023 ± 0.0145
      Z-score: 31.49
      Interpretation: Highly significant (real structure)

**Summary of metrics:**

* **Modularity (Q):** Overall quality, general-purpose
* **Coverage:** Simple interpretability (% internal edges)
* **Performance:** Balances true positives and true negatives
* **Conductance:** Community boundary quality (per-community)
* **Null model:** Statistical significance test
* **Replica Consistency (RC):** Multilayer coherence guardrail
* **Layer Entropy (H):** Degeneracy guardrail for multilayer networks

**Recommendation:** Always report modularity + at least one other metric to get a complete picture.

Multilayer Quality Metrics (Guardrails)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For multilayer community detection, two specialized quality metrics serve as **guardrails** against degenerate partitions:

1. **Replica Consistency (RC)**: Measures whether replicas of the same node across layers are assigned to the same community
2. **Layer Entropy (H)**: Measures the balance of community sizes within each layer, averaged across layers

**What are guardrails?**

Guardrails are metrics that detect pathological partitions but are not primary optimization objectives. They ensure that:

* Communities respect node identity across layers (RC)
* Partitions are not degenerate giant clusters or extreme fragmentation (H)

**Replica Consistency:**

Formula: For each node v with replicas in L_v layers (|L_v| ≥ 2):

.. math::

    RC(v) = \frac{2}{|L_v|(|L_v|-1)} \sum_{\ell_i < \ell_j} 1[c(v,\ell_i) = c(v,\ell_j)]

    RC = \frac{1}{|\{v: |L_v|\ge 2\}|} \sum_v RC(v)

RC ranges from 0 to 1:

* **RC = 1.0**: All replicas of each node have the same community (perfect coherence)
* **RC = 0.0**: No agreement (random assignment)
* **RC ∈ (0,1)**: Partial consistency

**Layer Entropy:**

Formula: For each layer ℓ with C_ℓ communities:

.. math::

    H_\ell = -\sum_i p_i^\ell \log(p_i^\ell) / \log(|C_\ell|)

    H = \text{mean}_\ell(H_\ell), \quad \text{clipped to } [0.1, 0.9]

H ranges from 0.1 to 0.9 (clipped):

* **H ≈ 0.9**: Balanced communities in all layers
* **H ≈ 0.1**: Giant cluster or extreme fragmentation (degenerate)
* **H ∈ (0.1,0.9)**: Normal partition

**Usage example:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    from py3plex.algorithms.community_detection.multilayer_quality_metrics import (
        replica_consistency,
        layer_entropy
    )
    
    # Load network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "datasets/synthetic_multilayer.txt",
        input_type="multiedgelist"
    )
    
    # Detect communities
    communities = louvain_multilayer(network, gamma=1.0, omega=1.0, random_state=42)
    
    # Compute multilayer quality metrics
    rc = replica_consistency(communities, network)
    h = layer_entropy(communities, network)
    
    print(f"Replica Consistency: {rc:.4f}")
    print(f"Layer Entropy: {h:.4f}")
    
    # Interpret
    if rc > 0.8:
        print("  ✓ High replica consistency (nodes coherent across layers)")
    elif rc < 0.3:
        print("  ⚠ Low replica consistency (nodes fragmented across layers)")
    else:
        print("  → Moderate replica consistency")
    
    if h > 0.7:
        print("  ✓ High layer entropy (balanced communities)")
    elif h < 0.3:
        print("  ⚠ Low layer entropy (degenerate partition)")
    else:
        print("  → Moderate layer entropy")

**Expected output:**

.. code-block:: text

    Replica Consistency: 0.8765
    Layer Entropy: 0.7234
      ✓ High replica consistency (nodes coherent across layers)
      ✓ High layer entropy (balanced communities)

**Comparison: good vs. bad partitions:**

.. code-block:: python

    # Good partition: coherent and balanced
    good_partition = {
        ('A', 'layer1'): 0, ('A', 'layer2'): 0, ('A', 'layer3'): 0,
        ('B', 'layer1'): 1, ('B', 'layer2'): 1, ('B', 'layer3'): 1,
        ('C', 'layer1'): 0, ('C', 'layer2'): 0, ('C', 'layer3'): 0,
        ('D', 'layer1'): 1, ('D', 'layer2'): 1, ('D', 'layer3'): 1,
    }
    
    # Bad partition 1: giant cluster (low entropy)
    giant_cluster = {
        ('A', 'layer1'): 0, ('A', 'layer2'): 0, ('A', 'layer3'): 0,
        ('B', 'layer1'): 0, ('B', 'layer2'): 0, ('B', 'layer3'): 0,
        ('C', 'layer1'): 0, ('C', 'layer2'): 0, ('C', 'layer3'): 0,
        ('D', 'layer1'): 0, ('D', 'layer2'): 0, ('D', 'layer3'): 0,
    }
    
    # Bad partition 2: fragmented replicas (low RC)
    fragmented = {
        ('A', 'layer1'): 0, ('A', 'layer2'): 1, ('A', 'layer3'): 2,
        ('B', 'layer1'): 3, ('B', 'layer2'): 4, ('B', 'layer3'): 5,
        ('C', 'layer1'): 6, ('C', 'layer2'): 7, ('C', 'layer3'): 8,
        ('D', 'layer1'): 9, ('D', 'layer2'): 10, ('D', 'layer3'): 11,
    }
    
    print("Good partition:")
    print(f"  RC={replica_consistency(good_partition, network):.3f}, H={layer_entropy(good_partition, network):.3f}")
    
    print("\nGiant cluster (degenerate):")
    print(f"  RC={replica_consistency(giant_cluster, network):.3f}, H={layer_entropy(giant_cluster, network):.3f}")
    
    print("\nFragmented replicas (incoherent):")
    print(f"  RC={replica_consistency(fragmented, network):.3f}, H={layer_entropy(fragmented, network):.3f}")

**Expected output:**

.. code-block:: text

    Good partition:
      RC=1.000, H=0.900
    
    Giant cluster (degenerate):
      RC=1.000, H=0.100
    
    Fragmented replicas (incoherent):
      RC=0.000, H=0.900

**Integration with AutoCommunity:**

These metrics are automatically included in AutoCommunity's multi-objective evaluation:

.. code-block:: python

    from py3plex.algorithms.community_detection import auto_select_community
    
    # AutoCommunity will use these metrics as guardrails
    result = auto_select_community(
        network,
        fast=True,
        seed=42
    )
    
    # Access metrics from evaluation matrix
    eval_matrix = result.evaluation_matrix
    
    print("All metrics computed:")
    print(eval_matrix[['algorithm_id', 'modularity', 'replica_consistency', 'layer_entropy']])

**When to use these metrics:**

* **RC**: When node identity across layers is important (e.g., same protein in different interaction types)
* **H**: To detect degenerate partitions (giant clusters or extreme fragmentation)
* **Both**: As sanity checks after multilayer community detection
* **AutoCommunity**: These are included by default; they contribute ~22% total weight in the default metric set

**Typical ranges:**

* **RC > 0.8**: Excellent replica consistency
* **RC ∈ [0.5, 0.8]**: Good consistency
* **RC < 0.5**: Poor consistency (investigate layer-specific communities)
* **H > 0.7**: Well-balanced communities
* **H ∈ [0.3, 0.7]**: Normal range
* **H < 0.3**: Degenerate partition (too few or too many communities)

**Performance characteristics:**

* **RC**: O(Σ_v |L_v|^2) where L_v is layers per node (efficient count-based implementation)
* **H**: O(|assignments|) linear in node-layer assignments
* **Both**: Fast enough for large networks (< 1 second for 10,000 node-layers)

**Label-permutation invariance:**

RC is **label-permutation invariant**: it only compares community labels within each node across layers. Different algorithms can produce arbitrary label numbering, and RC will still work correctly.

**Summary of metrics:**

* **Modularity (Q):** Overall quality, general-purpose
* **Coverage:** Simple interpretability (% internal edges)
* **Performance:** Balances true positives and true negatives
* **Conductance:** Community boundary quality (per-community)
* **Null model:** Statistical significance test

**Recommendation:** Always report modularity + at least one other metric to get a complete picture.

CLI Cross-Reference (Optional)
------------------------------

py3plex provides command-line tools for quick community detection without writing Python code.

**Basic usage:**

.. code-block:: bash

    # Detect communities using Louvain (default algorithm)
    py3plex community datasets/network.edgelist \
        --algorithm louvain \
        --output communities.json
    
    # Using Infomap (requires Infomap binary installed)
    py3plex community datasets/network.edgelist \
        --algorithm infomap \
        --output communities.json
    
    # Using Label Propagation (fast for large networks)
    py3plex community datasets/network.edgelist \
        --algorithm label_prop \
        --output communities.json
    
    # With custom resolution parameter for Louvain
    py3plex community datasets/network.edgelist \
        --algorithm louvain \
        --resolution 1.5 \
        --output communities.json

**Available algorithms:**

* ``louvain``: Fast Louvain method (default) - optimizes modularity on flattened network
* ``infomap``: Infomap algorithm - requires Infomap binary (https://www.mapequation.org/infomap/)
* ``label_prop``: Label propagation - very fast, suitable for large networks

**Output format:**

The CLI outputs JSON files with structure:

.. code-block:: json

    {
      "algorithm": "louvain",
      "num_communities": 5,
      "communities": {
        "node1": 0,
        "node2": 0,
        "node3": 1,
        ...
      },
      "community_sizes": {
        "0": 42,
        "1": 27,
        ...
      }
    }

**Note on multilayer networks:**

The current CLI ``community`` command operates on flattened networks. For multilayer-specific community detection (with inter-layer coupling), use the Python API with ``louvain_multilayer()`` as shown in the examples above. Future CLI versions may add multilayer support.

**Viewing results:**

After running the CLI command, you can analyze the JSON output:

.. code-block:: bash

    # View community statistics
    py3plex community network.edgelist --algorithm louvain
    # Output printed to console if no --output specified

For full CLI documentation, see :doc:`../tutorials/cli_usage` or :doc:`../deployment/cli_usage`.

Next Steps
----------

**Further reading:**

* **Algorithms:** :doc:`../concepts/algorithm_landscape` - Deep dive into community detection theory
* **Visualization:** :doc:`visualize_networks` - Advanced community visualization techniques
* **Benchmark:** :doc:`../tutorials/benchmark_communities` - Compare with ground-truth communities
* **Temporal analysis:** :doc:`../tutorials/temporal_communities` - Track community evolution over time

**Recommended workflows:**

1. **Exploratory:** Start with Louvain → visualize → if unsatisfied, try multilayer Louvain or Infomap
2. **Publication:** Run multiple algorithms → compare → report consensus + metrics
3. **Large-scale:** Use label propagation for initial exploration → refine with Louvain on filtered subgraph
4. **Temporal:** Detect communities in snapshots → track with NMI → visualize with alluvial diagrams

**Common pitfalls:**

* **Resolution limit:** Modularity cannot detect communities smaller than :math:`\sqrt{m}`
* **Non-determinism:** Many algorithms are stochastic; always set random seeds for reproducibility
* **Overfitting:** Too many tiny communities suggests over-segmentation; try lower resolution
* **Layer coupling:** For multilayer networks, always try multiple :math:`\omega` values

Automatic Algorithm Selection (AutoCommunity)
----------------------------------------------

**When you don't know which algorithm to use:** py3plex provides automatic algorithm selection that evaluates multiple algorithms on multiple quality metrics and picks the winner using a "most wins" decision engine.

**Quick example:**

.. code-block:: python

    from py3plex.algorithms.community_detection import auto_select_community
    
    # Automatically select best algorithm
    result = auto_select_community(network, fast=True, seed=42)
    
    # See why it won
    print(result.explain())
    
    # View leaderboard
    print(result.leaderboard)
    
    # Use the partition
    network.assign_partition(result.partition)

**With DSL:**

.. code-block:: python

    from py3plex.dsl import Q
    
    result = Q.communities().auto_select(fast=True, seed=42).execute(network)
    print(result.explain())

**How it works:**

1. Detects available algorithms (Leiden, Louvain, etc.)
2. Runs candidates with parameter grids (gamma, omega)
3. Evaluates on multiple metrics (modularity, coverage, stability, etc.)
4. Selects winner by pairwise "most wins" across metrics
5. Applies bucket caps to prevent any metric category from dominating

**Key parameters:**

* ``fast=True``: Use smaller parameter grids (default)
* ``max_candidates=10``: Maximum algorithms to evaluate
* ``seed=0``: Random seed for determinism
* ``uq=False``: Enable uncertainty quantification for stability metrics

**Result object:**

* ``result.partition``: Winning partition
* ``result.algorithm``: Algorithm name and parameters
* ``result.leaderboard``: DataFrame ranking all candidates
* ``result.explain()``: Natural language explanation of why it won
* ``result.to_dict()``: Serializable dictionary

**When to use:** Exploratory analysis, comparing algorithms fairly, reproducible algorithm choice with provenance.

See AGENTS.md for complete API documentation.

Hierarchical Flow-Based Community Detection
--------------------------------------------

**Goal:** Detect hierarchical community structure based on flow/diffusion dynamics rather than modularity optimization.

**What is hierarchical flow-based detection?**

Unlike modularity-based methods (Louvain, Leiden) that optimize a single quality function, hierarchical flow-based community detection (HFCD) identifies communities as sets of nodes that **retain probability mass** under random walk dynamics for longer times than expected by chance. The hierarchy emerges naturally from observing how flow-based communities merge as diffusion time increases.

**Key concepts:**

* **Communities = flow retention**: Groups that trap random walkers internally
* **Hierarchy = time scales**: Different community structures at different diffusion times
* **No resolution parameter**: Hierarchy levels correspond to stability plateaus
* **Multilayer-aware**: Native support for interlayer coupling via :math:`\alpha` parameter

**Mathematical foundation:**

For a multilayer network, construct transition operator:

.. math::

    P = \alpha P_{\text{intra}} + (1-\alpha) P_{\text{inter}}

where :math:`\alpha \in [0,1]` controls interlayer coupling. Flow affinity at scale :math:`t`:

.. math::

    F(t) = \sum_{k=1}^{t} P^k, \quad S_{ij}(t) = \frac{F_{ij}(t) + F_{ji}(t)}{2}

Community quality (flow retention):

.. math::

    \text{FlowRetention}(C, t) = \frac{\text{internal flow}}{\text{total flow}}

**Basic example:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection import flow_hierarchical_communities
    
    # Load network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "datasets/synthetic_multilayer.txt",
        input_type="multiedgelist"
    )
    
    # Run hierarchical flow detection
    result = flow_hierarchical_communities(
        network,
        approx="mc",      # Monte Carlo (scalable) or "exact"
        alpha=0.8,        # Interlayer coupling (0=full, 1=independent)
        n_walks=100,      # MC walks per node
        seed=42           # Reproducibility
    )
    
    # Access best partition (maximum stability)
    partition = result.get_partition()
    
    # Get partition with specific number of communities
    partition_3 = result.get_flat_partition(n_communities=3)
    
    # Display hierarchy
    print(result.summary())
    
    # Explore all hierarchy levels
    for scale, part in result.hierarchy_levels.items():
        stability = result.stability_scores[scale]
        n_comms = len(set(part.values()))
        print(f"Scale {scale}: {n_comms} communities (stability={stability:.3f})")

**Expected output:**

.. code-block:: text

    ======================================================================
    Hierarchical Flow-Based Community Detection Results
    ======================================================================
    Total nodes: 120
    Hierarchy levels detected: 4
    Scale range: [1.00, 8.00]
    
    Best partition (max stability):
      Scale: 4.00
      Stability: 0.8523
      Communities: 5
    
    Scale 1.0: 120 communities (stability=1.000)
    Scale 2.0: 12 communities (stability=0.912)
    Scale 4.0: 5 communities (stability=0.852)
    Scale 8.0: 2 communities (stability=0.734)

**Result structure:**

The ``FlowHierarchyResult`` object contains:

* ``dendrogram``: List of merge events (comm_i, comm_j, scale, stability_before, stability_after)
* ``hierarchy_levels``: Dict[scale → partition] at all detected levels
* ``stability_scores``: Flow retention at each scale (range [0,1])
* ``merge_scales``: Array of scales where merges occurred
* ``metadata``: Algorithm config (flow_type, alpha, approx, seed, scale_schedule)

**Multilayer-specific parameters:**

.. code-block:: python

    # High alpha (0.9): Layers mostly independent
    result_high = flow_hierarchical_communities(net, alpha=0.9, seed=42)
    
    # Low alpha (0.2): Strong interlayer coupling
    result_low = flow_hierarchical_communities(net, alpha=0.2, seed=42)
    
    # Communities bridge layers based on alpha

**Approximation methods:**

* **Monte Carlo (approx="mc")**: Memory-efficient O(n × walks), slight randomness (use seed)
* **Exact (approx="exact")**: Deterministic O(n²), memory-intensive for large networks

**Algorithm complexity:**

* **Time**: O(t × m × k) where t=scales, m=edges, k=merges
* **Space**: O(n²) exact, O(n × walks) Monte Carlo
* **Recommended**: n < 10,000 (exact) or n < 100,000 (MC)

**When to use:**

* Understanding hierarchical organization at multiple scales
* Networks where modularity optimization may miss structure
* Multilayer networks with different layer coupling strengths
* Temporal networks where communities evolve across time slices
* Comparing with flow-based baselines (Infomap, Markov Stability)

**Comparison with other methods:**

+-------------------+---------------------------+---------------------------+
| Aspect            | Flow Hierarchy            | Louvain/Leiden            |
+===================+===========================+===========================+
| Quality metric    | Flow retention            | Modularity                |
+-------------------+---------------------------+---------------------------+
| Hierarchy         | Full dendrogram           | Flat partition            |
+-------------------+---------------------------+---------------------------+
| Scale selection   | Stability plateaus        | Resolution parameter γ    |
+-------------------+---------------------------+---------------------------+
| Multilayer        | Native (α coupling)       | Requires ω parameter      |
+-------------------+---------------------------+---------------------------+
| Determinism       | Seed-controlled (MC/exact)| Heuristic-dependent       |
+-------------------+---------------------------+---------------------------+

**Examples:**

* Basic usage: :download:`example_flow_hierarchy_basic.py <../../examples/communities/example_flow_hierarchy_basic.py>`
* Multilayer with alpha variations: :download:`example_flow_hierarchy_multilayer.py <../../examples/communities/example_flow_hierarchy_multilayer.py>`

**References:**

* Schaub et al., "Markov Dynamics as a Zooming Lens for Multiscale Community Detection", *PLoS ONE* 7(2): e32210 (2012)
* Delvenne et al., "Stability of graph communities across time scales", *PNAS* 107(29): 12755-12760 (2010)
* Lambiotte et al., "Random Walks, Markov Processes and the Multiscale Modular Organization of Complex Networks", *IEEE Trans. Network Science and Engineering* 1(2): 76-90 (2014)

**Community detection checklist:**

- [ ] Run at least 2 different algorithms
- [ ] Calculate modularity and at least one other quality metric
- [ ] Visualize size distribution to check for over/under-segmentation
- [ ] Compare with null model to ensure statistical significance
- [ ] For multilayer: test multiple :math:`\omega` values
- [ ] Export results to CSV for downstream analysis
- [ ] Document random seeds for reproducibility

**Questions?**

* GitHub Issues: https://github.com/SkBlaz/py3plex/issues
* Documentation: https://skblaz.github.io/py3plex/
* Examples: ``examples/communities/`` directory in the repository

**Key References:**

* Blondel, V. D., Guillaume, J. L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics: Theory and Experiment*, 2008(10), P10008.
* Mucha, P. J., Richardson, T., Macon, K., Porter, M. A., & Onnela, J. P. (2010). Community structure in time-dependent, multiscale, and multiplex networks. *Science*, 328(5980), 876-878.
* Rosvall, M., & Bergstrom, C. T. (2008). Maps of random walks on complex networks reveal community structure. *Proceedings of the National Academy of Sciences*, 105(4), 1118-1123.
* Raghavan, U. N., Albert, R., & Kumara, S. (2007). Near linear time algorithm to detect community structures in large-scale networks. *Physical Review E*, 76(3), 036106.
