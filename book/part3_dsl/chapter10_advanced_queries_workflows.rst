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

The dynamics DSL uses a builder API similar to the query DSL. See ``examples/dynamics/`` for complete examples.

**Example 1: SIS Epidemic Model**

See ``examples/dynamics/sis_dynamics.py``:

.. code-block:: bash

    python examples/dynamics/sis_dynamics.py

**Example 2: SIR Epidemic Model**

See ``examples/dynamics/sir_epidemic.py``:

.. code-block:: bash

    python examples/dynamics/sir_epidemic.py

**Example 3: Random Walk Dynamics**

See ``examples/dynamics/random_walk.py``:

.. code-block:: bash

    python examples/dynamics/random_walk.py

**Accessing simulation results:**

.. code-block:: python

    # result.data is a dict of numpy arrays mapping measure names to time-series data
    # Each array has shape (num_runs, num_timesteps)
    print(f"Mean final prevalence: {result.data['prevalence'][:, -1].mean():.3f}")

    # Convert to pandas DataFrames for analysis
    df_dict = result.to_pandas()
    prevalence_df = df_dict['prevalence']  # DataFrame with columns for each timestep

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

    from py3plex.dsl import Q, L
    
    # Group nodes by layer and compute statistics
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    # Convert to pandas and group
    df = result.to_pandas()
    layer_stats = df.groupby('layer').agg({
        'degree': ['mean', 'std', 'max'],
        'betweenness_centrality': ['mean', 'max']
    })
    print(layer_stats)

**See also:** ``examples/network_analysis/example_dsl_advanced.py`` for complete grouping examples.

**Additional grouping patterns:**

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

Dplyr-Style Data Manipulation
------------------------------

The ``graph_ops`` module provides dplyr-style operations (inspired by R's dplyr data manipulation library) for manipulating network data with a chainable API.

**Example 1: Filter and Mutate**

.. code-block:: python

    from py3plex.graph_ops import nodes
    
    # Filter and mutate node data
    df = (
        nodes(network)
        .filter(lambda n: n["degree"] > 2)
        .mutate(score=lambda n: n["degree"] * 2)
        .arrange("degree", reverse=True)
        .to_pandas()
    )
    print(df)

**Example 2: Group and Summarise**

.. code-block:: python

    from py3plex.graph_ops import nodes
    
    # Group by layer and summarise
    df = (
        nodes(network)
        .group_by("layer")
        .summarise(
            mean_degree=("degree", "mean"),
            max_degree=("degree", "max"),
            count=("id", "count")
        )
        .to_pandas()
    )
    print(df)

**See also:** ``examples/network_analysis/example_dsl_dplyr_operations.py`` for complete dplyr-style examples.

**Example 3: Subgraph Extraction**

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Extract subgraph for high-degree nodes
    subgraph = (
        Q.nodes()
         .where(degree__gt=5)
         .to_networkx()
         .execute(network)
    )
    uv run examples/04_graph_ops/03_subgraph.py
    
    # Or using python
    python examples/04_graph_ops/03_subgraph.py

**Supported export formats:**

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

Advanced DSL Features
---------------------

This section covers advanced DSL capabilities including field expressions, semiring algebra, and compositional uncertainty quantification.

Field Expressions (F Builder)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **F builder** provides a Pythonic way to construct complex boolean conditions in WHERE clauses using operator overloading:

.. code-block:: python

    from py3plex.dsl import Q, L, F
    
    # Simple comparison
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("degree", "clustering")
         .where(F.degree > 5)
         .execute(network)
    )
    
    # Complex boolean logic with AND/OR
    result = (
        Q.nodes()
         .compute("degree", "clustering")
         .where((F.degree > 10) | ((F.layer == "social") & (F.clustering < 0.5)))
         .execute(network)
    )
    
    # Negation
    result = (
        Q.nodes()
         .where(~F.is_infected)
         .execute(network)
    )
    
    # Mix with kwargs
    result = (
        Q.nodes()
         .where(F.degree > 5, layer="social")
         .execute(network)
    )

**Supported operators:**

* Comparison: ``>``, ``>=``, ``<``, ``<=``, ``==``, ``!=``
* Boolean: ``&`` (AND), ``|`` (OR), ``~`` (NOT)
* Parentheses for grouping: ``(F.a > 5) & (F.b < 10)``

**Example:** See ``examples/dsl_zoo/28_field_expressions.py``

.. code-block:: bash

    python examples/dsl_zoo/28_field_expressions.py

**Advantages:**

* Type-safe compared to string-based queries
* IDE autocompletion for field names
* Natural Python syntax with operators
* Combines with kwargs-based filtering

Semiring Algebra (S Builder)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **S builder** provides semiring-based path queries for computing shortest paths, reachability, and closure operations:

.. code-block:: python

    from py3plex.dsl import S, L
    
    # Shortest paths using min-plus semiring
    result = (
        S.path()
         .source("A")
         .semiring("min_plus")
         .from_layers(L["*"])
         .execute(network)
    )
    
    # All-pairs shortest paths via closure
    result = (
        S.closure()
         .semiring("min_plus")
         .from_layers(L["social"])
         .method("auto")
         .execute(network)
    )
    
    # Reachability using boolean semiring
    result = (
        S.closure()
         .semiring("boolean")
         .from_layers(L["*"])
         .execute(network)
    )

**Available semirings:**

* ``min_plus`` — Shortest paths (tropical semiring)
* ``boolean`` — Reachability (OR-AND algebra)
* ``max_times`` — Widest paths (reliability)

**Path constraints:**

* ``.max_hops(k)`` — Limit path length to k hops
* ``.crossing_layers("allowed")`` — Allow cross-layer edges
* ``.witness(True)`` — Track witness paths

**Example:** See ``examples/dsl_zoo/24_semiring_closure.py``

.. code-block:: bash

    python examples/dsl_zoo/24_semiring_closure.py

**Use cases:**

* Multi-hop analysis in multilayer networks
* Layer-aware shortest paths
* Network accessibility and connectivity analysis

Compositional Uncertainty Quantification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Compositional UQ** extends basic uncertainty quantification to aggregate and ranking operations, providing uncertainty estimates for complex query results:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Per-layer aggregation with uncertainty
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree", "clustering")
         .per_layer()
         .aggregate(
             avg_degree="mean(degree)",
             max_cluster="max(clustering)",
             node_count="count()"
         )
         .uq(method="bootstrap", n_samples=20, ci=0.95, seed=42)
         .execute(network)
    )
    
    # Ranking with stability metrics
    result = (
        Q.nodes()
         .compute("degree")
         .order_by("-degree")
         .limit(10)
         .uq(method="perturbation", n_samples=50, seed=42)
         .execute(network)
    )

**Key features:**

* **Aggregate UQ:** Mean, median, max, min with confidence intervals
* **Ranking stability:** Top-k selection with stability scores
* **Coverage probability:** Membership probability in result sets
* **Method support:** bootstrap, perturbation, seed-based resampling

**Result structure:**

Aggregates return dictionary values with uncertainty:

.. code-block:: python

    # Example aggregate result
    {
        'mean': 5.2,           # Point estimate
        'std': 0.3,            # Standard error
        'quantiles': {         # Confidence intervals
            0.025: 4.8,
            0.975: 5.6
        },
        'n_samples': 20
    }

**Example:** See ``examples/dsl_zoo/42_compositional_uq.py``

.. code-block:: bash

    python examples/dsl_zoo/42_compositional_uq.py

**Use cases:**

* Robust layer comparisons with statistical confidence
* Stable hub identification in noisy networks
* Uncertainty-aware decision making
* Sensitivity analysis for network metrics

Guided Quickstart Recipes
--------------------------

These task-oriented recipes demonstrate best practices for common multilayer network analysis tasks. Each recipe is minimal (≤10 lines) and uses DSL v2 with modern practices.

Recipe 1: Find Hubs Across Layers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Identify nodes that are highly central across multiple network layers:

.. code-block:: python

    from py3plex.dsl import Q, L
    from py3plex.core import multinet
    
    # Load your network
    net = multinet.multi_layer_network()
    net.load_network("network.graphml")
    
    # Find nodes with high degree in multiple layers
    result = (
        Q.nodes()
         .from_layers(L["*"])  # All layers
         .compute("degree", "betweenness_centrality")
         .per_layer()  # Group by layer
           .top_k(10, "degree")  # Top 10 per layer
         .end_grouping()
         .coverage(mode="at_least", k=2)  # Present in ≥2 layers
         .order_by("-degree")
         .execute(net)
    )
    
    # Export hub nodes
    df = result.to_pandas()
    df.to_csv("cross_layer_hubs.csv", index=False)
    print(f"Found {result.count} hubs across {len(net.get_layers())} layers")

**Best practices:**

* Use ``per_layer()`` for layer-aware analysis
* Apply ``coverage()`` to find persistent hubs
* Always ``end_grouping()`` before applying filters

Recipe 2: Compare Two Multilayer Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Systematically compare network structure and metrics across two networks:

.. code-block:: python

    from py3plex.dsl import Q, C
    
    # Load two networks
    net1 = multinet.multi_layer_network()
    net1.load_network("network_v1.graphml")
    
    net2 = multinet.multi_layer_network()
    net2.load_network("network_v2.graphml")
    
    # Compare using C (Compare) builder
    comparison = (
        C.networks(baseline=net1, treatment=net2)
         .compare_structure()  # Node/edge counts, density
         .compare_metrics("degree", "betweenness_centrality")
         .per_layer()  # Compare layer-by-layer
         .execute()
    )
    
    # Access comparison results
    df_structural = comparison.structural_diff()
    df_metrics = comparison.metric_diff()
    
    print(df_structural)
    print(df_metrics)

**Alternative: Manual comparison with provenance**

.. code-block:: python

    # Query with provenance for reproducibility
    result1 = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .provenance(mode="replayable")
         .execute(net1)
    )
    
    result2 = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .provenance(mode="replayable")
         .execute(net2)
    )
    
    # Compare DataFrames
    df1 = result1.to_pandas()
    df2 = result2.to_pandas()
    
    # Compute differences (e.g., degree changes)
    merged = df1.merge(df2, on=["id", "layer"], suffixes=("_v1", "_v2"))
    merged["degree_diff"] = merged["degree_v2"] - merged["degree_v1"]

Recipe 3: Run Community Detection with Uncertainty
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Find communities with uncertainty quantification to assess partition stability:

.. code-block:: python

    from py3plex.dsl import Q, UQ
    
    # Community detection with UQ
    result = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .community(method="leiden", gamma=1.2, omega=0.8, random_state=42)
         .uq(method="ensemble", n_samples=50, seed=42)
         .execute(net)
    )
    
    # Access consensus partition and stability
    consensus_partition = result.meta["consensus_partition"]
    score_ci = result.meta["score_ci"]  # Confidence interval for modularity
    
    print(f"Consensus modularity: {score_ci['mean']:.3f} ± {score_ci['std']:.3f}")
    print(f"95% CI: [{score_ci['ci95_low']:.3f}, {score_ci['ci95_high']:.3f}]")
    
    # Get community assignments with uncertainty
    df = result.to_pandas()
    print(df[["id", "layer", "community_id"]].head())

**Best practices:**

* Use ``random_state`` for reproducibility
* UQ method ``ensemble`` is best for community detection
* Check ``score_ci`` to assess partition quality

Recipe 4: Export Reproducible Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create fully reproducible analysis results with provenance tracking:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Query with full provenance
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("degree", "betweenness_centrality", "clustering")
         .uq(method="bootstrap", n_samples=100, seed=42)
         .provenance(mode="replayable", capture="snapshot")
         .execute(net)
    )
    
    # Export bundle with everything needed for replay
    result.export_bundle("analysis_results.bundle.json.gz", compress=True)
    
    # Also export data tables
    df = result.to_pandas(expand_uncertainty=True)
    df.to_csv("metrics_with_uncertainty.csv", index=False)
    
    # Later: Replay the analysis
    from py3plex.provenance.replay import replay_query_from_bundle
    replayed_result = replay_query_from_bundle("analysis_results.bundle.json.gz")
    
    # Results should match exactly
    assert replayed_result.count == result.count

**Best practices:**

* Always set ``seed`` for UQ to ensure reproducibility
* Use ``provenance(mode="replayable")`` for full replay capability
* Export bundle immediately after execution
* Store bundle with analysis outputs for audit trail

**Provenance bundle contents:**

* Query AST (serialized)
* Network snapshot or fingerprint
* Parameter values
* Random seeds
* Environment info (py3plex version, Python version)
* Optionally: Full result data

Summary
-------

This chapter covered:

1. **DSL-based dynamics simulation** — Declarative framework for SIS, SIR, and Random Walk
2. **Mathematical formalism** — Formal definitions of epidemic models
3. **Multilayer coupling** — Simulating dynamics across network layers
4. **Query integration** — Using Q.nodes() for targeted initial conditions
5. **Parameter comparison** — Systematic exploration of parameter space
6. **Result analysis** — Rich result objects with pandas export and plotting
7. **Field expressions (F)** — Type-safe boolean conditions with operator overloading
8. **Semiring algebra (S)** — Path queries and closure operations with semiring semantics
9. **Compositional UQ** — Uncertainty quantification for aggregates and rankings
10. **Alternative APIs** — Dplyr-style, sklearn-style, and config-driven workflows

**Key takeaways:**

* The dynamics DSL follows the same design philosophy as the query DSL
* Simulations are fully declarative and composable
* Integration with query DSL enables sophisticated initial condition specification
* F expressions provide type-safe filtering with natural Python operators
* S builder enables semiring-based path analysis across layers
* Compositional UQ propagates uncertainty through complex query pipelines
* Results are analysis-ready with pandas, xarray, and plotting support
* Choose API style based on your workflow needs: DSL (query-focused), graph_ops (data munging), pipeline (reproducibility), workflows (configuration)

Further Reading
---------------

* Introduction to the Py3plex DSL (Chapter 8)
* The Builder API and Explain Plans (Chapter 9)
* ``examples/03_dsl_v2/`` — Advanced DSL examples
* ``examples/04_graph_ops/`` — Data manipulation examples
* ``examples/06_dynamics/`` — Dynamics simulation examples
* ``docfiles/sir_epidemic_simulator.rst`` — SIR multiplex simulator documentation
