How to Reproduce Common Analysis Workflows
===========================================

**Goal:** Use ready-made recipes for common multilayer network analysis tasks.

**Prerequisites:** Basic understanding of py3plex (see :doc:`../getting_started/tutorial_10min`).

**About examples:** Code and outputs below use the bundled synthetic datasets unless noted. Replace file paths with your own data; metrics will differ accordingly.

Complete Workflows
------------------

This guide links to detailed recipes and case studies. For step-by-step implementations, see:

* **Recipes:** :doc:`../user_guide/recipes_and_workflows` — Focused solutions for specific tasks
* **Case Studies:** :doc:`../user_guide/case_studies` — Complete end-to-end analyses
* **Examples:** :doc:`../examples/index` — Runnable code examples

Quick Recipe Index
------------------

Network Construction
~~~~~~~~~~~~~~~~~~~~

* **Building from edge lists** → :doc:`load_and_build_networks`
* **Converting from NetworkX** → :doc:`../user_guide/recipes_and_workflows` (Recipe 1)
* **Loading temporal networks** → :doc:`../reference/api_index` (Temporal section)

Statistical Analysis
~~~~~~~~~~~~~~~~~~~~

* **Computing multilayer statistics** → :doc:`compute_statistics`
* **Comparing layers** → :doc:`../user_guide/recipes_and_workflows` (Recipe 3)
* **Node versatility analysis** → :doc:`../user_guide/recipes_and_workflows` (Recipe 4)

Community Detection
~~~~~~~~~~~~~~~~~~~

* **Multilayer Louvain** → :doc:`run_community_detection`
* **Cross-layer community comparison** → :doc:`../user_guide/recipes_and_workflows` (Recipe 5)
* **Community stability analysis** → :doc:`../user_guide/case_studies` (Case Study 2)

Network Embeddings
~~~~~~~~~~~~~~~~~~

* **Node2Vec for link prediction** → :doc:`run_random_walks`
* **Embedding-based clustering** → :doc:`../user_guide/recipes_and_workflows` (Recipe 7)
* **Layer-specific embeddings** → :doc:`run_random_walks`

Visualization
~~~~~~~~~~~~~

* **Publication-ready plots** → :doc:`visualize_networks`
* **Interactive visualizations** → :doc:`visualize_networks`
* **Layer comparison plots** → :doc:`../user_guide/recipes_and_workflows` (Recipe 9)

Domain-Specific Workflows
--------------------------

Social Networks
~~~~~~~~~~~~~~~

**Multi-platform social analysis:**

.. code-block:: python

    # See: user_guide/case_studies.rst - Social Network Case Study
    # 1. Load data from multiple platforms
    # 2. Detect cross-platform communities
    # 3. Identify influential users
    # 4. Analyze information diffusion

See :doc:`../user_guide/case_studies` for complete implementation.

Biological Networks
~~~~~~~~~~~~~~~~~~~

**Multi-omics integration:**

.. code-block:: python

    # See: user_guide/case_studies.rst - Biological Network Case Study
    # 1. Integrate protein-protein + gene regulation + metabolic pathways
    # 2. Find key regulators using multilayer centrality
    # 3. Detect functional modules
    # 4. Prioritize disease genes

See :doc:`../user_guide/case_studies` for complete implementation.

Transportation Networks
~~~~~~~~~~~~~~~~~~~~~~~

**Multimodal route analysis:**

.. code-block:: python

    # See: examples/index.rst - Transportation Example
    # 1. Model different transportation modes as layers
    # 2. Add transfer connections between layers
    # 3. Compute optimal multimodal routes
    # 4. Identify critical transfer points

See :doc:`../examples/index` for runnable code.

Config-Driven Workflows
-----------------------

Use configuration files for reproducibility:

.. code-block:: yaml

    # workflow_config.yaml
    network:
      input_file: "data.multiedgelist"
      input_type: "multiedgelist"
    
    analysis:
      - name: "statistics"
        metrics: ["degree", "betweenness_centrality"]
      
      - name: "community_detection"
        algorithm: "louvain"
        params:
          resolution: 1.0
      
      - name: "visualization"
        output: "network.png"
        layout: "force_directed"

Execute workflow:

.. code-block:: python

    from py3plex.workflows import execute_workflow

    results = execute_workflow("workflow_config.yaml")

See :doc:`../user_guide/recipes_and_workflows` for complete config-driven workflow examples.

The config captures *what* to run (input format, metrics, algorithms, visualization) so you can reuse the same analysis across datasets by swapping only the file path.

DSL-Driven Analysis Workflows
------------------------------

**Goal:** Use py3plex's DSL to create reproducible, declarative analysis pipelines.

The DSL expresses analysis workflows as queries rather than imperative code, keeping them readable and reproducible. ``Q`` builds a query, ``L`` is a layer helper, and ``execute_query`` returns dictionaries keyed by ``(node_id, layer)`` tuples.

Basic DSL Workflow Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Template for DSL-first analysis:** Keep the pipeline linear—load, query, refine, export—so each step can be repeated with different parameters.

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import Q, L, execute_query
    
    # 1. Load network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "py3plex/datasets/_data/synthetic_multilayer.edges",
        input_type="multiedgelist"
    )
    
    # 2. Query and filter nodes with DSL
    high_degree_nodes = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .where(degree__gt=5)
         .order_by("betweenness_centrality", reverse=True)
         .execute(network)
    )  # dict keyed by (node_id, layer) -> metrics
    
    # 3. Extract subnetwork
    subgraph = network.core_network.subgraph(high_degree_nodes.keys())
    
    # 4. Analyze subnetwork
    print(f"High-degree subnetwork:")
    print(f"  Nodes: {len(high_degree_nodes)}")
    print(f"  Edges: {subgraph.number_of_edges()}")
    
    # 5. Export results
    import pandas as pd
    df = pd.DataFrame([
        {
            'node': node[0],
            'layer': node[1],
            'degree': data['degree'],
            'betweenness': data['betweenness_centrality']
        }
        for node, data in high_degree_nodes.items()
    ])
    df.to_csv('high_degree_analysis.csv', index=False)

**Expected output (synthetic_multilayer sample):**

.. code-block:: text

    High-degree subnetwork:
      Nodes: 25
      Edges: 89

Multilayer Exploration Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Systematic multilayer network analysis:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import Q, L
    import pandas as pd
    
    # Load network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "py3plex/datasets/_data/synthetic_multilayer.edges",
        input_type="multiedgelist"
    )
    
    print("MULTILAYER NETWORK EXPLORATION")
    print("=" * 70)
    
    # Step 1: Per-layer statistics
    print("\n1. Per-Layer Statistics:")
    layer_stats = []
    
    for layer in network.get_layers():
        # Query layer nodes
        layer_nodes = Q.nodes().from_layers(L[layer]).execute(network)
        layer_edges = Q.edges().from_layers(L[layer]).execute(network)
        
        # Compute metrics
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree")
             .execute(network)
        )
        
        avg_degree = sum(d['degree'] for d in result.values()) / len(result) if result else 0
        
        layer_stats.append({
            'layer': layer,
            'nodes': len(layer_nodes),
            'edges': len(layer_edges),
            'avg_degree': avg_degree
        })
        
        print(f"  {layer}: {len(layer_nodes)} nodes, {len(layer_edges)} edges, avg_degree={avg_degree:.2f}")
    
    # Step 2: Find versatile nodes (present in multiple layers)
    print("\n2. Versatile Nodes (multilayer presence):")
    from collections import Counter
    
    node_layer_count = Counter()
    for node, layer in network.get_nodes():
        node_layer_count[node] += 1
    
    versatile_nodes = {
        node: count for node, count in node_layer_count.items()
        if count >= 2
    }
    
    print(f"  Total versatile nodes: {len(versatile_nodes)}")
    print(f"  Top 5 most versatile:")
    for node, count in sorted(versatile_nodes.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"    {node}: {count} layers")
    
    # Step 3: Layer comparison
    print("\n3. Layer Overlap Analysis:")
    layers = network.get_layers()
    
    for i, layer1 in enumerate(layers):
        for layer2 in layers[i+1:]:
            nodes1 = set(n[0] for n in Q.nodes().from_layers(L[layer1]).execute(network).keys())
            nodes2 = set(n[0] for n in Q.nodes().from_layers(L[layer2]).execute(network).keys())
            
            overlap = nodes1 & nodes2
            jaccard = len(overlap) / len(nodes1 | nodes2) if (nodes1 | nodes2) else 0
            
            print(f"  {layer1} ∩ {layer2}: {len(overlap)} nodes, Jaccard={jaccard:.3f}")
    
    # Step 4: Hub identification across layers
    print("\n4. Cross-Layer Hub Nodes:")
    all_metrics = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .where(degree__gt=7)
         .execute(network)
    )
    
    print(f"  Hub nodes (degree > 7): {len(all_metrics)}")
    
    # Group hubs by base node ID
    from collections import defaultdict
    hub_layers = defaultdict(set)
    
    for (node, layer), data in all_metrics.items():
        hub_layers[node].add(layer)
    
    print(f"  Unique hub node IDs: {len(hub_layers)}")
    print(f"  Top 5 hub nodes:")
    for node, layers in sorted(hub_layers.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        print(f"    {node}: present in {len(layers)} layers - {list(layers)}")

**Expected output:**

.. code-block:: text

    MULTILAYER NETWORK EXPLORATION
    ======================================================================
    
    1. Per-Layer Statistics:
      layer1: 40 nodes, 95 edges, avg_degree=4.75
      layer2: 40 nodes, 87 edges, avg_degree=4.35
      layer3: 40 nodes, 102 edges, avg_degree=5.10
    
    2. Versatile Nodes (multilayer presence):
      Total versatile nodes: 35
      Top 5 most versatile:
        node7: 3 layers
        node12: 3 layers
        node3: 3 layers
        node15: 3 layers
        node1: 3 layers
    
    3. Layer Overlap Analysis:
      layer1 ∩ layer2: 35 nodes, Jaccard=0.875
      layer1 ∩ layer3: 32 nodes, Jaccard=0.800
      layer2 ∩ layer3: 33 nodes, Jaccard=0.825
    
    4. Cross-Layer Hub Nodes:
      Hub nodes (degree > 7): 18
      Unique hub node IDs: 12
      Top 5 hub nodes:
        node7: present in 3 layers - ['layer1', 'layer2', 'layer3']
        node12: present in 3 layers - ['layer1', 'layer2', 'layer3']
        node3: present in 3 layers - ['layer1', 'layer2', 'layer3']
        node15: present in 2 layers - ['layer1', 'layer3']
        node8: present in 2 layers - ['layer2', 'layer3']

The thresholds (degree > 7, overlap counts) match the bundled ``synthetic_multilayer`` dataset. Adjust them for sparser or denser graphs so averages and Jaccard scores remain meaningful.

Community Detection + DSL Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Combine community detection with DSL queries:**

.. code-block:: python

    from py3plex.algorithms.community_detection.community_wrapper import louvain_communities
    from py3plex.dsl import Q, execute_query
    from collections import Counter

    # Detect communities
    communities = louvain_communities(network)
    
    # Attach as node attributes
    for (node, layer), comm_id in communities.items():
        network.core_network.nodes[(node, layer)]['community'] = comm_id
    
    print("COMMUNITY-BASED ANALYSIS")
    print("=" * 70)
    
    # Query each community
    community_ids = set(communities.values())
    
    for comm_id in sorted(community_ids):
        # Use DSL to get community members
        comm_nodes = execute_query(
            network,
            f'SELECT nodes WHERE community={comm_id}'
        )
        members = comm_nodes.get("nodes", [])
        
        # Compute community metrics
        comm_result = (
            Q.nodes()
             .where(community=comm_id)
             .compute("degree", "betweenness_centrality")
             .execute(network)
        )
        
        # Statistics
        if comm_result:
            avg_degree = sum(d['degree'] for d in comm_result.values()) / len(comm_result)
            avg_betw = sum(d['betweenness_centrality'] for d in comm_result.values()) / len(comm_result)
        else:
            avg_degree = avg_betw = 0.0
        
        # Layer composition
        layer_counts = Counter(layer for _, layer in members)
        
        print(f"\nCommunity {comm_id}:")
        print(f"  Size: {len(members)} nodes")
        print(f"  Avg degree: {avg_degree:.2f}")
        print(f"  Avg betweenness: {avg_betw:.6f}")
        print(f"  Layer composition: {dict(layer_counts)}")

**Notes:** ``execute_query`` returns a dictionary; access community members via ``result["nodes"]`` as shown. If a community has no nodes (rare with Louvain), averages safely fall back to ``0.0``. Community labels live on the NetworkX backing graph (``network.core_network``), so they persist across subsequent DSL queries.

Dynamics + DSL Workflow
~~~~~~~~~~~~~~~~~~~~~~~~

**Epidemic simulation with DSL-based analysis:**

.. code-block:: python

    from py3plex.dynamics import SIRDynamics
    from py3plex.dsl import Q, L
    from collections import Counter
    
    # Run SIR simulation
    sir = SIRDynamics(
        network,
        beta=0.3,
        gamma=0.1,
        initial_infected=0.05
    )
    sir.set_seed(42)
    results = sir.run(steps=100)
    
    # Attach final state
    final_state = results.trajectory[-1]
    for node, state in final_state.items():
        network.core_network.nodes[node]['sir_state'] = state
    
    print("EPIDEMIC ANALYSIS")
    print("=" * 70)
    
    # Per-layer infection analysis
    for layer in network.get_layers():
        layer_nodes = Q.nodes().from_layers(L[layer]).execute(network)
        
        state_counts = Counter(
            network.core_network.nodes[node].get('sir_state', 'unknown')
            for node in layer_nodes.keys()
        )
        
        total = len(layer_nodes)
        
        def pct(count):
            return count / total * 100 if total else 0
        
        print(f"\n{layer}:")
        print(f"  S: {state_counts.get('S', 0)} ({pct(state_counts.get('S', 0)):.1f}%)")
        print(f"  I: {state_counts.get('I', 0)} ({pct(state_counts.get('I', 0)):.1f}%)")
        print(f"  R: {state_counts.get('R', 0)} ({pct(state_counts.get('R', 0)):.1f}%)")
    
    # Identify superspreaders (infected nodes with high degree)
    superspreaders = (
        Q.nodes()
         .where(sir_state='I')
         .compute("degree", "betweenness_centrality")
         .where(degree__gt=6)
         .order_by("degree", reverse=True)
         .execute(network)
    )
    
    print(f"\nSuperspreaders (infected, degree > 6): {len(superspreaders)}")
    for node, data in list(superspreaders.items())[:5]:
        print(f"  {node}: degree={data['degree']}, betw={data['betweenness_centrality']:.4f}")

**Notes:** The SIR outcomes depend on ``beta`` (infection rate), ``gamma`` (recovery rate), and the random seed. Percentages are guarded against empty layers so the snippet can be reused on sparse networks, and ``sir_state`` is stored per node as ``S``, ``I``, or ``R`` for follow-up filtering.

Reusable DSL Query Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Create reusable query templates:**

.. code-block:: python

    def get_layer_hubs(network, layer, degree_threshold=5):
        """Get high-degree nodes in a specific layer."""
        from py3plex.dsl import Q, L
        
        return (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree")
             .where(degree__gt=degree_threshold)
             .order_by("degree", reverse=True)
             .execute(network)
        )
    
    def get_versatile_nodes(network, min_layers=2):
        """Get nodes present in multiple layers."""
        from collections import Counter
        
        node_layer_count = Counter()
        for node, layer in network.get_nodes():
            node_layer_count[node] += 1
        
        return {
            node: count for node, count in node_layer_count.items()
            if count >= min_layers
        }
    
    def compare_layer_centrality(network, layer1, layer2):
        """Compare centrality distributions between two layers."""
        from py3plex.dsl import Q, L
        import numpy as np
        
        result1 = (
            Q.nodes()
             .from_layers(L[layer1])
             .compute("betweenness_centrality")
             .execute(network)
        )
        
        result2 = (
            Q.nodes()
             .from_layers(L[layer2])
             .compute("betweenness_centrality")
             .execute(network)
        )
        
        betw1 = [d['betweenness_centrality'] for d in result1.values()]
        betw2 = [d['betweenness_centrality'] for d in result2.values()]
        
        return {
            'layer1': {'mean': np.mean(betw1), 'std': np.std(betw1)},
            'layer2': {'mean': np.mean(betw2), 'std': np.std(betw2)}
        }
    
    # Use reusable functions
    hubs_layer1 = get_layer_hubs(network, 'layer1', degree_threshold=7)
    versatile = get_versatile_nodes(network, min_layers=3)
    centrality_comp = compare_layer_centrality(network, 'layer1', 'layer2')
    
    print(f"Layer1 hubs: {len(hubs_layer1)}")
    print(f"Highly versatile nodes: {len(versatile)}")
    print(f"Centrality comparison: {centrality_comp}")

**Why use DSL-driven workflows?**

* **Declarative:** Express *what* to analyze, not *how* to compute
* **Composable:** Chain queries to build complex analyses
* **Reproducible:** Queries are self-documenting and version-controllable
* **Efficient:** DSL optimizes execution internally
* **Readable:** SQL-like syntax is intuitive for data analysis

**Next steps with DSL workflows:**

* **Full DSL tutorial:** :doc:`query_with_dsl` - Comprehensive DSL guide
* **Community detection:** :doc:`run_community_detection` - Community + DSL workflows
* **Dynamics simulation:** :doc:`simulate_dynamics` - Dynamics + DSL workflows

Batch Processing
----------------

Process multiple networks:

.. code-block:: python

    import glob
    from py3plex.core import multinet
    
    results = []
    
    for filename in glob.glob("data/*.multiedgelist"):
        # Load network
        network = multinet.multi_layer_network()
        network.load_network(filename, input_type="multiedgelist")
        
        # Apply analysis pipeline
        stats = analyze_network(network)  # Your custom function
        
        results.append({
            'filename': filename,
            'stats': stats
        })
    
    # Aggregate results
    summary = aggregate_results(results)

``analyze_network`` and ``aggregate_results`` are placeholders for your own reusable pipeline (e.g., computing summary stats, exporting community labels). Keep them pure functions so the batch loop stays predictable.

Complete Example Templates
---------------------------

The following locations contain complete, runnable examples:

1. **User Guide Recipes** (:doc:`../user_guide/recipes_and_workflows`)
   
   * Recipe-style solutions with code + explanation
   * Focused on single tasks

2. **Case Studies** (:doc:`../user_guide/case_studies`)
   
   * End-to-end analyses
   * Real-world datasets
   * Publication-ready results

3. **Examples Gallery** (:doc:`../examples/index`)
   
   * Standalone Python scripts
   * Minimal, focused examples
   * Easy to adapt

Next Steps
----------

* **Learn fundamentals:** :doc:`../getting_started/tutorial_10min`
* **Detailed recipes:** :doc:`../user_guide/recipes_and_workflows`
* **Complete case studies:** :doc:`../user_guide/case_studies`
* **Browse examples:** :doc:`../examples/index`
