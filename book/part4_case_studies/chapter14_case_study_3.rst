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
    # ...

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
    # ...

Temporal Dynamics
~~~~~~~~~~~~~~~~~

Analyze how network properties change throughout the day:

.. code-block:: python

    # Load time-stamped network
    # for time_window in time_windows:
    #     network_t = load_network_for_time(time_window)
    #     stats = compute_stats(network_t)
    #     temporal_stats.append(stats)

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
* ``examples/network_analysis/`` for DSL patterns
