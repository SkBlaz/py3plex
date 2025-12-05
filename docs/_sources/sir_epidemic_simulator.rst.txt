SIR Epidemic Simulator on Multiplex Graphs
===========================================

This module provides efficient, reproducible SIR (Susceptible-Infected-Recovered) epidemic simulators for multiplex networks (same node set, multiple edge layers).

Features
--------

- **Discrete-time simulation**: Step-based updates with configurable time step
- **Continuous-time simulation**: Gillespie algorithm for exact event-driven dynamics
- **Multiplex support**: Multiple interaction layers with per-layer transmission rates
- **Flexible parameterization**: Per-layer transmission rates, per-node recovery rates, layer weights
- **Exogenous importations**: Optional external infection sources
- **Rich outputs**: Incidence curves, event logs, per-layer attribution
- **Sparse linear algebra**: Efficient handling of large networks
- **Reproducible**: Seeded random number generation

Model Definition
----------------

States
~~~~~~

Each node has a single health state shared across all layers:

- **S (0)**: Susceptible
- **I (1)**: Infected
- **R (2)**: Recovered

Transmission
~~~~~~~~~~~~

- Infections occur along layer-specific edges with rate/probability β[α]
- Edge weights can represent contact multiplicity or strength
- Hazards from all layers combine:
  
  - **Continuous-time (Gillespie)**: Additive combination
  - **Discrete-time**: Independent-trial complement (1 - ∏ exp(-λ_α dt))

Recovery
~~~~~~~~

- Infected nodes recover at rate γ (scalar or per-node)
- Recovery is independent of network structure

Optional Features
~~~~~~~~~~~~~~~~~

- **Layer weights**: Scale transmission rates by layer importance
- **Time-varying parameters**: β(α, t) and γ(i, t) as callables
- **Exogenous infections**: Poisson import rate η(t)

Installation
------------

The SIR multiplex module is part of py3plex. Ensure you have the required dependencies:

.. code-block:: bash

    pip install numpy scipy

Or install py3plex with all dependencies:

.. code-block:: bash

    pip install py3plex

Quick Start
-----------

Discrete-Time Simulation
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import numpy as np
    import scipy.sparse
    from py3plex.algorithms.sir_multiplex import simulate_sir_multiplex_discrete

    # Create a simple ring network
    N = 20
    edges = [(i, (i+1) % N) for i in range(N)]
    row, col = zip(*edges)
    A = scipy.sparse.csr_matrix((np.ones(len(edges)), (row, col)), shape=(N, N))

    # Run simulation
    result = simulate_sir_multiplex_discrete(
        A_layers=[A],
        beta=0.5,          # Transmission rate
        gamma=0.2,         # Recovery rate
        dt=0.5,            # Time step
        steps=100,         # Number of steps
        rng_seed=42        # For reproducibility
    )

    # Access results
    print(f"Peak prevalence: {result.I.max()} at time {result.times[result.I.argmax()]}")
    print(f"Final attack rate: {result.R[-1] / N:.2%}")

Continuous-Time (Gillespie) Simulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.sir_multiplex import simulate_sir_multiplex_gillespie

    result = simulate_sir_multiplex_gillespie(
        A_layers=[A],
        beta=0.5,
        gamma=0.2,
        t_max=100.0,       # Maximum time
        rng_seed=42,
        return_event_log=True  # Get detailed event log
    )

    # Examine events
    for t, event_type, node_id, layer in result.events[:10]:
        print(f"t={t:.2f}: {event_type} at node {node_id}")

Multiplex Network Example
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Create two-layer network: physical contact + online interaction
    N = 50

    # Layer 1: Physical proximity (localized)
    edges_physical = [(i, (i+1) % N) for i in range(N)]
    row, col = zip(*edges_physical)
    A_physical = scipy.sparse.csr_matrix((np.ones(len(edges_physical)), (row, col)), shape=(N, N))

    # Layer 2: Online network (more random)
    np.random.seed(42)
    edges_online = [(i, j) for i in range(N) for j in range(N) 
                    if i != j and np.random.random() < 0.1]
    row, col = zip(*edges_online) if edges_online else ([], [])
    data = np.ones(len(edges_online)) if edges_online else []
    A_online = scipy.sparse.csr_matrix((data, (row, col)), shape=(N, N))

    # Simulate with different transmission rates per layer
    result = simulate_sir_multiplex_discrete(
        A_layers=[A_physical, A_online],
        beta=np.array([0.3, 0.1]),  # Higher transmission in physical layer
        gamma=0.15,
        layer_weights=np.array([1.0, 0.5]),  # Weight online layer less
        dt=0.5,
        steps=200,
        rng_seed=123,
        return_layer_incidence=True  # Track which layer caused infections
    )

    # Analyze layer contributions
    from py3plex.algorithms.sir_multiplex import summarize
    summary = summarize(result)
    print(f"Layer contributions: {summary['layer_contributions']}")

API Reference
-------------

simulate_sir_multiplex_discrete
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Discrete-time SIR simulation with synchronous updates.

**Parameters:**

- ``A_layers`` (list[csr_matrix]): List of L sparse adjacency matrices (N×N)
- ``beta`` (float | ndarray): Transmission rate (scalar or length L array)
- ``gamma`` (float | ndarray): Recovery rate (scalar or length N array)
- ``layer_weights`` (ndarray, optional): Layer importance weights (length L)
- ``dt`` (float): Time step size (default: 1.0)
- ``steps`` (int): Number of simulation steps (default: 100)
- ``initial_state`` (ndarray, optional): Initial state array with values {0,1,2}
- ``initial_infected`` (ndarray, optional): Boolean mask for initially infected nodes
- ``import_rate`` (float | callable): Exogenous infection rate (default: 0.0)
- ``rng_seed`` (int): Random seed (default: 0)
- ``return_event_log`` (bool): Return event log (default: False)
- ``return_layer_incidence`` (bool): Return per-layer infections (default: False)

**Returns:** ``EpidemicResult`` object

simulate_sir_multiplex_gillespie
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Continuous-time SIR simulation using Gillespie algorithm.

**Parameters:** Same as discrete, except:

- ``t_max`` (float): Maximum simulation time instead of ``dt`` and ``steps``
- ``return_event_log`` (bool): Default is True

**Returns:** ``EpidemicResult`` object

EpidemicResult
~~~~~~~~~~~~~~

Dataclass containing simulation results:

- ``times`` (ndarray): Time points
- ``S``, ``I``, ``R`` (ndarray): Counts of each state over time
- ``states`` (ndarray, optional): Full state history (discrete only)
- ``incidence_by_layer`` (ndarray, optional): Infections per layer over time
- ``events`` (list, optional): Event log with tuples (time, type, node, layer)
- ``meta`` (dict): Simulation metadata

basic_reproduction_number
~~~~~~~~~~~~~~~~~~~~~~~~~~

Compute approximate R₀ using spectral radius.

.. code-block:: python

    R0 = basic_reproduction_number(A_layers, beta, gamma, layer_weights=None)

For homogeneous networks with uniform recovery rate γ:

.. math::

    R_0 \approx \rho\left(\sum_\alpha \frac{\beta_\alpha w_\alpha}{\gamma} A^{(\alpha)}\right)

summarize
~~~~~~~~~

Extract summary statistics from simulation results.

.. code-block:: python

    summary = summarize(result)

Returns dictionary with:

- ``peak_prevalence``: Maximum infected count
- ``peak_time``: Time of peak
- ``attack_rate``: Final proportion recovered
- ``time_to_extinction``: When infections reached zero
- ``total_infections``: Total recovered at end
- ``layer_contributions``: Proportion of infections per layer
- ``duration``: Total simulation time

Update Rules
------------

Discrete-Time
~~~~~~~~~~~~~

For each time step t → t + dt:

1. **Infection probability** for susceptible node i:

   .. math::

       \lambda_{i,\alpha}(t) = \beta_\alpha w_\alpha \sum_j A^{(\alpha)}_{ji} \mathbb{1}\{X_j = I\}

       p_i(t) = 1 - \prod_\alpha \exp(-\lambda_{i,\alpha}(t) \, dt)

2. **Recovery probability** for infected node i:

   .. math::

       p_{\text{rec}}(i) = 1 - \exp(-\gamma_i \, dt)

3. **Synchronous update**: Compute all probabilities from state at t, then apply changes

Continuous-Time (Gillespie)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Compute total event rate:

   .. math::

       \Lambda = \sum_{i \in S} \sum_\alpha \lambda_{i,\alpha} + \sum_{i \in I} \gamma_i + \eta|S|

2. Sample time to next event: :math:`\Delta t \sim \text{Exp}(\Lambda)`

3. Select event type proportionally to rates

4. Update state and incrementally adjust affected rates

5. Record event and repeat until :math:`t > t_{\text{max}}` or no infected remain

Units and Conventions
---------------------

- **Time**: Arbitrary units (days, hours, etc.). Ensure β, γ, dt/t_max are in same units.
- **Rates**: Events per time unit. β = 0.5 per day means average 0.5 transmissions per infected-susceptible contact per day.
- **Probabilities**: For discrete-time, computed as 1 - exp(-rate × dt)
- **Edge weights**: Scale transmission. Weight 2.0 doubles effective contact rate.

Performance Tips
----------------

- Use sparse matrices (CSR format) for all adjacency matrices
- For large networks (N > 10⁴), use smaller time steps or t_max
- Disable event logs for very long simulations to save memory
- Vectorized operations are used internally for efficiency

Examples
--------

See ``examples/advanced/example_sir_multiplex.py`` for additional examples including:

- Comparison of discrete vs continuous time
- Effect of network structure on epidemic spread
- Multi-layer network analysis
- Parameter sensitivity studies

References
----------

- Gillespie, D. T. (1977). Exact stochastic simulation of coupled chemical reactions. *Journal of Physical Chemistry*, 81(25), 2340-2361.
- Keeling, M. J., & Rohani, P. (2008). *Modeling infectious diseases in humans and animals*. Princeton University Press.
- De Domenico, M., et al. (2013). Mathematical formulation of multilayer networks. *Physical Review X*, 3(4), 041022.

Citation
--------

If you use this simulator in your research, please cite py3plex:

.. code-block:: bibtex

    @software{py3plex,
      author = {Škrlj, Blaž},
      title = {Py3plex: A library for analysis and visualization of heterogeneous networks},
      url = {https://github.com/SkBlaz/py3plex},
      year = {2023}
    }
