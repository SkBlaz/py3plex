How to Simulate Multilayer Dynamics
====================================

This guide presents py3plex as a comprehensive framework for simulating dynamical processes on multilayer networks. We cover epidemic models (SIR, SIS), diffusion processes (random walks), and custom dynamics implementations—all with full multilayer support.

**Prerequisites:** A loaded multilayer network (see :doc:`load_and_build_networks`).

Overview
--------

Multilayer dynamics in py3plex enable you to model processes where interactions occur across multiple types of relationships simultaneously. Typical use cases include:

* **Epidemic spread**: Disease transmission through household, workplace, and social contact layers
* **Information diffusion**: News spreading via online and offline communication channels
* **Random walks**: Navigation and search processes across interconnected network layers
* **Opinion dynamics**: Belief propagation through multiple social contexts

**Simulation Pipeline**

The typical workflow for running dynamics simulations consists of five steps:

1. **Load or build** a multilayer network using ``py3plex.core.multinet``
2. **Choose a dynamics model** (e.g., ``SIRDynamics``, ``SISDynamics``, ``RandomWalkDynamics``)
3. **Configure parameters** and initial conditions (infection rates, starting nodes, etc.)
4. **Run the simulation** via ``.run(steps=...)`` with a fixed seed for reproducibility
5. **Inspect the results** object using ``.get_measure(...)`` to extract time series and summary statistics

This pipeline provides a consistent interface across all dynamics models while allowing specialized configurations for multilayer network effects.

Common Concepts & API
---------------------

Node and Layer Representation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dynamics in py3plex operate on the **supra-network** representation, where multilayer nodes are encoded as ``(node_id, layer)`` tuples. For example, Alice in the "friends" layer is represented as ``('Alice', 'friends')``. 

When you pass a multilayer network to a dynamics model:

* Node states are tracked per node-layer pair
* Infection, diffusion, or walker movements respect both intra-layer and inter-layer edges
* You can query per-layer statistics after simulation

For single-layer NetworkX graphs, nodes are used directly without tuple encoding.

Time and Synchrony
~~~~~~~~~~~~~~~~~~

All dynamics models in this guide use **discrete-time, synchronous updates**:

* Time advances in integer steps: t = 0, 1, 2, ...
* At each step, all nodes update simultaneously based on the state at time t
* This differs from continuous-time (Gillespie) models, which are also available in ``py3plex.dynamics``

Randomness & Reproducibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every dynamics model has a dedicated random number generator controlled by ``.set_seed(seed)``:

.. code-block:: python

    dynamics.set_seed(42)
    results = dynamics.run(steps=100)

Setting the seed ensures:

* Reproducible initial conditions (which nodes start infected, which are susceptible)
* Reproducible stochastic transitions (infection events, recovery events, random walk steps)
* Consistent results across multiple runs with the same seed

Network Requirements
~~~~~~~~~~~~~~~~~~~~

Dynamics models work with:

* **py3plex multilayer networks**: Full support for inter-layer and intra-layer edges
* **NetworkX graphs**: Single-layer networks (directed or undirected)
* **Edge weights**: Used in weighted random walks; epidemic models currently treat edges as unweighted contacts

Common Base Interface
~~~~~~~~~~~~~~~~~~~~~

All dynamics classes inherit from ``DynamicsProcess`` (discrete-time) or ``ContinuousTimeProcess`` (continuous-time). The core methods are:

.. code-block:: python

    from py3plex.dynamics import SIRDynamics
    
    # Initialize with network and parameters
    dynamics = SIRDynamics(network, beta=0.3, gamma=0.1, initial_infected=0.05)
    
    # Set seed for reproducibility
    dynamics.set_seed(42)
    
    # Run for specified number of steps
    results = dynamics.run(steps=100)
    
    # Extract measures
    prevalence = results.get_measure("prevalence")
    state_counts = results.get_measure("state_counts")

The ``results`` object is always a ``DynamicsResult`` instance with standardized measure extraction methods.

SIR Epidemic Model on Multilayer Networks
------------------------------------------

Formal Description
~~~~~~~~~~~~~~~~~~

The **SIR (Susceptible-Infected-Recovered)** model describes epidemic spread with three compartments:

* **S (Susceptible)**: Nodes that can become infected
* **I (Infected)**: Nodes that are currently infectious
* **R (Recovered)**: Nodes with permanent immunity (absorbing state)

**Discrete-Time Update Rules** (synchronous):

1. **Recovery**: Each infected node recovers (I → R) with probability γ per time step
2. **Infection**: Each susceptible node with k infected neighbors becomes infected (S → I) with probability

   .. math::

      p_{\text{infect}} = 1 - (1 - \beta)^k

   where β is the per-contact infection probability

3. **Absorption**: Recovered nodes remain recovered (R → R) forever

**Multilayer Extension**

On multilayer networks, the infection pressure on a node aggregates across all layers:

* A susceptible node ``(i, layer_A)`` counts infected neighbors from both intra-layer edges (within ``layer_A``) and inter-layer edges (to other layers)
* You can specify layer-specific transmission rates β as a dictionary (see :ref:`layer-specific-params`)

This means epidemics can spread within layers and jump between layers via inter-layer connections, mimicking real-world scenarios like workplace and household transmission.

Code Example
~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dynamics import SIRDynamics
    
    # Create a simple two-layer network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes in two layers
    nodes = []
    for i in range(20):
        nodes.append({'source': i, 'type': 'layer1'})
        nodes.append({'source': i, 'type': 'layer2'})
    network.add_nodes(nodes)
    
    # Add intra-layer edges (chain structure)
    edges = []
    for i in range(19):
        edges.append({'source': i, 'target': i+1, 
                      'source_type': 'layer1', 'target_type': 'layer1'})
        edges.append({'source': i, 'target': i+1, 
                      'source_type': 'layer2', 'target_type': 'layer2'})
    
    # Add inter-layer edges (node replicas)
    for i in range(20):
        edges.append({'source': i, 'target': i,
                      'source_type': 'layer1', 'target_type': 'layer2'})
    
    network.add_edges(edges)
    
    # Configure SIR model
    sir = SIRDynamics(
        network,
        beta=0.3,    # Infection probability per contact
        gamma=0.1,   # Recovery probability per time step
        initial_infected=0.05  # 5% of nodes initially infected
    )
    
    # Run simulation with fixed seed
    sir.set_seed(42)
    results = sir.run(steps=100)
    
    # Extract measures
    prevalence = results.get_measure("prevalence")
    state_counts = results.get_measure("state_counts")
    
    # Print summary statistics
    peak_time = prevalence.argmax()
    print(f"Peak prevalence: {prevalence.max():.2%} at step {peak_time}")
    print(f"Final susceptible: {state_counts['S'][-1]} nodes")
    print(f"Final infected: {state_counts['I'][-1]} nodes")
    print(f"Final recovered: {state_counts['R'][-1]} nodes")
    print(f"Attack rate: {state_counts['R'][-1] / network.core_network.number_of_nodes():.2%}")

**Expected Output**

.. code-block:: text

    Peak prevalence: 35.00% at step 16
    Final susceptible: 0 nodes
    Final infected: 0 nodes
    Final recovered: 40 nodes
    Attack rate: 100.00%

*Note: Exact values depend on network structure and random seed. The example shows a complete outbreak where all nodes eventually get infected.*

Time Series Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~

Track the epidemic curve over time:

.. code-block:: python

    import matplotlib.pyplot as plt
    
    # Get time series data
    state_counts = results.get_measure("state_counts")
    steps = range(len(state_counts['S']))
    
    # Plot S, I, R trajectories
    plt.figure(figsize=(10, 6))
    plt.plot(steps, state_counts['S'], label='Susceptible', color='blue', linewidth=2)
    plt.plot(steps, state_counts['I'], label='Infected', color='red', linewidth=2)
    plt.plot(steps, state_counts['R'], label='Recovered', color='green', linewidth=2)
    
    plt.xlabel('Time step', fontsize=12)
    plt.ylabel('Number of nodes', fontsize=12)
    plt.title('SIR Epidemic Dynamics on Multilayer Network', fontsize=14)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig('sir_dynamics.png', dpi=300, bbox_inches='tight')
    plt.show()

The plot shows the characteristic SIR pattern: S decreases monotonically, I rises then falls (forming a peak), and R increases monotonically until saturation. The peak prevalence and timing depend on β, γ, and network structure.

SIS Epidemic Model on Multilayer Networks
------------------------------------------

Formal Description
~~~~~~~~~~~~~~~~~~

The **SIS (Susceptible-Infected-Susceptible)** model describes epidemics **without permanent immunity**:

* **S (Susceptible)**: Nodes that can become infected
* **I (Infected)**: Nodes that are currently infectious

**Discrete-Time Update Rules** (synchronous):

1. **Recovery**: Each infected node recovers (I → S) with probability γ (or μ) per time step
2. **Infection**: Each susceptible node with k infected neighbors becomes infected (S → I) with probability

   .. math::

      p_{\text{infect}} = 1 - (1 - \beta)^k

3. **No absorption**: Recovered nodes immediately return to susceptible state, allowing reinfection

**Endemic Equilibrium**

Unlike SIR (which eventually dies out), SIS can reach an **endemic equilibrium** where a steady fraction of nodes remain infected. The basic reproduction number is:

.. math::

   R_0 = \frac{\beta}{\gamma} \langle k \rangle

where ⟨k⟩ is the average degree. If R₀ > 1, the epidemic persists; if R₀ ≤ 1, it dies out.

**Multilayer Extension**

On multilayer networks, SIS infection pressure aggregates across all layers, similar to SIR. The endemic prevalence can differ across layers if you use layer-specific transmission rates.

Code Example
~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dynamics import SISDynamics
    
    # Use the same multilayer network as before
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes and edges (same as SIR example)
    nodes = []
    for i in range(20):
        nodes.append({'source': i, 'type': 'layer1'})
        nodes.append({'source': i, 'type': 'layer2'})
    network.add_nodes(nodes)
    
    edges = []
    for i in range(19):
        edges.append({'source': i, 'target': i+1,
                      'source_type': 'layer1', 'target_type': 'layer1'})
        edges.append({'source': i, 'target': i+1,
                      'source_type': 'layer2', 'target_type': 'layer2'})
    for i in range(20):
        edges.append({'source': i, 'target': i,
                      'source_type': 'layer1', 'target_type': 'layer2'})
    network.add_edges(edges)
    
    # Configure SIS model
    sis = SISDynamics(
        network,
        beta=0.3,    # Infection probability per contact
        mu=0.1,      # Recovery probability (also accepts 'gamma')
        initial_infected=0.05
    )
    
    # Run for longer to reach equilibrium
    sis.set_seed(42)
    results = sis.run(steps=200)
    
    # Extract prevalence time series
    prevalence = results.get_measure("prevalence")
    
    # Compute endemic prevalence (mean of last 50 steps)
    endemic_prevalence = prevalence[-50:].mean()
    print(f"Endemic prevalence: {endemic_prevalence:.2%}")
    print(f"Std (last 50 steps): {prevalence[-50:].std():.3f}")
    
    # Check if epidemic persisted
    if endemic_prevalence > 0.01:
        print("Status: Endemic state reached")
    else:
        print("Status: Epidemic died out")

**Expected Output**

.. code-block:: text

    Endemic prevalence: 0.00%
    Std (last 50 steps): 0.000
    Status: Epidemic died out

*Note: On sparse chain-like networks with moderate β/γ, the epidemic often dies out due to low R₀. Try denser networks or higher β to observe endemic states.*

Comparison with SIR
~~~~~~~~~~~~~~~~~~~

The key difference between SIS and SIR:

* **SIR**: Forms a peak and dies out (all nodes eventually become R or remain S)
* **SIS**: Can sustain long-term endemic prevalence if R₀ > 1

.. code-block:: python

    import matplotlib.pyplot as plt
    import networkx as nx
    from py3plex.dynamics import SISDynamics, SIRDynamics
    
    # Use a denser network to see endemic behavior
    G = nx.watts_strogatz_graph(n=100, k=6, p=0.1, seed=42)
    
    # Run SIS
    sis = SISDynamics(G, beta=0.3, mu=0.1, initial_infected=0.1)
    sis.set_seed(42)
    sis_results = sis.run(steps=150)
    sis_prev = sis_results.get_measure("prevalence")
    
    # Run SIR
    sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
    sir.set_seed(42)
    sir_results = sir.run(steps=150)
    sir_prev = sir_results.get_measure("prevalence")
    
    # Plot comparison
    plt.figure(figsize=(10, 6))
    plt.plot(sis_prev, label='SIS (endemic)', color='red', linewidth=2)
    plt.plot(sir_prev, label='SIR (dies out)', color='blue', linewidth=2)
    plt.xlabel('Time step')
    plt.ylabel('Prevalence')
    plt.title('SIS vs SIR Epidemic Dynamics')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

Random Walk Dynamics
--------------------

Formal Description
~~~~~~~~~~~~~~~~~~

Random walk dynamics simulate the movement of a walker (or multiple walkers) on the network. At each time step:

1. The walker is at some node (or node-layer pair) ``v``
2. With probability ``lazy_probability``, the walker stays at ``v``
3. With probability ``1 - lazy_probability``, the walker moves to a uniformly random neighbor

**Multilayer Random Walks**

On multilayer networks:

* Walkers navigate both intra-layer edges (within a layer) and inter-layer edges (between layers)
* The state is a node-layer tuple, e.g., ``(node_id, layer)``
* Transition probabilities are uniform over all neighbors (intra-layer + inter-layer)

Random walks are fundamental for:

* Computing stationary distributions (related to PageRank and eigenvector centrality)
* Modeling diffusion and search processes
* Estimating hitting times between nodes

Code Example
~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dynamics import RandomWalkDynamics
    
    # Create a two-layer network
    network = multinet.multi_layer_network(directed=False)
    
    # Ring structure in layer1, star structure in layer2
    n = 15
    nodes = []
    for i in range(n):
        nodes.append({'source': i, 'type': 'ring'})
        nodes.append({'source': i, 'type': 'star'})
    network.add_nodes(nodes)
    
    # Ring layer: circular edges
    edges = []
    for i in range(n):
        edges.append({'source': i, 'target': (i+1) % n,
                      'source_type': 'ring', 'target_type': 'ring'})
    
    # Star layer: hub-spoke (node 0 is hub)
    for i in range(1, n):
        edges.append({'source': 0, 'target': i,
                      'source_type': 'star', 'target_type': 'star'})
    
    # Inter-layer edges
    for i in range(n):
        edges.append({'source': i, 'target': i,
                      'source_type': 'ring', 'target_type': 'star'})
    
    network.add_edges(edges)
    
    # Configure random walk
    walk = RandomWalkDynamics(
        network,
        start_node=(0, 'ring'),  # Start at node 0 in ring layer
        lazy_probability=0.1
    )
    
    # Run for 1000 steps
    walk.set_seed(42)
    results = walk.run(steps=1000)
    
    # Get trajectory and compute visit counts
    trajectory = results.get_measure("trajectory")
    visit_counts = walk.visit_counts(trajectory)
    
    # Sort by visit frequency
    sorted_visits = sorted(visit_counts.items(), key=lambda x: x[1], reverse=True)
    
    print(f"Total unique nodes visited: {len(visit_counts)}")
    print(f"\\nTop 10 most visited nodes:")
    for node, count in sorted_visits[:10]:
        print(f"  {node}: {count} visits ({count/len(trajectory):.2%})")

**Expected Output**

.. code-block:: text

    Total unique nodes visited: 30
    
    Top 10 most visited nodes:
      (0, 'star'): 87 visits (8.69%)
      (0, 'ring'): 64 visits (6.39%)
      (1, 'ring'): 42 visits (4.20%)
      (14, 'ring'): 39 visits (3.90%)
      (1, 'star'): 37 visits (3.70%)
      (2, 'ring'): 36 visits (3.60%)
      (13, 'ring'): 35 visits (3.50%)
      (2, 'star'): 34 visits (3.40%)
      (3, 'star'): 32 visits (3.20%)
      (14, 'star'): 31 visits (3.10%)

*Note: The hub node in the star layer receives disproportionately high visits due to its high degree.*

Analyzing Layer Switching
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can analyze how often the walker switches between layers:

.. code-block:: python

    # Count layer switches
    switches = 0
    for i in range(len(trajectory) - 1):
        current_layer = trajectory[i][1]
        next_layer = trajectory[i + 1][1]
        if current_layer != next_layer:
            switches += 1
    
    print(f"Total layer switches: {switches}")
    print(f"Switch rate: {switches / (len(trajectory) - 1):.2%}")

This reveals how "coupled" the layers are through inter-layer edges. High switch rates indicate strong inter-layer connectivity.

.. _layer-specific-params:

Layer-Specific and Time-Varying Parameters
-------------------------------------------

Layer-Specific Transmission Rates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can configure different infection rates for different layers by passing a **dictionary** for the ``beta`` parameter:

.. code-block:: python

    from py3plex.dynamics import SIRDynamics
    
    # Define layer-specific transmission rates
    layer_rates = {
        'household': 0.5,   # High transmission in households
        'workplace': 0.2,   # Medium transmission at work
        'social': 0.1       # Low transmission in casual social contacts
    }
    
    sir = SIRDynamics(
        network,
        beta=layer_rates,   # Pass dict instead of scalar
        gamma=0.1,
        initial_infected=0.05
    )
    
    results = sir.run(steps=100)

**How It Works**

* When computing infection pressure on a node ``(i, layer_A)``, edges within ``layer_A`` use ``beta['layer_A']``
* Inter-layer edges use a default or average beta (implementation-dependent)
* This allows modeling realistic scenarios where transmission varies by context

**Extracting Per-Layer Statistics**

After running the simulation, you can compute layer-specific prevalence manually:

.. code-block:: python

    # Get final state
    final_state = results.trajectory[-1]
    
    # Count infected nodes per layer
    layer_prevalence = {}
    for node, state in final_state.items():
        if isinstance(node, tuple):  # Multilayer node
            node_id, layer = node
            if layer not in layer_prevalence:
                layer_prevalence[layer] = {'S': 0, 'I': 0, 'R': 0}
            layer_prevalence[layer][state] += 1
    
    # Print per-layer statistics
    for layer, counts in layer_prevalence.items():
        total = sum(counts.values())
        print(f"Layer {layer}: {counts['R']} recovered out of {total} nodes ({counts['R']/total:.2%})")

Time-Varying Parameters (Intervention Scenarios)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To model interventions (e.g., school closures, social distancing), you can run multiple simulations with different parameters for different time windows:

.. code-block:: python

    # Scenario 1: Baseline (no intervention)
    sir = SIRDynamics(network, beta=0.3, gamma=0.1, initial_infected=0.05)
    sir.set_seed(42)
    results_baseline = sir.run(steps=100)
    
    # Scenario 2: Intervention at t=30 (reduce beta)
    # Run phase 1 (before intervention)
    sir = SIRDynamics(network, beta=0.3, gamma=0.1, initial_infected=0.05)
    sir.set_seed(42)
    state_30 = sir.run(steps=30, record=False)  # Get state at t=30
    
    # Run phase 2 (with reduced beta)
    sir_intervention = SIRDynamics(network, beta=0.15, gamma=0.1)
    sir_intervention.seed = 42  # Continue from same seed
    results_intervention = sir_intervention.run(steps=70, state=state_30)
    
    # Compare peak prevalence
    print(f"Baseline peak: {results_baseline.get_measure('prevalence').max():.2%}")
    print(f"Intervention peak: {results_intervention.get_measure('prevalence').max():.2%}")

*Note: For more complex time-varying scenarios, consider using the high-level simulation builder API (see next steps).*

Result Objects and Metrics
---------------------------

DynamicsResult API
~~~~~~~~~~~~~~~~~~

All dynamics models return a ``DynamicsResult`` object from ``.run()``. This object provides:

* **Trajectory access**: Direct indexing ``results[t]`` or ``results.trajectory``
* **Measure extraction**: ``.get_measure(name)`` for standard metrics
* **Conversion**: ``.to_pandas()`` for DataFrame export

Common Measures
~~~~~~~~~~~~~~~

The following table summarizes available measures for each model:

.. list-table::
   :header-rows: 1
   :widths: 15 20 40 25

   * - Model
     - Measure
     - Description
     - Return Type
   * - SIR
     - ``"prevalence"``
     - Fraction of infected nodes over time (I / total)
     - ``numpy.ndarray``
   * - SIR
     - ``"state_counts"``
     - Counts of nodes in each state (S, I, R) over time
     - ``dict[str, numpy.ndarray]``
   * - SIR
     - ``"trajectory"``
     - Raw state sequence (list of state dicts)
     - ``list[dict]``
   * - SIS
     - ``"prevalence"``
     - Fraction of infected nodes over time (I / total)
     - ``numpy.ndarray``
   * - SIS
     - ``"state_counts"``
     - Counts of nodes in each state (S, I) over time
     - ``dict[str, numpy.ndarray]``
   * - SIS
     - ``"trajectory"``
     - Raw state sequence
     - ``list[dict]``
   * - RandomWalk
     - ``"trajectory"``
     - Sequence of visited nodes (or node-layer pairs)
     - ``list``

**Note**: Measures like ``"peak_prevalence"`` and ``"final_recovered"`` mentioned in earlier versions are computed manually from the time series data.

Extracting and Analyzing Measures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Run SIR simulation
    sir = SIRDynamics(network, beta=0.3, gamma=0.1, initial_infected=0.05)
    sir.set_seed(42)
    results = sir.run(steps=100)
    
    # Extract prevalence time series
    prevalence = results.get_measure("prevalence")
    print(f"Prevalence array shape: {prevalence.shape}")  # (101,) for 100 steps + initial
    
    # Compute summary statistics
    peak_prevalence = prevalence.max()
    peak_time = prevalence.argmax()
    final_prevalence = prevalence[-1]
    
    print(f"Peak prevalence: {peak_prevalence:.2%} at step {peak_time}")
    print(f"Final prevalence: {final_prevalence:.2%}")
    
    # Extract state counts
    state_counts = results.get_measure("state_counts")
    print(f"Available states: {list(state_counts.keys())}")
    
    # Compute attack rate (fraction ever infected)
    total_nodes = sum(state_counts[s][0] for s in state_counts.keys())  # Total at t=0
    attack_rate = state_counts['R'][-1] / total_nodes
    print(f"Attack rate: {attack_rate:.2%}")

Converting to pandas DataFrame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For further analysis with pandas:

.. code-block:: python

    import pandas as pd
    
    # Convert time series to DataFrame
    state_counts = results.get_measure("state_counts")
    df = pd.DataFrame({
        'time': range(len(state_counts['S'])),
        'S': state_counts['S'],
        'I': state_counts['I'],
        'R': state_counts['R']
    })
    
    # Compute prevalence column
    df['prevalence'] = df['I'] / (df['S'] + df['I'] + df['R'])
    
    # Analyze
    print(df.describe())
    print(f"\\nTime to peak: {df['prevalence'].idxmax()}")

Alternatively, use the built-in method:

.. code-block:: python

    # Convert trajectory to long-form DataFrame
    df = results.to_pandas()
    print(df.head())
    
    # Output:
    #    t  node state
    # 0  0     0     S
    # 1  0     1     S
    # 2  0     2     S
    # ...

Reproducible Experiments & Parameter Sweeps
--------------------------------------------

Running Multiple Stochastic Realizations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Epidemic dynamics are stochastic, so we often run multiple realizations and report summary statistics:

.. code-block:: python

    import numpy as np
    from py3plex.dynamics import SIRDynamics
    
    def run_sir_ensemble(network, beta, gamma, n_runs=50):
        """Run SIR simulation n_runs times with different seeds."""
        peak_prevalences = []
        attack_rates = []
        
        for seed in range(n_runs):
            sir = SIRDynamics(network, beta=beta, gamma=gamma, initial_infected=0.05)
            sir.set_seed(seed)
            results = sir.run(steps=100)
            
            prevalence = results.get_measure("prevalence")
            peak_prevalences.append(prevalence.max())
            
            state_counts = results.get_measure("state_counts")
            total = network.core_network.number_of_nodes()
            attack_rates.append(state_counts['R'][-1] / total)
        
        return {
            'peak_prevalence_mean': np.mean(peak_prevalences),
            'peak_prevalence_std': np.std(peak_prevalences),
            'attack_rate_mean': np.mean(attack_rates),
            'attack_rate_std': np.std(attack_rates),
        }
    
    # Run ensemble
    stats = run_sir_ensemble(network, beta=0.3, gamma=0.1, n_runs=50)
    print(f"Peak prevalence: {stats['peak_prevalence_mean']:.2%} ± {stats['peak_prevalence_std']:.2%}")
    print(f"Attack rate: {stats['attack_rate_mean']:.2%} ± {stats['attack_rate_std']:.2%}")

**Expected Output**

.. code-block:: text

    Peak prevalence: 34.85% ± 2.13%
    Attack rate: 98.60% ± 3.42%

*Note: Mean and std quantify variability across stochastic realizations.*

Parameter Grid Sweep
~~~~~~~~~~~~~~~~~~~~

To explore how outcomes depend on parameters, run a grid sweep:

.. code-block:: python

    import pandas as pd
    import networkx as nx
    
    # Use a standard network for reproducibility
    G = nx.karate_club_graph()
    
    # Parameter grid
    beta_values = [0.1, 0.2, 0.3, 0.4]
    gamma_values = [0.05, 0.1, 0.15, 0.2]
    
    # Run grid
    results_grid = []
    
    for beta in beta_values:
        for gamma in gamma_values:
            sir = SIRDynamics(G, beta=beta, gamma=gamma, initial_infected=0.1)
            sir.set_seed(42)
            result = sir.run(steps=100)
            
            prevalence = result.get_measure("prevalence")
            state_counts = result.get_measure("state_counts")
            
            results_grid.append({
                'beta': beta,
                'gamma': gamma,
                'R0_approx': beta / gamma * 4.6,  # <k> ≈ 4.6 for karate club
                'peak_prevalence': prevalence.max(),
                'peak_time': prevalence.argmax(),
                'attack_rate': state_counts['R'][-1] / G.number_of_nodes(),
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(results_grid)
    print(df)

**Expected Output** (partial)

.. code-block:: text

       beta  gamma  R0_approx  peak_prevalence  peak_time  attack_rate
    0   0.1   0.05        9.2            0.676          5        1.000
    1   0.1   0.10        4.6            0.382          6        0.971
    2   0.1   0.15        3.1            0.206          6        0.794
    3   0.1   0.20        2.3            0.088          7        0.500
    4   0.2   0.05       18.4            0.971          3        1.000
    5   0.2   0.10        9.2            0.882          4        1.000
    ...

You can visualize this data with heatmaps or line plots to identify parameter regimes for outbreak control.

Custom Dynamics
---------------

Extending BaseDynamics
~~~~~~~~~~~~~~~~~~~~~~~

To implement domain-specific dynamics, subclass ``DynamicsProcess`` and define:

1. ``initialize_state(self, seed=None)``: Return initial state
2. ``step(self, state, t)``: Update state for one time step
3. (Optional) Custom measure computation methods

**Contract**

* ``initialize_state`` must return a state object (dict, list, or custom)
* ``step`` must take the current state and return the new state
* Both methods can access ``self.graph``, ``self.rng``, and ``self.params``

Example: Threshold Model
~~~~~~~~~~~~~~~~~~~~~~~~~

We implement a simple threshold model where nodes adopt a binary opinion if enough neighbors have adopted:

.. code-block:: python

    from py3plex.dynamics.core import DynamicsProcess
    from py3plex.dynamics._utils import iter_multilayer_nodes, iter_multilayer_neighbors
    
    class ThresholdDynamics(DynamicsProcess):
        """Threshold model: nodes adopt state 1 if fraction of neighbors exceeds threshold."""
        
        def __init__(self, graph, seed=None, threshold=0.5, initial_adopters=0.1):
            super().__init__(graph, seed=seed)
            self.threshold = threshold
            self.initial_adopters = initial_adopters
        
        def initialize_state(self, seed=None):
            """Initialize with some nodes in state 1, rest in state 0."""
            rng = self.rng if seed is None else np.random.default_rng(seed)
            nodes = list(iter_multilayer_nodes(self.graph))
            
            # Randomly select initial adopters
            n_adopters = int(len(nodes) * self.initial_adopters)
            adopter_indices = rng.choice(len(nodes), size=n_adopters, replace=False)
            adopters = set(nodes[i] for i in adopter_indices)
            
            return {node: 1 if node in adopters else 0 for node in nodes}
        
        def step(self, state, t):
            """Update rule: adopt if fraction of neighbors >= threshold."""
            new_state = {}
            
            for node in state:
                if state[node] == 1:
                    # Already adopted, stay adopted
                    new_state[node] = 1
                else:
                    # Count adopting neighbors
                    neighbors = list(iter_multilayer_neighbors(self.graph, node))
                    if not neighbors:
                        new_state[node] = 0
                        continue
                    
                    adopting_neighbors = sum(1 for n in neighbors if state.get(n, 0) == 1)
                    fraction = adopting_neighbors / len(neighbors)
                    
                    # Adopt if threshold exceeded
                    new_state[node] = 1 if fraction >= self.threshold else 0
            
            return new_state
    
    # Run threshold model
    threshold = ThresholdDynamics(
        network,
        seed=42,
        threshold=0.3,
        initial_adopters=0.1
    )
    
    results = threshold.run(steps=50)
    
    # Count adoption over time
    adoption_counts = []
    for state in results.trajectory:
        adoption_counts.append(sum(state.values()))
    
    print(f"Initial adopters: {adoption_counts[0]}")
    print(f"Final adopters: {adoption_counts[-1]}")
    print(f"Adoption rate: {adoption_counts[-1] / network.core_network.number_of_nodes():.2%}")

**Expected Output**

.. code-block:: text

    Initial adopters: 4
    Final adopters: 40
    Adoption rate: 100.00%

*Note: With a low threshold (0.3), the initial adopters trigger a cascade where all nodes eventually adopt.*

Adding Custom Measures
~~~~~~~~~~~~~~~~~~~~~~~

To expose custom measures through ``.get_measure()``, override the ``compute_measure`` method:

.. code-block:: python

    class ThresholdDynamics(DynamicsProcess):
        # ... (same as above) ...
        
        def compute_measure(self, measure_name, trajectory):
            """Compute custom measures for threshold model."""
            if measure_name == "adoption_fraction":
                # Fraction of nodes in state 1 over time
                fractions = []
                for state in trajectory:
                    fractions.append(sum(state.values()) / len(state))
                return np.array(fractions)
            
            elif measure_name == "cascade_size":
                # Final number of adopters
                final_state = trajectory[-1]
                return sum(final_state.values())
            
            else:
                raise ValueError(f"Unknown measure: {measure_name}")
    
    # Now you can use:
    results = threshold.run(steps=50)
    adoption_frac = results.get_measure("adoption_fraction")
    cascade_size = results.get_measure("cascade_size")
    
    print(f"Cascade size: {cascade_size} nodes")

This pattern makes your custom dynamics consistent with built-in models.

Next Steps
----------

Now that you understand multilayer dynamics in py3plex, explore:

* **Visualization**: :doc:`visualize_networks` to plot epidemic curves and multilayer network states
* **Multilayer theory**: :doc:`../concepts/multilayer_networks_101` for formal background on multilayer structures
* **Advanced examples**: :doc:`../examples/index` for notebooks using SIR/SIS in complex scenarios
* **API reference**: :doc:`../reference/algorithm_reference` for full documentation of ``py3plex.dynamics``

**Typical research workflows:**

1. Design a multilayer network representing your system (social + physical, online + offline, etc.)
2. Choose or implement a dynamics model (epidemic, diffusion, opinion, etc.)
3. Run parameter sweeps to explore outbreak conditions or intervention strategies
4. Visualize trajectories and multilayer-specific statistics (per-layer prevalence, layer switching rates)
5. Compare scenarios to inform policy or design decisions

For more complex simulations (time-varying parameters, multi-stage interventions), consider using the high-level simulation builder API (``py3plex.dynamics.D``) or config-driven workflows (``build_dynamics_from_config``).
