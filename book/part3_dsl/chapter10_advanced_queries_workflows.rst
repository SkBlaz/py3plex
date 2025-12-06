Chapter 10: Advanced Queries and Workflows
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
* **Update rules:**
  
  * S → I with probability λᵢ = 1 - ∏ⱼ (1 - β)^(Aᵢⱼ · Iⱼ)
  * I → S with probability μ

* **Parameters:**
  
  * β: transmission probability per contact (0 ≤ β ≤ 1)
  * μ: recovery probability per time step (0 ≤ μ ≤ 1)

The SIS model exhibits endemic equilibria when R₀ = β/μ · λ₁(A) > 1, where
λ₁(A) is the largest eigenvalue of the adjacency matrix.

**SIR Model (Susceptible-Infected-Recovered)**

The SIR model includes permanent immunity after recovery:

* **States:** S (susceptible), I (infected), R (recovered/removed)
* **Update rules:**
  
  * S → I with probability λᵢ = 1 - ∏ⱼ (1 - β)^(Aᵢⱼ · Iⱼ)
  * I → R with probability γ

* **Parameters:**
  
  * β: transmission probability per contact
  * γ: recovery probability per time step

The final outbreak size (attack rate) depends on the basic reproduction number
R₀ = β/γ · ⟨k⟩, where ⟨k⟩ is the mean degree.

**Random Walk**

Random walk dynamics model diffusion processes:

* **State:** Current node position
* **Update rule:** Move to neighbor j with probability 1/degree(i), or stay
  at i with probability p_lazy (for lazy walks)
* **Parameters:**
  
  * teleport: probability of random teleportation (default: 0.05)

Basic Dynamics DSL Usage
~~~~~~~~~~~~~~~~~~~~~~~~~

The dynamics DSL uses a builder API similar to the query DSL:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dynamics import D, SIS
    from py3plex.dsl import L

    # Create network
    network = multinet.multi_layer_network()
    # ... add nodes and edges ...

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
This chapter explores advanced DSL patterns for complex multilayer network analyses.

.. admonition:: Advanced DSL Patterns
   :class: dsl-example

   The DSL supports sophisticated analysis workflows:

   .. code-block:: python

       from py3plex.dsl import Q, L, Param

       # 1. Parameterized queries for systematic analysis
       query = (
           Q.nodes()
            .from_layers(L[Param.str("layer")])
            .where(degree__gt=Param.int("threshold"))
            .compute("betweenness_centrality")
            .limit(Param.int("top_n"))
       )

       # Execute with different parameters
       for layer in ["social", "work", "family"]:
           result = query.execute(network, layer=layer, threshold=5, top_n=20)
           result.to_pandas().to_csv(f"{layer}_hubs.csv")

       # 2. Multi-layer comparative analysis
       comparison = []
       for layer in network.get_layers():
           stats = (
               Q.nodes()
                .from_layers(L[layer])
                .compute("degree", "betweenness_centrality", "clustering")
                .execute(network)
           )
           df = stats.to_pandas()
           comparison.append({
               'layer': layer,
               'nodes': stats.count,
               'avg_degree': df['degree'].mean(),
               'max_bc': df['betweenness_centrality'].max(),
           })

       # 3. EXPLAIN mode for optimization
       expensive_query = Q.nodes().compute("betweenness_centrality")
       plan = expensive_query.explain().execute(network)
       for step in plan.steps:
           print(f"{step.description}: {step.estimated_complexity}")

   Advanced patterns enable complex research workflows!

*TODO: Expand from advanced DSL examples and patterns*

Complex Query Patterns
-----------------------

Multilayer Motifs
~~~~~~~~~~~~~~~~~

[Pattern detection across layers]

Multilayer Paths
~~~~~~~~~~~~~~~~

[Path queries respecting layer structure]

Aggregations and Grouping
~~~~~~~~~~~~~~~~~~~~~~~~~~

[Aggregate measures by layer]

Result Conversion
-----------------

To Pandas DataFrames
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    df = result.to_pandas()

To NetworkX
~~~~~~~~~~~

[Export query results as NetworkX graphs]

To Arrow/Parquet
~~~~~~~~~~~~~~~~

[High-performance export]

Workflow Integration
--------------------

Pipeline Composition
~~~~~~~~~~~~~~~~~~~~

[Chain multiple queries]

Combining with sklearn
~~~~~~~~~~~~~~~~~~~~~~

[Integration with machine learning pipelines]

Custom Measures
~~~~~~~~~~~~~~~

[Extending the DSL with custom functions]

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

Summary
-------

This chapter covered:

1. **DSL-based dynamics simulation** — Declarative framework for SIS, SIR, and Random Walk
2. **Mathematical formalism** — Formal definitions of epidemic models
3. **Multilayer coupling** — Simulating dynamics across network layers
4. **Query integration** — Using Q.nodes() for targeted initial conditions
5. **Parameter comparison** — Systematic exploration of parameter space
6. **Result analysis** — Rich result objects with pandas export and plotting

**Key takeaways:**

* The dynamics DSL follows the same design philosophy as the query DSL
* Simulations are fully declarative and composable
* Integration with query DSL enables sophisticated initial condition specification
* Results are analysis-ready with pandas, xarray, and plotting support

Further Reading
---------------

* Chapter 8: Introduction to the Py3plex DSL
* Chapter 9: The Builder API and Explain Plans
* ``examples/network_analysis/example_dsl_dynamics.py`` — Complete examples
* ``examples/advanced/example_dynamics_core.py`` — Core dynamics classes
* ``docfiles/sir_epidemic_simulator.rst`` — SIR multiplex simulator documentation
