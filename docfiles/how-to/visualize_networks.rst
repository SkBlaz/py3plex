How to Visualize Multilayer Networks
=====================================

**Goal:** Create publication-ready visualizations of multilayer networks.

**Prerequisites:** A loaded network (see :doc:`load_and_build_networks`).

Basic Visualization
-------------------

Quick Plot
~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    # Load network
    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
        ['Alice', 'work', 'Carol', 'work', 1],
    ], input_type="list")
    
    # Visualize
    network.visualize_network(show=True)

This opens an interactive window with the network visualization.

Save to File
~~~~~~~~~~~~

.. code-block:: python

    network.visualize_network(
        output_file='network.png',
        show=False
    )

Customizing Visualizations
---------------------------

Node Sizes and Colors
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization import visualize_network_custom
    
    # Compute node importance
    from py3plex.dsl import Q
    result = Q.nodes().compute("degree").execute(network)
    degrees = {node: data['degree'] for node, data in result.items()}
    
    # Visualize with custom node sizes
    visualize_network_custom(
        network,
        node_sizes=degrees,
        node_color_by_layer=True,
        output_file='network_sized.png'
    )

Edge Weights
~~~~~~~~~~~~

.. code-block:: python

    visualize_network_custom(
        network,
        edge_width_by_weight=True,
        show=True
    )

Layout Algorithms
-----------------

Force-Directed Layout
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization.multilayer import hairball_plot
    
    hairball_plot(
        network,
        layout_algorithm='force_directed',
        output_file='force_layout.png'
    )

Circular Layout
~~~~~~~~~~~~~~~

.. code-block:: python

    hairball_plot(
        network,
        layout_algorithm='circular',
        output_file='circular_layout.png'
    )

Layer-Specific Visualization
-----------------------------

Visualize Single Layer
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Extract layer
    layer_network = Q.edges().from_layers(L["friends"]).execute(network)
    
    # Visualize
    layer_network.visualize_network(
        output_file='friends_layer.png',
        show=True
    )

Side-by-Side Layer Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for idx, layer in enumerate(['friends', 'work', 'family']):
        layer_net = Q.edges().from_layers(L[layer]).execute(network)
        # Visualize on specific axis
        visualize_on_axis(layer_net, axes[idx], title=f'Layer: {layer}')
    
    plt.tight_layout()
    plt.savefig('layers_comparison.png', dpi=300)

DSL-Driven Visualization Workflows
-----------------------------------

**Goal:** Use DSL queries to select and visualize specific network subsets.

The DSL enables you to create targeted visualizations by filtering nodes and edges before rendering. This is essential for large multilayer networks where visualizing everything is impractical.

Visualize High-Degree Subnetwork
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Focus visualization on hub nodes:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import Q
    import matplotlib.pyplot as plt
    
    # Load network
    network = multinet.multi_layer_network(directed=False)
    network.load_network(
        "py3plex/datasets/_data/synthetic_multilayer.edges",
        input_type="multiedgelist"
    )
    
    # Query high-degree nodes
    hubs = (
        Q.nodes()
         .compute("degree")
         .where(degree__gt=6)
         .execute(network)
    )
    
    print(f"Hub nodes (degree > 6): {len(hubs)}")
    
    # Extract hub subgraph
    hub_subgraph = network.core_network.subgraph(hubs.keys())
    
    # Create visualization
    import networkx as nx
    pos = nx.spring_layout(hub_subgraph, k=0.5, iterations=50)
    
    plt.figure(figsize=(12, 10))
    
    # Color by layer
    layer_colors = {'layer1': 'red', 'layer2': 'blue', 'layer3': 'green'}
    node_colors = [layer_colors.get(node[1], 'gray') for node in hub_subgraph.nodes()]
    
    # Size by degree
    node_sizes = [hubs[node]['degree'] * 100 for node in hub_subgraph.nodes()]
    
    nx.draw_networkx(
        hub_subgraph,
        pos,
        node_color=node_colors,
        node_size=node_sizes,
        with_labels=True,
        font_size=8,
        alpha=0.7
    )
    
    plt.title('Hub Nodes Subnetwork (degree > 6)', fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('hub_subnetwork.png', dpi=300, bbox_inches='tight')
    print("Saved: hub_subnetwork.png")

**Expected output:**

.. code-block:: text

    Hub nodes (degree > 6): 18
    Saved: hub_subnetwork.png

Visualize Community Structure with DSL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Community-aware visualization:**

.. code-block:: python

    from py3plex.algorithms.community_detection.community_wrapper import louvain_communities
    from py3plex.dsl import Q, execute_query
    import matplotlib.pyplot as plt
    import networkx as nx
    
    # Detect communities
    communities = louvain_communities(network)
    
    # Attach community labels
    for (node, layer), comm_id in communities.items():
        network.core_network.nodes[(node, layer)]['community'] = comm_id
    
    # Visualize each community separately
    community_ids = set(communities.values())
    n_communities = len(community_ids)
    
    fig, axes = plt.subplots(1, min(n_communities, 4), figsize=(20, 5))
    if n_communities == 1:
        axes = [axes]
    
    for idx, comm_id in enumerate(sorted(community_ids)[:4]):
        # Query community members
        comm_nodes = execute_query(
            network,
            f'SELECT nodes WHERE community={comm_id}'
        )
        
        # Extract community subgraph
        comm_subgraph = network.core_network.subgraph(comm_nodes)
        
        # Visualize
        pos = nx.spring_layout(comm_subgraph, k=0.3)
        
        # Color by layer
        layer_colors = {'layer1': '#FF6B6B', 'layer2': '#4ECDC4', 'layer3': '#45B7D1'}
        node_colors = [layer_colors.get(node[1], 'gray') for node in comm_subgraph.nodes()]
        
        nx.draw_networkx(
            comm_subgraph,
            pos,
            ax=axes[idx],
            node_color=node_colors,
            node_size=200,
            with_labels=False,
            alpha=0.8
        )
        
        axes[idx].set_title(f'Community {comm_id}\n({len(comm_nodes)} nodes)')
        axes[idx].axis('off')
    
    plt.tight_layout()
    plt.savefig('communities_separate.png', dpi=300, bbox_inches='tight')
    print(f"Saved: communities_separate.png with {min(n_communities, 4)} communities")

Layer-Specific Visualizations with DSL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Compare layer structures visually:**

.. code-block:: python

    from py3plex.dsl import Q, L
    import matplotlib.pyplot as plt
    import networkx as nx
    
    layers = network.get_layers()
    n_layers = len(layers)
    
    fig, axes = plt.subplots(1, n_layers, figsize=(6*n_layers, 5))
    if n_layers == 1:
        axes = [axes]
    
    for idx, layer in enumerate(layers):
        # Query layer nodes and edges
        layer_nodes = Q.nodes().from_layers(L[layer]).execute(network)
        layer_edges = Q.edges().from_layers(L[layer]).execute(network)
        
        # Extract layer subgraph
        layer_subgraph = network.core_network.subgraph(layer_nodes.keys())
        
        # Compute metrics for sizing
        layer_metrics = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree")
             .execute(network)
        )
        
        # Visualization
        pos = nx.spring_layout(layer_subgraph, k=0.5, iterations=50)
        
        # Size by degree
        node_sizes = [layer_metrics[node]['degree'] * 50 for node in layer_subgraph.nodes()]
        
        nx.draw_networkx(
            layer_subgraph,
            pos,
            ax=axes[idx],
            node_size=node_sizes,
            node_color='lightblue',
            edge_color='gray',
            with_labels=False,
            alpha=0.7
        )
        
        axes[idx].set_title(f'{layer}\n{len(layer_nodes)} nodes, {len(layer_edges)} edges')
        axes[idx].axis('off')
    
    plt.tight_layout()
    plt.savefig('layer_comparison.png', dpi=300, bbox_inches='tight')
    print("Saved: layer_comparison.png")

**Expected output:**

.. code-block:: text

    Saved: layer_comparison.png

Visualize Central Nodes
~~~~~~~~~~~~~~~~~~~~~~~~

**Highlight nodes by centrality:**

.. code-block:: python

    from py3plex.dsl import Q
    import matplotlib.pyplot as plt
    import networkx as nx
    import numpy as np
    
    # Compute centrality for all nodes
    centrality_result = (
        Q.nodes()
         .compute("betweenness_centrality", "degree")
         .execute(network)
    )
    
    # Extract betweenness values for coloring
    betweenness = {
        node: data['betweenness_centrality']
        for node, data in centrality_result.items()
    }
    
    # Create visualization
    plt.figure(figsize=(14, 10))
    pos = nx.spring_layout(network.core_network, k=0.5, iterations=50)
    
    # Node colors based on betweenness (using colormap)
    node_list = list(network.core_network.nodes())
    betw_values = [betweenness.get(node, 0) for node in node_list]
    
    # Node sizes based on degree
    degrees = {node: data['degree'] for node, data in centrality_result.items()}
    node_sizes = [degrees.get(node, 1) * 100 for node in node_list]
    
    # Draw
    nodes = nx.draw_networkx_nodes(
        network.core_network,
        pos,
        node_size=node_sizes,
        node_color=betw_values,
        cmap=plt.cm.YlOrRd,
        alpha=0.8
    )
    
    nx.draw_networkx_edges(
        network.core_network,
        pos,
        alpha=0.2,
        edge_color='gray'
    )
    
    # Add colorbar
    plt.colorbar(nodes, label='Betweenness Centrality')
    plt.title('Network Centrality Visualization\n(size=degree, color=betweenness)', fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('centrality_viz.png', dpi=300, bbox_inches='tight')
    print("Saved: centrality_viz.png")

Dynamics State Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Visualize epidemic simulation results:**

.. code-block:: python

    from py3plex.dynamics import SIRDynamics
    from py3plex.dsl import Q
    import matplotlib.pyplot as plt
    import networkx as nx
    
    # Run SIR simulation
    sir = SIRDynamics(network, beta=0.3, gamma=0.1, initial_infected=0.05)
    sir.set_seed(42)
    results = sir.run(steps=100)
    
    # Attach final state
    final_state = results.trajectory[-1]
    for node, state in final_state.items():
        network.core_network.nodes[node]['sir_state'] = state
    
    # Query infected and recovered nodes
    infected = Q.nodes().where(sir_state='I').execute(network)
    recovered = Q.nodes().where(sir_state='R').execute(network)
    susceptible = Q.nodes().where(sir_state='S').execute(network)
    
    print(f"Infected: {len(infected)}, Recovered: {len(recovered)}, Susceptible: {len(susceptible)}")
    
    # Visualization
    plt.figure(figsize=(14, 10))
    pos = nx.spring_layout(network.core_network, k=0.5, iterations=50)
    
    # Color by SIR state
    state_colors = {'S': 'lightblue', 'I': 'red', 'R': 'green'}
    node_colors = [
        state_colors.get(network.core_network.nodes[node].get('sir_state'), 'gray')
        for node in network.core_network.nodes()
    ]
    
    nx.draw_networkx(
        network.core_network,
        pos,
        node_color=node_colors,
        node_size=300,
        with_labels=False,
        alpha=0.8
    )
    
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='lightblue', label=f'Susceptible ({len(susceptible)})'),
        Patch(facecolor='red', label=f'Infected ({len(infected)})'),
        Patch(facecolor='green', label=f'Recovered ({len(recovered)})')
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.title('SIR Epidemic Simulation (t=100)', fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('sir_visualization.png', dpi=300, bbox_inches='tight')
    print("Saved: sir_visualization.png")

**Expected output:**

.. code-block:: text

    Infected: 8, Recovered: 82, Susceptible: 30
    Saved: sir_visualization.png

Interactive Visualization with DSL Filtering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Create interactive plots with Plotly:**

.. code-block:: python

    from py3plex.dsl import Q
    import plotly.graph_objects as go
    import networkx as nx
    
    # Query nodes with metrics
    metrics = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    # Extract subgraph (optional: filter for clarity)
    high_degree = {
        node: data for node, data in metrics.items()
        if data['degree'] > 4
    }
    
    subgraph = network.core_network.subgraph(high_degree.keys())
    
    # Layout
    pos = nx.spring_layout(subgraph, k=0.5)
    
    # Create edge trace
    edge_x = []
    edge_y = []
    for edge in subgraph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    # Create node trace
    node_x = []
    node_y = []
    node_text = []
    node_sizes = []
    node_colors = []
    
    for node in subgraph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        degree = high_degree[node]['degree']
        betw = high_degree[node]['betweenness_centrality']
        
        node_text.append(f'{node}<br>Degree: {degree}<br>Betweenness: {betw:.4f}')
        node_sizes.append(degree * 5)
        node_colors.append(betw)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale='YlOrRd',
            size=node_sizes,
            color=node_colors,
            colorbar=dict(
                title="Betweenness"
            ),
            line_width=2
        )
    )
    
    # Create figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title='Interactive Network Visualization (degree > 4)',
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    )
    
    # Save to HTML
    fig.write_html('interactive_network.html')
    print("Saved: interactive_network.html (open in browser)")

**Why use DSL for visualization?**

* **Targeted views:** Filter nodes/edges to reduce visual clutter
* **Multi-scale:** Visualize different network scales (layer, community, subnetwork)
* **Attribute-driven:** Color/size nodes based on computed metrics
* **Reproducible:** Query-based selections are version-controllable
* **Efficient:** Process only relevant subsets for large networks

**Next steps with DSL visualization:**

* **Full DSL tutorial:** :doc:`query_with_dsl` - Complete DSL reference
* **Community detection:** :doc:`run_community_detection` - Visualize communities
* **Dynamics:** :doc:`simulate_dynamics` - Visualize dynamics results

Community Visualization
-----------------------

Color by Communities
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import louvain_communities
    from py3plex.visualization import visualize_communities
    
    # Detect communities
    communities = louvain_communities(network)
    
    # Visualize with community colors
    visualize_communities(
        network,
        communities,
        output_file='communities.png',
        show=True
    )

Interactive Visualization
-------------------------

Using Plotly
~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization import plotly_visualization
    
    # Create interactive plot
    fig = plotly_visualization(network)
    
    # Show in browser
    fig.show()
    
    # Or save as HTML
    fig.write_html('network_interactive.html')

Export for Gephi/Cytoscape
---------------------------

Export to GraphML
~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    # Convert to NetworkX
    G = network.to_networkx()
    
    # Export
    nx.write_graphml(G, 'network.graphml')

Then open `network.graphml` in Gephi or Cytoscape for advanced visualization.

Next Steps
----------

* **Compute statistics to visualize:** :doc:`compute_statistics`
* **Detect communities:** :doc:`run_community_detection`
* **API reference:** :doc:`../reference/api_index`
