Multilayer Dynamics
===================

Consider a disease spreading through a community where people interact both in-person (physical layer) and online (digital layer). An individual infected in person can spread to their physical contacts, but awareness spread online might change behavior and reduce transmission. **Multilayer dynamics** simulates these coupled processes across interaction types.

.. admonition::  DSL for Dynamics
   :class: dsl-example

   Run dynamics simulations declaratively with the DSL:

   .. code-block:: python

       from py3plex.dynamics import D, SIS

       # Define and run SIS simulation
       sim = (
           D.process(SIS(beta=0.3, mu=0.1))
            .initial(infected=0.05)
            .steps(100)
            .measure("prevalence")
            .seed(42)
       )
       
       result = sim.run(network)
       print(f"Peak prevalence: {result.data['prevalence'].max():.2%}")

   See :doc:`dsl` for complete dynamics DSL documentation!

----

This chapter shows you how to:

- Simulate **epidemic dynamics** (SIR, SIS) on multilayer networks
- Run **random walks** and analyze exploration patterns
- Configure **initial conditions** and **parameters**
- Extract and visualize **simulation results**
- Understand how **layer structure affects dynamics**

py3plex provides a clean, object-oriented API for dynamics that integrates seamlessly with the rest of the library.

----

Overview of Dynamics Models
----------------------------

py3plex supports three main classes of dynamics:

**Epidemic Models**

- **SIR (Susceptible-Infected-Recovered)** — Models diseases with lasting immunity (measles, chickenpox)
- **SIS (Susceptible-Infected-Susceptible)** — Models diseases without immunity (common cold, computer viruses)

**Diffusion Processes**

- **Random Walk** — Models exploration, search, and diffusion on networks

All models support:

-  **Multilayer networks** — Different interaction contexts (physical, digital, etc.)
-  **Reproducible simulations** — Seeded random number generation
-  **Rich output measures** — Prevalence, state counts, trajectories
-  **Clean API** — Object-oriented design aligned with best practices

----

SIR Epidemic Dynamics
----------------------

The **SIR model** simulates epidemic spread where infected individuals recover with lasting immunity. This is appropriate for many infectious diseases and for modeling information spread where people don't "forget" what they've learned.

**States:**

- **S (Susceptible)** — Not infected, can become infected
- **I (Infected)** — Currently infected, can transmit to susceptibles
- **R (Recovered)** — Recovered with immunity, cannot be re-infected

**Parameters:**

- ``beta`` (:math:`\beta \in (0, 1)`) — Transmission probability per contact per time step
- ``gamma`` (:math:`\gamma \in (0, 1)`) — Recovery probability per time step
- ``initial_infected`` — Fraction or number of initially infected nodes

Basic Example
~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.dynamics import SIRDynamics
    import networkx as nx

    # Create a network
    G = nx.karate_club_graph()

    # Create SIR dynamics
    sir = SIRDynamics(
        G,
        beta=0.3,              # Infection probability
        gamma=0.1,             # Recovery probability
        initial_infected=0.1   # 10% initially infected
    )

    # Set seed for reproducibility
    sir.set_seed(42)

    # Run simulation
    results = sir.run(steps=100)

    # Extract measures
    prevalence = results.get_measure("prevalence")
    state_counts = results.get_measure("state_counts")

    print(f"Peak prevalence: {prevalence.max():.2%}")
    print(f"Final recovered: {state_counts['R'][-1]}")

**Example Output:**

.. code-block:: text

    Peak prevalence: 35.29%
    Final recovered: 30

The epidemic infects about 88% of the network before dying out naturally.

Multilayer SIR Example
~~~~~~~~~~~~~~~~~~~~~~

On multilayer networks, infection can spread through different interaction contexts:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dynamics import SIRDynamics

    # Create two-layer network
    network = multinet.multi_layer_network(directed=False)

    # Add nodes to two layers
    for i in range(20):
        network.add_nodes([
            {'source': i, 'type': 'physical'},
            {'source': i, 'type': 'digital'}
        ])

    # Physical layer: local ring connections
    for i in range(20):
        network.add_edges([{
            'source': i, 'target': (i+1) % 20,
            'source_type': 'physical', 'target_type': 'physical'
        }])

    # Digital layer: random connections (more global)
    import numpy as np
    rng = np.random.default_rng(42)
    for _ in range(30):
        i, j = rng.integers(0, 20), rng.integers(0, 20)
        if i != j:
            network.add_edges([{
                'source': i, 'target': j,
                'source_type': 'digital', 'target_type': 'digital'
            }])

    # Run SIR dynamics
    sir = SIRDynamics(network, beta=0.3, gamma=0.1)
    sir.set_seed(42)
    results = sir.run(steps=100)

    # Analyze results
    prevalence = results.get_measure("prevalence")
    state_counts = results.get_measure("state_counts")

    print(f"Peak prevalence: {prevalence.max():.2%} at step {prevalence.argmax()}")
    print(f"Attack rate: {state_counts['R'][-1] / 40:.2%}")

**Example Output:**

.. code-block:: text

    Peak prevalence: 30.00% at step 10
    Attack rate: 55.00%

The multilayer structure allows faster spread through the digital layer while maintaining local spread through physical contacts.

Understanding SIR Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **basic reproduction number** :math:`R_0` determines epidemic outcome:

.. math::

    R_0 = \frac{\beta}{\gamma} \langle k \rangle

where :math:`\langle k \rangle` is the average degree.

- **R₀ > 1**: Epidemic spreads (each infected person infects >1 others on average)
- **R₀ < 1**: Epidemic dies out quickly
- **R₀ = 1**: Epidemic threshold — critical point

**Parameter Effects:**

.. code-block:: python

    # Compare different parameters
    import matplotlib.pyplot as plt

    G = nx.karate_club_graph()
    
    params = [
        {'beta': 0.2, 'gamma': 0.1, 'label': 'Low transmission (R₀≈9)'},
        {'beta': 0.4, 'gamma': 0.1, 'label': 'High transmission (R₀≈18)'},
        {'beta': 0.3, 'gamma': 0.05, 'label': 'Slow recovery'},
        {'beta': 0.3, 'gamma': 0.2, 'label': 'Fast recovery'},
    ]
    
    plt.figure(figsize=(10, 6))
    
    for p in params:
        sir = SIRDynamics(G, beta=p['beta'], gamma=p['gamma'], 
                         initial_infected=0.1)
        sir.set_seed(42)
        results = sir.run(steps=50)
        prevalence = results.get_measure("prevalence")
        plt.plot(prevalence, label=p['label'], linewidth=2)
    
    plt.xlabel('Time step')
    plt.ylabel('Prevalence (fraction infected)')
    plt.title('SIR Dynamics with Different Parameters')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

**Output Characteristics:**

- **Higher β**: Faster, higher peak, larger attack rate
- **Higher γ**: Faster recovery, lower peak, smaller attack rate
- **Slow recovery**: Epidemic lasts longer, more sustained infections

----

SIS Epidemic Dynamics
----------------------

The **SIS model** simulates diseases without lasting immunity — individuals recover but can be immediately re-infected. This creates an **endemic equilibrium** where infection persists indefinitely (unlike SIR which always dies out).

**States:**

- **S (Susceptible)** — Not infected, can become infected
- **I (Infected)** — Currently infected, can transmit and recover

**No recovered state** — recovered individuals return to susceptible.

**Parameters:**

- ``beta`` (:math:`\beta \in (0, 1)`) — Transmission probability per contact
- ``gamma`` (:math:`\gamma \in (0, 1)`) — Recovery probability per time step (also denoted ``mu`` for SIS)
- ``initial_infected`` — Fraction or number initially infected

Basic Example
~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.dynamics import SISDynamics
    import networkx as nx

    # Create a small-world network
    G = nx.watts_strogatz_graph(n=100, k=6, p=0.1, seed=42)

    # Create SIS dynamics
    sis = SISDynamics(
        G,
        beta=0.3,      # Infection rate
        gamma=0.1,     # Recovery rate
        initial_infected=0.05
    )

    # Set seed and run
    sis.set_seed(42)
    results = sis.run(steps=200)

    # Extract measures
    prevalence = results.get_measure("prevalence")
    
    # Endemic equilibrium (mean of last 50 steps)
    endemic_level = prevalence[-50:].mean()
    
    print(f"Endemic prevalence: {endemic_level:.2%}")
    print(f"Std deviation: {prevalence[-50:].std():.2%}")

**Example Output:**

.. code-block:: text

    Endemic prevalence: 89.48%
    Std deviation: 2.77%

The infection reaches a **stable endemic state** where it persists indefinitely, unlike SIR.

SIS vs SIR Comparison
~~~~~~~~~~~~~~~~~~~~~

The key difference: **SIS sustains infection, SIR dies out**:

.. code-block:: python

    from py3plex.dynamics import SISDynamics, SIRDynamics
    import networkx as nx
    import matplotlib.pyplot as plt

    G = nx.karate_club_graph()

    # SIS dynamics
    sis = SISDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
    sis.set_seed(42)
    sis_results = sis.run(steps=100)
    sis_prevalence = sis_results.get_measure("prevalence")

    # SIR dynamics
    sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
    sir.set_seed(42)
    sir_results = sir.run(steps=100)
    sir_prevalence = sir_results.get_measure("prevalence")

    # Plot comparison
    plt.figure(figsize=(10, 6))
    plt.plot(sis_prevalence, label='SIS (no immunity)', 
             color='red', linewidth=2)
    plt.plot(sir_prevalence, label='SIR (with immunity)', 
             color='blue', linewidth=2)
    plt.xlabel('Time step')
    plt.ylabel('Prevalence')
    plt.title('SIS vs SIR Epidemic Dynamics')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

**Output Characteristics:**

- **SIS**: Initial outbreak → settles to endemic equilibrium → persists indefinitely
- **SIR**: Initial outbreak → peak → gradual decline → complete extinction

Endemic Threshold
~~~~~~~~~~~~~~~~~

SIS has an **epidemic threshold** below which infection dies out:

.. code-block:: python

    G = nx.karate_club_graph()
    avg_degree = 2 * G.number_of_edges() / G.number_of_nodes()
    
    gamma = 0.1
    beta_values = [0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3]
    
    for beta in beta_values:
        sis = SISDynamics(G, beta=beta, gamma=gamma, initial_infected=0.1)
        sis.set_seed(42)
        results = sis.run(steps=200)
        prevalence = results.get_measure("prevalence")
        
        # Endemic level (mean of last 50 steps)
        endemic = prevalence[-50:].mean()
        R0 = beta / gamma * avg_degree
        status = "endemic" if endemic > 0.01 else "extinct"
        
        print(f"β={beta:.2f}, R₀={R0:.2f}: {endemic:.2%} ({status})")

**Example Output:**

.. code-block:: text

    β=0.01, R₀=0.46: 0.00% (extinct)
    β=0.02, R₀=0.92: 0.00% (extinct)
    β=0.03, R₀=1.38: 27.35% (endemic)
    β=0.05, R₀=2.29: 56.41% (endemic)
    β=0.10, R₀=4.59: 75.00% (endemic)
    β=0.20, R₀=9.18: 83.06% (endemic)
    β=0.30, R₀=13.76: 86.24% (endemic)

**Threshold occurs at R₀ ≈ 1** (between β=0.02 and β=0.03 in this network).

----

Random Walk Dynamics
---------------------

Random walks simulate **exploration** and **diffusion** on networks. At each step, a walker moves to a random neighbor (or stays in place with some probability).

**Use cases:**

- Computing **PageRank** and other centrality measures
- Modeling **search** and **navigation**  
- Analyzing **community structure** through exploration patterns
- Understanding **information diffusion**

Basic Example
~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.dynamics import RandomWalkDynamics
    import networkx as nx

    # Create network
    G = nx.karate_club_graph()

    # Create random walk starting at node 0
    walk = RandomWalkDynamics(
        G,
        start_node=0,
        lazy_probability=0.1  # 10% chance to stay in place
    )

    # Set seed and run
    walk.set_seed(42)
    results = walk.run(steps=1000)

    # Get trajectory
    trajectory = results.get_measure("trajectory")

    print(f"Walk length: {len(trajectory)}")
    print(f"Start: {trajectory[0]}, End: {trajectory[-1]}")
    
    # Count visits
    from collections import Counter
    visits = Counter(trajectory)
    top_5 = visits.most_common(5)
    
    print(f"Most visited nodes:")
    for node, count in top_5:
        print(f"  Node {node}: {count} visits")

**Example Output:**

.. code-block:: text

    Walk length: 1001
    Start: 0, End: 2
    Most visited nodes:
      Node 33: 87 visits
      Node 0: 76 visits
      Node 2: 64 visits
      Node 1: 58 visits
      Node 32: 51 visits

High-degree nodes (hubs) get visited more frequently due to more incoming edges.

Multilayer Random Walk
~~~~~~~~~~~~~~~~~~~~~~

Random walks on multilayer networks can **switch between layers** at inter-layer connections:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dynamics import RandomWalkDynamics

    # Create two-layer network with different structures
    network = multinet.multi_layer_network(directed=False)

    n = 15
    nodes = []
    for i in range(n):
        nodes.append({'source': i, 'type': 'ring'})
        nodes.append({'source': i, 'type': 'star'})
    network.add_nodes(nodes)

    # Layer 1: Ring topology
    for i in range(n):
        network.add_edges([{
            'source': i, 'target': (i+1) % n,
            'source_type': 'ring', 'target_type': 'ring'
        }])

    # Layer 2: Star topology (node 0 is hub)
    for i in range(1, n):
        network.add_edges([{
            'source': 0, 'target': i,
            'source_type': 'star', 'target_type': 'star'
        }])

    # Inter-layer connections
    for i in range(n):
        network.add_edges([{
            'source': i, 'target': i,
            'source_type': 'ring', 'target_type': 'star'
        }])

    # Run random walk
    walk = RandomWalkDynamics(network, start_node=(0, 'ring'))
    walk.set_seed(42)
    results = walk.run(steps=1000)
    trajectory = results.get_measure("trajectory")

    # Analyze layer switching
    switches = 0
    for i in range(len(trajectory) - 1):
        if trajectory[i][1] != trajectory[i+1][1]:
            switches += 1

    print(f"Layer switches: {switches}")
    print(f"Switch rate: {switches / len(trajectory):.2%}")

**Example Output:**

.. code-block:: text

    Layer switches: 348
    Switch rate: 34.77%

The walker frequently moves between layers, exploring both network structures.

Lazy Random Walks
~~~~~~~~~~~~~~~~~

The **lazy probability** controls how often the walker stays in place:

.. code-block:: python

    import networkx as nx
    import matplotlib.pyplot as plt

    G = nx.path_graph(20)  # Simple chain
    
    lazy_probs = [0.0, 0.2, 0.5, 0.8]
    
    plt.figure(figsize=(10, 6))
    
    for lazy_p in lazy_probs:
        walk = RandomWalkDynamics(G, start_node=10, 
                                  lazy_probability=lazy_p)
        walk.set_seed(42)
        results = walk.run(steps=100)
        trajectory = results.get_measure("trajectory")
        
        plt.plot(trajectory, label=f'Lazy p={lazy_p}', 
                linewidth=2, alpha=0.7)
    
    plt.xlabel('Time step')
    plt.ylabel('Node position')
    plt.title('Random Walk with Different Lazy Probabilities')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()

**Output Characteristics:**

- **lazy_p = 0.0**: Active walk, explores quickly
- **lazy_p = 0.5**: Balanced, moderate exploration
- **lazy_p = 0.8**: Mostly stationary, slow exploration

Higher lazy probability → slower diffusion, more time at current location.

----

Working with Results
--------------------

All dynamics simulations return a ``DynamicsResult`` object with rich output measures.

Available Measures
~~~~~~~~~~~~~~~~~~

**Epidemic Models (SIR, SIS):**

- ``"prevalence"`` — Fraction of nodes infected at each time step (array)
- ``"state_counts"`` — Count of nodes in each state over time (dict of arrays)
- ``"trajectory"`` — Full state history (list of dicts mapping node → state)

**Random Walk:**

- ``"trajectory"`` — Sequence of visited nodes (list)

Extracting Measures
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Run simulation
    sir = SIRDynamics(G, beta=0.3, gamma=0.1)
    sir.set_seed(42)
    results = sir.run(steps=100)

    # Get prevalence over time
    prevalence = results.get_measure("prevalence")
    
    # Get state counts
    state_counts = results.get_measure("state_counts")
    S = state_counts['S']  # Susceptible over time
    I = state_counts['I']  # Infected over time
    R = state_counts['R']  # Recovered over time

    # Get full trajectory (memory intensive for large networks)
    trajectory = results.get_measure("trajectory")
    # trajectory[t] is dict: {node: state} at time t

Converting to Pandas
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Convert to pandas DataFrame
    df_dict = results.to_pandas()
    
    # For epidemic models, returns dict of DataFrames
    prevalence_df = df_dict['prevalence']
    state_counts_df = df_dict['state_counts']
    
    # Export to CSV
    prevalence_df.to_csv("prevalence.csv")
    state_counts_df.to_csv("state_counts.csv")

Visualization
~~~~~~~~~~~~~

.. code-block:: python

    import matplotlib.pyplot as plt

    # Run SIR simulation
    sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
    sir.set_seed(42)
    results = sir.run(steps=100)

    prevalence = results.get_measure("prevalence")
    state_counts = results.get_measure("state_counts")

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Plot state counts
    steps = range(len(state_counts['S']))
    ax1.plot(steps, state_counts['S'], label='Susceptible', 
            color='blue', linewidth=2)
    ax1.plot(steps, state_counts['I'], label='Infected', 
            color='red', linewidth=2)
    ax1.plot(steps, state_counts['R'], label='Recovered', 
            color='green', linewidth=2)
    ax1.set_xlabel('Time step')
    ax1.set_ylabel('Number of nodes')
    ax1.set_title('SIR Epidemic Dynamics')
    ax1.legend()
    ax1.grid(alpha=0.3)

    # Plot prevalence
    ax2.plot(steps, prevalence, color='red', linewidth=2)
    ax2.fill_between(steps, 0, prevalence, alpha=0.3, color='red')
    ax2.set_xlabel('Time step')
    ax2.set_ylabel('Prevalence (fraction infected)')
    ax2.set_title('Infection Prevalence Over Time')
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

This produces publication-ready epidemic curves showing the full dynamics.

----

Mathematical Formalism
----------------------

SIR Model
~~~~~~~~~

**Discrete-time update rules** (per time step):

For each susceptible node *i*:

.. math::

    P(S_i \\rightarrow I_i) = 1 - \\prod_{j \\in N(i)} (1 - \\beta)^{\\mathbb{1}_{I_j}}

where :math:`N(i)` are neighbors and :math:`\\mathbb{1}_{I_j}` indicates if neighbor *j* is infected.

For each infected node *i*:

.. math::

    P(I_i \\rightarrow R_i) = \\gamma

**Continuous-time interpretation:**

Transition rates: :math:`S \\xrightarrow{\\beta \\lambda_i} I \\xrightarrow{\\gamma} R`

where :math:`\\lambda_i = \\sum_{j \\in N(i)} \\mathbb{1}_{I_j}` is the number of infected neighbors.

SIS Model
~~~~~~~~~

**Discrete-time update rules:**

Same infection rule as SIR, but recovery returns to susceptible:

.. math::

    P(I_i \\rightarrow S_i) = \\gamma

**Endemic equilibrium** (mean-field approximation):

.. math::

    \\rho^* = 1 - \\frac{\\gamma}{\\beta \\langle k \\rangle}

where :math:`\\rho^*` is endemic prevalence and :math:`\\langle k \\rangle` is average degree.

Random Walk
~~~~~~~~~~~

**Transition probability** from node *i* to node *j*:

.. math::

    P(i \\rightarrow j) = 
    \\begin{cases}
    p_{\\text{lazy}} & \\text{if } j = i \\\\
    \\frac{1 - p_{\\text{lazy}}}{\\text{degree}(i)} & \\text{if } j \\in N(i) \\\\
    0 & \\text{otherwise}
    \\end{cases}

**Stationary distribution** (long-run proportion of time at each node):

.. math::

    \\pi_i \\propto \\text{degree}(i)

High-degree nodes are visited more frequently.

----

Advanced Topics
---------------

Multilayer Coupling
~~~~~~~~~~~~~~~~~~~

In multilayer networks, nodes can have **different infection states in different layers** (weak coupling) or **share a single state across all layers** (strong coupling).

py3plex uses **strong coupling by default** — each node has one state shared across all its layer-specific replicas. This is appropriate for most epidemic models (a person is either infected or not, regardless of which social context you observe them in).

.. code-block:: python

    # Strong coupling (default): node state shared across layers
    sir = SIRDynamics(multilayer_network, beta=0.3, gamma=0.1)
    
    # Infection can spread through any layer
    # Recovery is per-node, not per-layer

Time-Varying Parameters
~~~~~~~~~~~~~~~~~~~~~~~~

Parameters can be **functions of time** for more realistic models:

.. code-block:: python

    # Seasonal variation in transmission
    def seasonal_beta(t):
        import math
        return 0.3 * (1 + 0.5 * math.sin(2 * math.pi * t / 365))
    
    # Note: Advanced feature, check core module support
    # sir = SIRDynamics(G, beta=seasonal_beta, gamma=0.1)

Heterogeneous Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~

Different nodes can have different recovery rates:

.. code-block:: python

    import numpy as np
    
    # Assign random recovery rates
    n_nodes = G.number_of_nodes()
    recovery_rates = np.random.uniform(0.05, 0.15, n_nodes)
    
    # Note: Advanced feature, check core module support
    # sir = SIRDynamics(G, beta=0.3, gamma=recovery_rates)

----

Performance Considerations
---------------------------

**Simulation speed** depends on:

- **Network size**: Larger networks take longer
- **Number of steps**: More steps = more computation
- **Trajectory storage**: Storing full state history uses memory

**Tips for efficiency:**

.. code-block:: python

    # For large networks, avoid storing full trajectory
    results = sir.run(steps=100)
    
    # Only extract measures you need
    prevalence = results.get_measure("prevalence")  # Lightweight
    # trajectory = results.get_measure("trajectory")  # Heavy for large networks

    # Use moderate step counts for exploration
    # Refine with more steps once parameters are tuned

**Typical performance** (on modern laptop):

- Network with 1000 nodes, 100 steps: ~1 second
- Network with 10,000 nodes, 100 steps: ~10 seconds
- Network with 100,000 nodes, 100 steps: ~2 minutes

----

DSL Integration
---------------

The dynamics module integrates with py3plex's :doc:`dsl` to provide declarative simulation syntax. The dynamics builder API follows the same philosophy as the network query DSL: chainable method calls that construct a simulation specification before execution.

**How Dynamics DSL Aligns with Query DSL:**

* **Same Builder Pattern**: Both use ``D.process()`` and ``Q.nodes()`` as entry points that return builder objects
* **Chainable Configuration**: Methods like ``.steps()``, ``.measure()``, and ``.seed()`` mirror ``.where()``, ``.compute()``, and ``.limit()``
* **Lazy Execution**: Both builders construct a specification; execution happens when you call ``.run()`` or ``.execute()``
* **Clean Separation**: Configuration (what to simulate/query) is separate from execution (running the simulation/query)

See :doc:`dsl` for the complete query DSL documentation, which shares these design principles.

**Example:**

.. code-block:: python

    from py3plex.dynamics import D, SIS, SIR, RandomWalk

    # Define simulation
    sim = (
        D.process(SIS(beta=0.3, mu=0.1))
         .initial(infected=0.05)
         .steps(100)
         .measure("prevalence", "incidence")
         .replicates(10)  # Run 10 independent trials
         .seed(42)
    )

    # Execute
    result = sim.run(network)

    # Aggregate across replicates
    mean_prevalence = result.data['prevalence'].mean(axis=0)
    std_prevalence = result.data['prevalence'].std(axis=0)

**See also:**

- :doc:`dsl` — Complete network query DSL documentation with builder API details
- `DSL documentation <dsl.html>`_ — Advanced dynamics DSL with mathematical formalism

----

Examples and Tutorials
----------------------

**Working examples** in ``examples/dynamics/``:

- ``sir_epidemic.py`` — Complete SIR epidemic simulation with multilayer networks and parameter comparison
- ``sis_dynamics.py`` — SIS dynamics, endemic equilibrium, threshold analysis
- ``random_walk.py`` — Random walks on multilayer networks, layer switching, hitting times

**Run an example:**

.. code-block:: bash

    python examples/dynamics/sir_epidemic.py

**Additional resources:**

- ``examples/network_analysis/example_dsl_dynamics.py`` — Dynamics using DSL
- :doc:`../sir_epidemic_simulator` — Detailed SIR epidemic documentation

----

Key Takeaways
-------------

 **Three dynamics models**: SIR (with immunity), SIS (without immunity), RandomWalk (diffusion)

 **Clean API**: ``DynamicsClass(network, params).set_seed(seed).run(steps)``

 **Rich outputs**: Prevalence, state counts, trajectories via ``results.get_measure()``

 **Multilayer support**: Dynamics spread through multiple interaction contexts

 **Reproducible**: Always use ``.set_seed()`` for deterministic results

 **Tunable parameters**: Adjust β, γ to model different scenarios

 **Visualization ready**: Extract numpy arrays or pandas DataFrames for plotting

----

Next Steps
----------

- **Experiment with parameters**: How does R₀ affect your specific network?
- **Compare layer effects**: Run dynamics on single layers vs full multilayer network
- **Analyze real data**: Apply to your domain (social networks, biological systems, etc.)
- **Combine with DSL**: Use declarative syntax for complex workflows
- **Read formalism**: See book chapters for mathematical foundations

**Related documentation:**

- :doc:`dsl` — Query and dynamics DSL
- :doc:`statistics` — Network statistics and measures
- :doc:`community_detection` — Finding communities
- :doc:`visualization` — Plotting networks and results
