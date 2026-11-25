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

    name: "Reproducible network statistics"
    datasets:
      - name: "sample"
        type: "generate"
        generator: "random"
        parameters:
          nodes: 12
          layers: 2
          probability: 0.3
          seed: 42
    operations:
      - type: "stats"
        dataset: "sample"

Save the YAML as ``workflow_config.yaml`` and install the
``py3plex[workflows]`` extra for YAML support.

.. code-block:: python

    from py3plex.workflows import WorkflowConfig, WorkflowRunner

    runner = WorkflowRunner(WorkflowConfig.from_file("workflow_config.yaml"))
    runner.run()
    print(runner.results["sample_stats_0"])

See :doc:`../user_guide/recipes_and_workflows` for complete config-driven workflow examples.

A workflow can load datasets from files or generate them with a seed. Operations name the dataset they use.

DSL-Driven Analysis Workflows
------------------------------

**Goal:** Use py3plex's DSL to create reproducible, declarative analysis pipelines.

The DSL expresses analysis workflows as queries rather than imperative code, keeping them readable and reproducible. ``Q`` builds a query, ``L`` is a layer helper. Use the Builder API (``Q.nodes()``) for production code with type hints, or the legacy string DSL (``execute_query()``) for backward compatibility.

Basic DSL Workflow Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Template for DSL-first analysis:** Keep the pipeline linear—load, query, refine, export—so each step can be repeated with different parameters.

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import Q, L
    
    # 1. Load network
    from py3plex.datasets import load_synthetic_multilayer

    network = load_synthetic_multilayer()
    
    # 2. Query and filter nodes with DSL
    high_degree_nodes = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .where(degree__gt=5)
         .order_by("betweenness_centrality", desc=True)
         .execute(network)
    )  # QueryResult with one item per node replica
    
    # 3. Extract subnetwork
    subgraph = high_degree_nodes.to_networkx(network)
    
    # 4. Analyze subnetwork
    print(f"High-degree subnetwork:")
    print(f"  Nodes: {len(high_degree_nodes)}")
    print(f"  Edges: {subgraph.number_of_edges()}")
    
    # 5. Export results
    high_degree_nodes.to_pandas().to_csv("high_degree_analysis.csv", index=False)

Multilayer Exploration Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Systematic multilayer network analysis:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import Q, L
    import pandas as pd
    
    # Load network
    from py3plex.datasets import load_synthetic_multilayer

    network = load_synthetic_multilayer()
    
    print("MULTILAYER NETWORK EXPLORATION")
    print("=" * 70)
    
    # Step 1: Per-layer statistics
    print("\n1. Per-Layer Statistics:")
    layer_stats = []
    
    for layer in network.layers:
        # Query layer nodes
        layer_nodes = Q.nodes().from_layers(L[layer]).execute(network)
        layer_edges = Q.edges().from_layers(L[layer]).execute(network)
        
        # Compute metrics
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree", kind="intra")
             .execute(network)
        )
        
        avg_degree = result.to_pandas()['degree'].mean() if result.count else 0
        
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
    layers = network.layers
    
    for i, layer1 in enumerate(layers):
        for layer2 in layers[i+1:]:
            nodes1 = set(n[0] for n in Q.nodes().from_layers(L[layer1]).execute(network).items)
            nodes2 = set(n[0] for n in Q.nodes().from_layers(L[layer2]).execute(network).items)
            
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
    
    for node, layer in all_metrics.items:
        hub_layers[node].add(layer)
    
    print(f"  Unique hub node IDs: {len(hub_layers)}")
    print(f"  Top 5 hub nodes:")
    for node, layers in sorted(hub_layers.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        print(f"    {node}: present in {len(layers)} layers - {list(layers)}")

Adjust the degree threshold to suit your network. The comparison reports
Jaccard overlap over physical node IDs, while the hub query starts from
node replicas.

Community Detection + DSL Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Combine community detection with DSL queries:**

.. code-block:: python

    from py3plex.algorithms.community_detection.community_wrapper import louvain_communities
    from py3plex.dsl import Q
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
        # Use DSL Builder API to get community members and compute metrics
        comm_result = (
            Q.nodes()
             .where(community=comm_id)
             .compute("degree", "betweenness_centrality")
             .execute(network)
        )
        
        members = comm_result.items  # Get node-layer tuples
        
        # Statistics
        if comm_result.count > 0:
            df = comm_result.to_pandas()
            avg_degree = df['degree'].mean()
            avg_betw = df['betweenness_centrality'].mean()
        else:
            avg_degree = avg_betw = 0.0
        
        # Layer composition
        layer_counts = Counter(layer for _, layer in members)
        
        print(f"\nCommunity {comm_id}:")
        print(f"  Size: {len(members)} nodes")
        print(f"  Avg degree: {avg_degree:.2f}")
        print(f"  Avg betweenness: {avg_betw:.6f}")
        print(f"  Layer composition: {dict(layer_counts)}")

**Notes:** The Builder API (``Q.nodes()``) provides ``result.items`` for node-layer tuples, ``result.count`` for the count, and ``.to_pandas()`` for DataFrame conversion. If a community has no nodes (rare with Louvain), averages safely fall back to ``0.0``. Community labels live on the NetworkX backing graph (``network.core_network``), so they persist across subsequent DSL queries.

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
    for layer in network.layers:
        layer_nodes = Q.nodes().from_layers(L[layer]).execute(network)
        
        state_counts = Counter(
            network.core_network.nodes[node].get('sir_state', 'unknown')
            for node in layer_nodes.items
        )
        
        total = len(layer_nodes)
        
        def pct(count):
            return count / total * 100 if total else 0
        
        print(f"\n{layer}:")
        print(f"  S: {state_counts.get('S', 0)} ({pct(state_counts.get('S', 0)):.1f}%)")
        print(f"  I: {state_counts.get('I', 0)} ({pct(state_counts.get('I', 0)):.1f}%)")
        print(f"  R: {state_counts.get('R', 0)} ({pct(state_counts.get('R', 0)):.1f}%)")
    
    # Find high-degree infected replicas at the final step
    infected_hubs = (
        Q.nodes()
         .where(sir_state='I')
         .compute("degree", "betweenness_centrality")
         .where(degree__gt=6)
         .order_by("degree", desc=True)
         .execute(network)
    )
    
    print(f"\nInfected replicas with degree > 6: {len(infected_hubs)}")
    print(infected_hubs.to_pandas().head(5))

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
             .order_by("degree", desc=True)
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
             .per_layer()
             .compute("betweenness_centrality")
             .execute(network)
        )
        
        result2 = (
            Q.nodes()
             .from_layers(L[layer2])
             .per_layer()
             .compute("betweenness_centrality")
             .execute(network)
        )
        
        betw1 = result1.to_pandas()["betweenness_centrality"]
        betw2 = result2.to_pandas()["betweenness_centrality"]
        
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

    from pathlib import Path

    import pandas as pd
    from py3plex.core import multinet

    records = []
    for filename in sorted(Path("data").glob("*.multiedgelist")):
        batch_network = multinet.multi_layer_network(directed=False)
        batch_network.load_network(str(filename), input_type="multiedgelist")
        records.append({
            "filename": str(filename),
            "replicas": sum(1 for _ in batch_network.get_nodes()),
            "edges": sum(1 for _ in batch_network.get_edges()),
            "layers": batch_network.layer_count,
        })

    summary = pd.DataFrame(records, columns=["filename", "replicas", "edges", "layers"])
    print(summary)

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
