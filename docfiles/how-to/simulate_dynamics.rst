How to Simulate Multilayer Dynamics
====================================

**Goal:** Model epidemic spread, diffusion processes, and other dynamic phenomena on multilayer networks.

**Prerequisites:** A loaded network (see :doc:`load_and_build_networks`).

SIR Epidemic Model
------------------

Simulate disease spread with Susceptible-Infected-Recovered dynamics:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dynamics import SIRDynamics
    
    # Create network
    network = multinet.multi_layer_network()
    network.load_network("data.multiedgelist", input_type="multiedgelist")
    
    # Configure SIR model
    sir = SIRDynamics(
        network,
        beta=0.3,    # Infection rate
        gamma=0.1,   # Recovery rate
        initial_infected=5  # Number of initially infected nodes
    )
    
    # Run simulation
    sir.set_seed(42)
    results = sir.run(steps=100)
    
    # View results
    print(f"Peak prevalence: {results.get_measure('peak_prevalence'):.2%}")
    print(f"Final recovered: {results.get_measure('final_recovered'):.2%}")

**Expected output:**

.. code-block:: text

    Peak prevalence: 35.29%
    Final recovered: 87.45%

SIS Epidemic Model
------------------

Susceptible-Infected-Susceptible model (no permanent immunity):

.. code-block:: python

    from py3plex.dynamics import SISDynamics
    
    # Configure SIS model
    sis = SISDynamics(
        network,
        beta=0.3,    # Infection rate
        gamma=0.1,   # Recovery rate
        initial_infected=5
    )
    
    # Run simulation
    sis.set_seed(42)
    results = sis.run(steps=200)
    
    # Check endemic prevalence
    endemic = results.get_measure('endemic_prevalence')
    print(f"Endemic prevalence: {endemic:.2%}")

**Expected output:**

.. code-block:: text

    Endemic prevalence: 23.18%

Random Walk Dynamics
--------------------

Simulate random walks on the multilayer network:

.. code-block:: python

    from py3plex.dynamics import RandomWalkDynamics
    
    # Configure random walk
    rw = RandomWalkDynamics(
        network,
        start_node=('Alice', 'friends'),
        walk_length=1000
    )
    
    # Run simulation
    rw.set_seed(42)
    results = rw.run(steps=1000)
    
    # Analyze visited nodes
    visit_counts = results.get_measure('visit_counts')
    
    # Most visited nodes
    sorted_visits = sorted(
        visit_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    print("Most visited nodes:")
    for node, count in sorted_visits[:10]:
        print(f"{node}: {count} visits")

Layer-Specific Transmission Rates
----------------------------------

Set different infection rates per layer:

.. code-block:: python

    from py3plex.dynamics import SIRDynamics
    
    # Define layer-specific rates
    layer_rates = {
        'household': 0.5,   # High transmission
        'workplace': 0.2,   # Medium transmission
        'social': 0.1       # Low transmission
    }
    
    sir = SIRDynamics(
        network,
        beta=layer_rates,   # Pass dict instead of float
        gamma=0.1,
        initial_infected=5
    )
    
    results = sir.run(steps=100)

Analyzing Results Over Time
----------------------------

Track epidemic progression:

.. code-block:: python

    from py3plex.dynamics import SIRDynamics
    import matplotlib.pyplot as plt
    
    sir = SIRDynamics(network, beta=0.3, gamma=0.1, initial_infected=5)
    sir.set_seed(42)
    results = sir.run(steps=100)
    
    # Get time series
    time_series = results.get_measure('time_series')
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(time_series['susceptible'], label='Susceptible')
    plt.plot(time_series['infected'], label='Infected')
    plt.plot(time_series['recovered'], label='Recovered')
    plt.xlabel('Time step')
    plt.ylabel('Number of nodes')
    plt.legend()
    plt.title('SIR Epidemic Progression')
    plt.savefig('sir_progression.png', dpi=300, bbox_inches='tight')
    plt.show()

Comparing Intervention Strategies
----------------------------------

Test different scenarios:

.. code-block:: python

    scenarios = [
        {'name': 'Baseline', 'beta': 0.3, 'gamma': 0.1},
        {'name': 'Social distancing', 'beta': 0.15, 'gamma': 0.1},
        {'name': 'Faster recovery', 'beta': 0.3, 'gamma': 0.2},
    ]
    
    results = []
    
    for scenario in scenarios:
        sir = SIRDynamics(
            network,
            beta=scenario['beta'],
            gamma=scenario['gamma'],
            initial_infected=5
        )
        sir.set_seed(42)
        result = sir.run(steps=100)
        
        results.append({
            'name': scenario['name'],
            'peak': result.get_measure('peak_prevalence'),
            'final': result.get_measure('final_recovered')
        })
    
    # Compare
    for r in results:
        print(f"{r['name']}: peak={r['peak']:.2%}, final={r['final']:.2%}")

**Expected output:**

.. code-block:: text

    Baseline: peak=35.29%, final=87.45%
    Social distancing: peak=18.42%, final=62.33%
    Faster recovery: peak=28.91%, final=79.21%

Custom Dynamics
---------------

Implement custom dynamics models:

.. code-block:: python

    from py3plex.dynamics.core import BaseDynamics
    
    class CustomDynamics(BaseDynamics):
        def __init__(self, network, param1, param2):
            super().__init__(network)
            self.param1 = param1
            self.param2 = param2
        
        def step(self):
            """Single simulation step."""
            # Your custom logic here
            pass
        
        def run(self, steps):
            """Run simulation for specified steps."""
            for _ in range(steps):
                self.step()
            return self.get_results()

See :doc:`../reference/api_index` for the BaseDynamics API.

Next Steps
----------

* **Visualize dynamics:** :doc:`visualize_networks`
* **Understand theory:** :doc:`../concepts/multilayer_networks_101`
* **See examples:** :doc:`../examples/index`
* **API reference:** :doc:`../reference/algorithm_reference`
