.. _advanced-dsl-chapter:

Advanced Queries and Workflows
==========================================

This chapter covers advanced DSL patterns including dynamics simulation,
complex query patterns, and workflow integration.

DSL-Based Dynamics Simulation
------------------------------

The py3plex DSL includes a powerful framework for declarative dynamics
simulation on multilayer networks. This section demonstrates how to use
the dynamics DSL for epidemic modeling, random walks, and other dynamical
processes.

Mathematical Formalism
~~~~~~~~~~~~~~~~~~~~~~

**SIS Model (Susceptible-Infected-Susceptible)**

The SIS model tracks disease spread with possible reinfection:

* **States:** S (susceptible), I (infected)
* **Update rules** (discrete time, node i):
  
  * :math:`P(S_i \to I_i) = 1 - (1 - \beta)^{\sum_j A_{ij} I_j(t)}`
  * :math:`P(I_i \to S_i) = \gamma`

* **Parameters:**
  
  * :math:`\beta \in (0, 1)`: transmission probability per contact
  * :math:`\gamma \in (0, 1)`: recovery probability per time step (also denoted :math:`\mu`)

* **Epidemic threshold:**
  
  * :math:`R_0 = \frac{\beta}{\gamma} \lambda_{\max}(A)` where :math:`\lambda_{\max}(A)` is the largest eigenvalue of the adjacency matrix. Endemic equilibria exist when :math:`R_0 > 1`.

**SIR Model (Susceptible-Infected-Recovered)**

The SIR model includes permanent immunity after recovery:

* **States:** S (susceptible), I (infected), R (recovered/removed)
* **Update rules** (discrete time, node i):
  
  * :math:`P(S_i \to I_i) = 1 - (1 - \beta)^{\sum_j A_{ij} I_j(t)}`
  * :math:`P(I_i \to R_i) = \gamma`

* **Parameters:**
  
  * :math:`\beta \in (0, 1)`: transmission probability per contact
  * :math:`\gamma \in (0, 1)`: recovery probability per time step

The final outbreak size (attack rate) depends on the basic reproduction number :math:`R_0 = \frac{\beta}{\gamma} \langle k \rangle`, where :math:`\langle k \rangle` is the mean degree. Epidemic threshold at :math:`R_0 = 1`.

**Random Walk**

Random walk dynamics model diffusion processes:

* **State:** Current node position
* **Update rule:** Move to neighbor j with probability 1/degree(i), or stay
  at i with probability p_lazy (for lazy walks)
* **Parameters:**
  
  * p_teleport: probability of random teleportation (default: 0.05)
  * p_lazy: probability of staying at current node (default: 0.0)

Basic Dynamics DSL Usage
~~~~~~~~~~~~~~~~~~~~~~~~~

The dynamics DSL uses a builder API similar to the query DSL:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dynamics import D, SIS
    from py3plex.dsl import L

    # Create network
    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'social', 'Bob', 'social', 1],
        ['Bob', 'social', 'Carol', 'social', 1],
        ['Carol', 'social', 'Dave', 'social', 1],
    ], input_type="list")

    # Define SIS simulation
    sim = (
        D.process(SIS(beta=0.3, mu=0.1))  # Specify process and parameters
         .initial(infected=0.05)           # 5% initially infected
         .steps(100)                       # Run for 100 time steps
         .measure("prevalence", "incidence")  # Track measures
         .replicates(10)                   # Run 10 independent simulations
         .seed(42)                         # For reproducibility
    )

    # Execute simulation
    result = sim.run(network)

    # Access results
    print(f"Mean final prevalence: {result.data['prevalence'][:, -1].mean():.3f}")

    # Convert to pandas for analysis
    df_dict = result.to_pandas()
    prevalence_df = df_dict['prevalence']

**Key components:**

1. **D.process()** — Specify the dynamical process (SIS, SIR, RandomWalk)
2. **.initial()** — Set initial conditions
3. **.steps()** — Number of time steps to simulate
4. **.measure()** — Metrics to track during simulation
5. **.replicates()** — Number of independent runs (for averaging)
6. **.seed()** — Random seed for reproducibility
7. **.run()** — Execute the simulation

Initial Conditions
~~~~~~~~~~~~~~~~~~

The ``.initial()`` method accepts multiple formats for setting initial infected nodes:

**Float (fraction of nodes):**

.. code-block:: python

    .initial(infected=0.05)  # 5% of nodes randomly infected

**Integer (exact count):**

.. code-block:: python

    .initial(infected=5)  # Exactly 5 nodes randomly infected

**List of node tuples:**

.. code-block:: python

    .initial(infected=[('Alice', 'social'), ('Bob', 'work')])

**DSL query (dynamic selection):**

.. code-block:: python

    .initial(infected=Q.nodes().where(degree__gte=5))  # Infect high-degree hubs

**Recommended:** Use float fractions (0.05) for reproducibility across different network sizes.

Available Measures
~~~~~~~~~~~~~~~~~~

Different processes support different measures:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Process
     - Measure
     - Description
   * - SIS
     - prevalence
     - Fraction of infected nodes at each time step
   * - SIS
     - incidence
     - Number of new infections at each time step
   * - SIS
     - prevalence_by_layer
     - Prevalence tracked separately per layer
   * - SIR
     - prevalence
     - Fraction of infected nodes
   * - SIR
     - state_counts
     - Counts of nodes in each state (S, I, R)
   * - RandomWalk
     - visit_frequency
     - Frequency of visits to each node
   * - RandomWalk
     - state_counts
     - Current position over time

Multilayer Dynamics
~~~~~~~~~~~~~~~~~~~

The DSL supports multilayer networks with coupling between layers:

.. code-block:: python

    from py3plex.dsl import L

    # Simulate on specific layers
    sim = (
        D.process(SIS(beta=0.25, mu=0.08))
         .on_layers(L["offline"] + L["online"])  # Select layers
         .coupling(node_replicas="strong")       # Shared node states
         .initial(infected=0.1)
         .steps(120)
         .measure("prevalence", "prevalence_by_layer")
         .replicates(15)
    )

    result = sim.run(multilayer_network)

**Coupling modes:**

* **"strong"** — Node states shared across all layers (default)
* **"independent"** — Each layer has independent node states
* **"weak"** — Partial coupling with cross-layer transmission rate

Integration with Query DSL
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The dynamics DSL integrates seamlessly with the query DSL for targeted
initial conditions:

.. code-block:: python

    from py3plex.dsl import Q

    # Start infection at high-degree nodes (hubs)
    sim = (
        D.process(SIS(beta=0.35, mu=0.12))
         .initial(
             infected=Q.nodes().where(degree__gte=5)  # Query for hubs
         )
         .steps(100)
         .measure("prevalence")
         .replicates(10)
    )

    result = sim.run(network)

This allows precise control over initial conditions based on network
structure, centrality, or other properties.

Parameter Comparison Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compare dynamics under different parameters:

.. code-block:: python

    # Compare transmission rates
    beta_values = [0.2, 0.3, 0.4, 0.5]
    results = {}

    for beta in beta_values:
        sim = (
            D.process(SIS(beta=beta, mu=0.1))
             .initial(infected=0.05)
             .steps(80)
             .measure("prevalence")
             .replicates(20)
             .seed(42)
        )
        results[beta] = sim.run(network)

    # Analyze final prevalence
    for beta, result in results.items():
        mean_final = result.data['prevalence'][:, -1].mean()
        print(f"β={beta:.1f}: final prevalence = {mean_final:.3f}")

Result Analysis
~~~~~~~~~~~~~~~

The ``SimulationResult`` object provides rich analysis capabilities:

.. code-block:: python

    # Get summary statistics
    summary = result.summary()
    print(summary)

    # Plot time series with confidence intervals
    import matplotlib.pyplot as plt
    result.plot("prevalence")
    plt.show()

    # Export to pandas for custom analysis
    df_dict = result.to_pandas()
    prevalence_df = df_dict['prevalence']

    # Compute mean trajectory
    mean_trajectory = (
        prevalence_df
        .groupby('t')['value']
        .agg(['mean', 'std'])
    )

.. admonition:: Status: Dynamics DSL
   :class: note

   The builder API (``D.process()``) is under active development and may change in future releases. The core dynamics classes (``SIRDynamics``, ``SISDynamics``, ``RandomWalkDynamics``) are stable and production-ready.

Complex Query Patterns
-----------------------

Beyond basic filtering and computation, the DSL supports advanced analysis patterns.

Parameterized Comparative Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Systematic comparison across layers using parameterized queries:

.. code-block:: python

    from py3plex.dsl import Q, L, Param

    # Define reusable parameterized query
    hub_analysis = (
        Q.nodes()
         .from_layers(L[Param.str("layer")])
         .where(degree__gt=Param.int("threshold"))
         .compute("betweenness_centrality", "clustering")
         .order_by("-betweenness_centrality")
         .limit(Param.int("top_n"))
    )

    # Execute for multiple layers
    for layer in ["social", "work", "family"]:
        result = hub_analysis.execute(
            network,
            layer=layer,
            threshold=5,
            top_n=20
        )
        df = result.to_pandas()
        df.to_csv(f"{layer}_hubs.csv")
        print(f"{layer}: {result.count} hubs, max BC = {df['betweenness_centrality'].max():.3f}")

Multi-Layer Statistical Summaries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Aggregate statistics across all layers:

.. code-block:: python

    # Collect statistics for each layer
    layer_stats = []
    for layer_name in network.get_layers():
        result = (
            Q.nodes()
             .from_layers(L[layer_name])
             .compute("degree", "betweenness_centrality", "clustering")
             .execute(network)
        )
        df = result.to_pandas()
        
        layer_stats.append({
            'layer': layer_name,
            'node_count': result.count,
            'avg_degree': df['degree'].mean(),
            'max_betweenness': df['betweenness_centrality'].max(),
            'avg_clustering': df['clustering'].mean(),
        })
    
    # Convert to DataFrame for analysis
    import pandas as pd
    summary_df = pd.DataFrame(layer_stats)
    print(summary_df)

Layer Algebra for Complex Filters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Combine layers using set operations:

.. code-block:: python

    from py3plex.dsl import L
    
    # Nodes in social OR work layers
    social_or_work = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .compute("degree")
         .execute(network)
    )
    
    # Nodes in social BUT NOT bots
    legitimate_social = (
        Q.nodes()
         .from_layers(L["social"] - L["bots"])
         .compute("degree")
         .execute(network)
    )
    
    # Intersection of layers
    overlap = (
        Q.nodes()
         .from_layers(L["layer1"] & L["layer2"])
         .execute(network)
    )

Aggregations by Node Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Group and aggregate by node properties:

.. code-block:: python

    # Compute average centrality by community
    result = (
        Q.nodes()
         .compute("betweenness_centrality", "community")
         .execute(network)
    )
    
    df = result.to_pandas()
    community_centrality = df.groupby('community')['betweenness_centrality'].agg(['mean', 'std', 'max'])
    print(community_centrality)

Result Conversion
-----------------

The DSL provides flexible export capabilities for different analysis workflows.

To Pandas DataFrames
~~~~~~~~~~~~~~~~~~~~

Convert query results to pandas for statistical analysis:

.. code-block:: python

    # Execute query
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("degree", "betweenness_centrality", "clustering")
         .execute(network)
    )
    
    # Convert to DataFrame
    df = result.to_pandas()
    
    # Standard pandas operations
    print(df.describe())
    print(df[df['degree'] > 10])
    df.to_csv("results.csv", index=False)

**DataFrame structure:**

* Each row is a node
* Columns include: node_id, layer, computed measures

To NetworkX
~~~~~~~~~~~

Export filtered nodes as a NetworkX subgraph:

.. code-block:: python

    # Query for high-degree nodes
    result = (
        Q.nodes()
         .where(degree__gt=10)
         .execute(network)
    )
    
    # Extract as NetworkX subgraph
    node_ids = list(result.node_ids)
    subgraph = network.core_network.subgraph(node_ids)
    
    # Use NetworkX algorithms
    import networkx as nx
    communities = nx.community.louvain_communities(subgraph)

To CSV/JSON
~~~~~~~~~~~

Direct export without intermediate DataFrame:

.. code-block:: python

    # Export to CSV
    (
        Q.nodes()
         .from_layers(L["social"])
         .compute("degree", "betweenness_centrality")
         .export_csv("social_centrality.csv")
         .execute(network)
    )
    
    # Export to JSON
    (
        Q.nodes()
         .compute("degree")
         .export_json("node_degrees.json", orient="records")
         .execute(network)
    )

**Supported formats:**

* CSV (with custom delimiter)
* JSON (various orientations)
* pandas DataFrame (in-memory)

Workflow Integration
--------------------

Pipeline Composition
~~~~~~~~~~~~~~~~~~~~

Chain multiple queries in analysis pipelines:

.. code-block:: python

    # Step 1: Find high-degree nodes
    hubs = (
        Q.nodes()
         .where(degree__gt=20)
         .execute(network)
    )
    
    # Step 2: Compute centrality only for hubs
    hub_centrality = (
        Q.nodes()
         .where(node_id__in=list(hubs.node_ids))
         .compute("betweenness_centrality", "closeness_centrality")
         .execute(network)
    )
    
    # Step 3: Identify super-hubs
    super_hubs = (
        Q.nodes()
         .where(
             node_id__in=list(hubs.node_ids),
             betweenness_centrality__gt=0.1
         )
         .execute(network)
    )
    
    print(f"Hubs: {hubs.count}, Super-hubs: {super_hubs.count}")

Combining with sklearn
~~~~~~~~~~~~~~~~~~~~~~

Integrate DSL results with machine learning pipelines:

.. code-block:: python

    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    
    # Extract features using DSL
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality", "clustering")
         .execute(network)
    )
    
    df = result.to_pandas()
    
    # Prepare features
    features = df[['degree', 'betweenness_centrality', 'clustering']].values
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Cluster nodes
    kmeans = KMeans(n_clusters=5, random_state=42)
    df['cluster'] = kmeans.fit_predict(features_scaled)
    
    # Analyze clusters
    print(df.groupby('cluster')[['degree', 'betweenness_centrality']].mean())

Custom Measures
~~~~~~~~~~~~~~~

While the DSL provides built-in measures, you can compute custom measures using pandas:

.. code-block:: python

    # Get base measures
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    df = result.to_pandas()
    
    # Compute custom measure
    df['influence_score'] = (
        0.6 * df['degree'] / df['degree'].max() +
        0.4 * df['betweenness_centrality'] / df['betweenness_centrality'].max()
    )
    
    # Find top nodes by custom measure
    top_influential = df.nlargest(10, 'influence_score')
    print(top_influential[['node_id', 'influence_score']])

Performance Tips
----------------

Query Optimization
~~~~~~~~~~~~~~~~~~

For large-scale dynamics simulations:

* Use fewer replicates during development, scale up for production
* Consider using numpy backend for faster computation
* Track only essential measures to reduce memory usage
* Use smaller time steps when necessary but be aware of computational cost

Memory Management
~~~~~~~~~~~~~~~~~

For very large networks or long simulations:

* Avoid tracking full trajectories (``trajectory`` measure) if not needed
* Use measure-specific exports rather than full result objects
* Process results in batches for very long time series

Alternative Workflow APIs
-------------------------

Beyond the main DSL, py3plex provides complementary APIs for different programming styles.

Dplyr-Style Operations (graph_ops)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For users familiar with R's dplyr or Python's pandas, ``graph_ops`` provides chainable verb-based operations:

.. code-block:: python

    from py3plex.graph_ops import nodes
    
    # Dplyr-style pipeline
    df = (
        nodes(network)
        .filter(lambda n: n["degree"] > 5)
        .mutate(score=lambda n: n["degree"] * 2)
        .arrange("score", reverse=True)
        .head(10)
        .to_pandas()
    )

**Key verbs:** ``filter()``, ``mutate()``, ``arrange()``, ``select()``, ``group_by()``, ``summarise()``

**Use case:** Interactive exploration and data munging with familiar pandas-like syntax.

Sklearn-Style Pipelines (pipeline)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For reproducible workflows, ``pipeline`` provides scikit-learn style composition:

.. code-block:: python

    from py3plex.pipeline import Pipeline, LoadStep, AggregateLayers
    from py3plex.pipeline import LouvainCommunity, ComputeStats
    
    # Define analysis pipeline
    pipe = Pipeline([
        ("load", LoadStep(path="network.graphml")),
        ("aggregate", AggregateLayers()),
        ("community", LouvainCommunity(resolution=1.0)),
        ("stats", ComputeStats()),
    ])
    
    # Run pipeline
    result = pipe.run()
    
    # Reuse pipeline on different network
    result2 = pipe.set_params(load__path="network2.graphml").run()

**Key steps:** ``LoadStep``, ``AggregateLayers``, ``LeidenMultilayer``, ``FilterNodes``, ``SaveNetwork``

**Use case:** Production workflows, parameter sweeps, and reproducible analysis scripts.

Config-Driven Workflows (workflows)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For declarative specification of complex analyses, ``workflows`` supports YAML/JSON configurations:

.. code-block:: python

    from py3plex.workflows import run_workflow
    
    config = {
        'input': {'path': 'network.edgelist', 'type': 'edgelist'},
        'steps': [
            {'type': 'community_detection', 'algorithm': 'louvain'},
            {'type': 'centrality', 'measures': ['degree', 'betweenness']},
            {'type': 'export', 'format': 'csv', 'path': 'results.csv'}
        ]
    }
    
    results = run_workflow(config)

**Use case:** Batch processing, configuration management, and non-programmer friendly analysis.

Summary
-------

This chapter covered:

1. **DSL-based dynamics simulation** — Declarative framework for SIS, SIR, and Random Walk
2. **Mathematical formalism** — Formal definitions of epidemic models
3. **Multilayer coupling** — Simulating dynamics across network layers
4. **Query integration** — Using Q.nodes() for targeted initial conditions
5. **Parameter comparison** — Systematic exploration of parameter space
6. **Result analysis** — Rich result objects with pandas export and plotting
7. **Alternative APIs** — Dplyr-style, sklearn-style, and config-driven workflows

**Key takeaways:**

* The dynamics DSL follows the same design philosophy as the query DSL
* Simulations are fully declarative and composable
* Integration with query DSL enables sophisticated initial condition specification
* Results are analysis-ready with pandas, xarray, and plotting support
* Choose API style based on your workflow needs: DSL (query-focused), graph_ops (data munging), pipeline (reproducibility), workflows (configuration)

Further Reading
---------------

* Introduction to the Py3plex DSL
* The Builder API and Explain Plans
* ``examples/network_analysis/example_dsl_dynamics.py`` — Complete examples
* ``examples/advanced/example_dynamics_core.py`` — Core dynamics classes
* ``docfiles/sir_epidemic_simulator.rst`` — SIR multiplex simulator documentation
