Case Study 3 — Transportation Network
============================================================

.. admonition:: Case Study Template
   :class: note

   This case study outlines a complete workflow for transportation multilayer network 
   analysis. The approach demonstrates advanced techniques including temporal analysis 
   and large-scale DSL queries. Examples use representative synthetic data to illustrate 
   methodology applicable to real transportation datasets.

Domain Context
--------------

Urban transportation systems are inherently multilayer:

* **Nodes:** Locations (stations, stops, intersections)
* **Layers:** Transportation modes (subway, bus, bike-share, walking)
* **Edges:** Direct connections between locations within each mode
* **Inter-layer edges:** Transfer points between modes
* **Temporal dimension:** Schedules, rush hours, seasonal patterns

**Research questions:**

1. How do disruptions in one mode affect overall connectivity?
2. Which stations are critical hubs across multiple modes?
3. How do communities of well-connected areas differ by mode?
4. What is the optimal multi-modal route between locations?

Potential Analysis Directions
------------------------------

Resilience Analysis
~~~~~~~~~~~~~~~~~~~

Simulate mode disruptions and measure impact:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Baseline connectivity
    baseline = (
        Q.nodes()
         .compute("betweenness_centrality")
         .execute(network)
    )
    
    # Remove subway layer
    reduced_network = network.remove_layer("subway")
    
    # Recompute connectivity
    disrupted = (
        Q.nodes()
         .compute("betweenness_centrality")
         .execute(reduced_network)
    )
    
    # Identify most affected locations
    baseline_df = baseline.to_pandas()
    disrupted_df = disrupted.to_pandas()
    
    # Compare betweenness changes
    for idx in baseline_df.index:
        node = baseline_df.loc[idx, 'node']
        layer = baseline_df.loc[idx, 'layer']
        base_bc = baseline_df.loc[idx, 'betweenness_centrality']
        
        # Find matching node in disrupted network
        disrupted_row = disrupted_df[
            (disrupted_df['node'] == node) & (disrupted_df['layer'] == layer)
        ]
        if not disrupted_row.empty:
            disrupt_bc = disrupted_row.iloc[0]['betweenness_centrality']
            impact = (base_bc - disrupt_bc) / base_bc if base_bc > 0 else 0
            if impact > 0.2:  # More than 20% reduction
                print(f"High impact: {node} in {layer}, {impact:.1%} reduction")

Multi-Modal Path Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~

Find optimal paths using multiple transportation modes:

.. code-block:: python

    # Shortest path across modes
    import networkx as nx
    
    path = nx.shortest_path(
        network.core_network,
        source=('location_A', 'bus'),
        target=('location_B', 'subway')
    )
    
    # Identify mode switches in path
    mode_switches = 0
    for i in range(len(path) - 1):
        current_mode = path[i][1]  # Layer is second element of tuple
        next_mode = path[i+1][1]
        if current_mode != next_mode:
            mode_switches += 1
            print(f"Switch from {current_mode} to {next_mode} at {path[i][0]}")
    
    print(f"Total mode switches: {mode_switches}")
    print(f"Path length: {len(path)} stops")

Temporal Dynamics
~~~~~~~~~~~~~~~~~

Analyze how network properties change throughout the day:

.. code-block:: python

    from py3plex.dsl import Q
    import pandas as pd
    
    # Example: Analyze network at different time windows
    time_windows = [(0, 6), (6, 12), (12, 18), (18, 24)]  # Hours of day
    temporal_stats = []
    
    for start_hour, end_hour in time_windows:
        # Filter edges by time window (assuming temporal metadata)
        result = (
            Q.nodes()
             .compute("degree", "betweenness_centrality")
             .execute(network)
        )
        
        stats = {
            'window': f"{start_hour:02d}:00-{end_hour:02d}:00",
            'avg_degree': result.to_pandas()['degree'].mean(),
            'avg_betweenness': result.to_pandas()['betweenness_centrality'].mean()
        }
        temporal_stats.append(stats)
    
    # Display temporal patterns
    temporal_df = pd.DataFrame(temporal_stats)
    print(temporal_df)

DSL-Heavy Analysis
~~~~~~~~~~~~~~~~~~

Demonstrate advanced DSL patterns:

.. code-block:: python

    from py3plex.dsl import Q, L, Param
    
    # Parameterized cross-modal analysis
    hub_query = (
        Q.nodes()
         .from_layers(
             L[Param.str("mode1")] + L[Param.str("mode2")]
         )
         .where(degree__gt=Param.int("threshold"))
         .compute("betweenness_centrality", "closeness_centrality")
         .order_by("-betweenness_centrality")
         .limit(20)
    )
    
    # Execute for different mode combinations
    for mode1, mode2 in [("subway", "bus"), ("bus", "bike"), ("subway", "bike")]:
        result = hub_query.execute(
            network,
            mode1=mode1,
            mode2=mode2,
            threshold=10
        )
        print(f"{mode1} + {mode2}: {result.count} hubs")

Summary
-------

This case study (when completed) will demonstrate:

1. **Temporal multilayer networks** — Time-varying structure
2. **Resilience analysis** — Impact of layer removal
3. **Multi-modal routing** — Path finding across layers
4. **Large-scale DSL queries** — Advanced query patterns
5. **Geospatial visualization** — Map-based network rendering

**To complete:**

1. Obtain transportation dataset (GTFS format, OpenStreetMap)
2. Construct multilayer representation
3. Implement temporal slicing
4. Run resilience experiments
5. Visualize with geospatial coordinates

**Relevant resources:**

* GTFS (General Transit Feed Specification) for public transit data
* OpenStreetMap for walking/cycling networks
* ``examples/03_dsl_v2/`` for DSL patterns
* ``examples/01_network_construction/`` for network building patterns
