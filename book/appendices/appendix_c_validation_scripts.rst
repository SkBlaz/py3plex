Appendix C: Detailed Validation Scripts
========================================

This appendix provides detailed validation strategies and test scripts for ensuring correctness of multilayer network algorithms. These complement the high-level overview in Chapter 15.

Validation Philosophy
---------------------

py3plex uses multiple validation strategies:

1. **Unit tests** — Test individual functions in isolation
2. **Property-based tests** — Test invariants that should always hold
3. **Reference runs** — Compare against known-good results
4. **Conservation tests** — Verify physical/mathematical laws (e.g., probability conservation)

Random Walk Validation
----------------------

Conservation Tests
~~~~~~~~~~~~~~~~~~

Random walks must conserve probability—the sum of transition probabilities from any state must equal 1:

.. code-block:: python

    # File: tests/test_random_walk_conservation.py
    import pytest
    import numpy as np
    from py3plex.algorithms.paths import random_walk
    
    def test_probability_conservation():
        """Verify random walk conserves probability."""
        network = create_test_network()
        
        # Run random walk
        walks = random_walk(network, num_walks=1000, walk_length=100)
        
        # Compute transition matrix
        trans_matrix = compute_transition_matrix(walks)
        
        # Check row sums = 1
        row_sums = trans_matrix.sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-6)

Bias Validation
~~~~~~~~~~~~~~~

Node2Vec introduces biases (return parameter p, in-out parameter q). Validate that biases have the intended effect:

.. code-block:: python

    # File: tests/test_node2vec_bias.py
    def test_return_bias():
        """Higher p should reduce probability of returning to previous node."""
        network = create_test_network()
        
        # Low p (encourage return)
        walks_low_p = node2vec_walk(network, p=0.25, q=1.0, num_walks=1000)
        return_rate_low = count_immediate_returns(walks_low_p)
        
        # High p (discourage return)
        walks_high_p = node2vec_walk(network, p=4.0, q=1.0, num_walks=1000)
        return_rate_high = count_immediate_returns(walks_high_p)
        
        assert return_rate_high < return_rate_low

Reference Runs
~~~~~~~~~~~~~~

Store reference outputs for deterministic tests:

.. code-block:: python

    # File: tests/test_dynamics_reference_runs.py
    REFERENCE_DATA = {
        'sir_small_graph_42': {
            'beta': 0.3,
            'gamma': 0.1,
            'steps': 100,
            'seed': 42,
            'expected_final_recovered': 0.75
        }
    }
    
    def test_sir_matches_reference():
        """Ensure SIR dynamics match reference run."""
        ref = REFERENCE_DATA['sir_small_graph_42']
        
        network = make_tiny_chain_graph()
        sir = SIRDynamics(network, beta=ref['beta'], gamma=ref['gamma'])
        sir.set_seed(ref['seed'])
        
        results = sir.run(steps=ref['steps'])
        final_recovered = results.get_measure('state_counts')[2][-1] / network.number_of_nodes()
        
        assert abs(final_recovered - ref['expected_final_recovered']) < 0.01

Community Detection Validation
-------------------------------

Modularity Bounds
~~~~~~~~~~~~~~~~~

Modularity Q must be in range [-0.5, 1.0]:

.. code-block:: python

    # File: tests/test_community_bounds.py
    def test_modularity_bounds():
        """Modularity must be in valid range."""
        network = create_test_network()
        
        communities = multilayer_louvain.best_partition(network.core_network)
        Q = compute_modularity(network, communities)
        
        assert -0.5 <= Q <= 1.0

Partition Quality
~~~~~~~~~~~~~~~~~

Every node must be assigned to exactly one community:

.. code-block:: python

    def test_partition_completeness():
        """Every node must be in exactly one community."""
        network = create_test_network()
        communities = multilayer_louvain.best_partition(network.core_network)
        
        # All nodes accounted for
        assert set(communities.keys()) == set(network.get_nodes())
        
        # No overlapping assignments (in non-overlapping methods)
        assert len(communities) == len(set(communities.values()))

Singleton Detection
~~~~~~~~~~~~~~~~~~~

Validate that isolated nodes form their own communities:

.. code-block:: python

    def test_singleton_communities():
        """Isolated nodes should form singleton communities."""
        network = create_network_with_isolates()
        communities = multilayer_louvain.best_partition(network.core_network)
        
        isolates = [n for n in network.get_nodes() if network.core_network.degree(n) == 0]
        
        # Each isolate in its own community
        for node in isolates:
            community = communities[node]
            same_community = [n for n, c in communities.items() if c == community]
            assert same_community == [node]

Centrality Validation
---------------------

Degree Centrality
~~~~~~~~~~~~~~~~~

Degree centrality should match actual degree counts:

.. code-block:: python

    # File: tests/test_centrality_correctness.py
    def test_degree_centrality():
        """Degree centrality should match computed degrees."""
        network = create_test_network()
        
        import networkx as nx
        degree_cent = nx.degree_centrality(network.core_network)
        
        for node in network.get_nodes():
            computed = degree_cent[node]
            expected = network.core_network.degree(node) / (network.number_of_nodes() - 1)
            assert abs(computed - expected) < 1e-10

Betweenness Centrality
~~~~~~~~~~~~~~~~~~~~~~

Validate using known structures (e.g., star graphs):

.. code-block:: python

    def test_betweenness_star_graph():
        """In a star graph, center has betweenness 1.0."""
        network = create_star_graph(n=5)  # 1 center + 4 leaves
        
        import networkx as nx
        bc = nx.betweenness_centrality(network.core_network, normalized=True)
        
        center = ('center', 'layer')
        assert bc[center] == 1.0  # All paths go through center
        
        leaves = [n for n in network.get_nodes() if n != center]
        for leaf in leaves:
            assert bc[leaf] == 0.0  # Leaves are not on any shortest paths

Dynamics Validation
-------------------

SIS Model Conservation
~~~~~~~~~~~~~~~~~~~~~~

In SIS model, S(t) + I(t) = N for all t:

.. code-block:: python

    # File: tests/test_dynamics_conservation.py
    def test_sis_conservation():
        """SIS model must conserve population."""
        network = create_test_network()
        N = network.number_of_nodes()
        
        sis = SISDynamics(network, beta=0.3, gamma=0.1)
        sis.set_seed(42)
        
        results = sis.run(steps=100)
        
        for t in range(100):
            S_t = results.get_measure('state_counts')[0][t]
            I_t = results.get_measure('state_counts')[1][t]
            assert S_t + I_t == N

SIR Model Conservation
~~~~~~~~~~~~~~~~~~~~~~

In SIR model, S(t) + I(t) + R(t) = N for all t:

.. code-block:: python

    def test_sir_conservation():
        """SIR model must conserve population."""
        network = create_test_network()
        N = network.number_of_nodes()
        
        sir = SIRDynamics(network, beta=0.3, gamma=0.1)
        sir.set_seed(42)
        
        results = sir.run(steps=100)
        
        for t in range(100):
            S_t = results.get_measure('state_counts')[0][t]
            I_t = results.get_measure('state_counts')[1][t]
            R_t = results.get_measure('state_counts')[2][t]
            assert S_t + I_t + R_t == N

Steady State Validation
~~~~~~~~~~~~~~~~~~~~~~~

SIS model should reach steady state:

.. code-block:: python

    def test_sis_steady_state():
        """SIS should reach equilibrium."""
        network = create_test_network()
        
        sis = SISDynamics(network, beta=0.3, gamma=0.1)
        sis.set_seed(42)
        
        results = sis.run(steps=1000)
        prevalence = results.get_measure('prevalence')
        
        # Check last 100 steps are stable
        last_100 = prevalence[-100:]
        variance = np.var(last_100)
        assert variance < 0.01  # Low variance = steady state

Property-Based Testing
----------------------

Using Hypothesis
~~~~~~~~~~~~~~~~

Property-based tests use the ``hypothesis`` library to generate random inputs:

.. code-block:: python

    # File: tests/property/test_paths_properties.py
    from hypothesis import given, strategies as st
    from hypothesis import assume
    
    @given(
        num_nodes=st.integers(min_value=3, max_value=20),
        num_layers=st.integers(min_value=1, max_value=5),
        seed=st.integers(min_value=0, max_value=1000)
    )
    def test_shortest_path_length_property(num_nodes, num_layers, seed):
        """Shortest path length should be <= graph diameter."""
        network = generate_random_network(num_nodes, num_layers, seed)
        assume(nx.is_connected(network.core_network))  # Skip disconnected graphs
        
        # Pick random source and target
        nodes = list(network.get_nodes())
        source, target = random.sample(nodes, 2)
        
        # Compute shortest path
        path = nx.shortest_path(network.core_network, source, target)
        path_length = len(path) - 1
        
        # Path length should be <= diameter
        diameter = nx.diameter(network.core_network)
        assert path_length <= diameter

Multilayer-Specific Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @given(num_nodes=st.integers(min_value=2, max_value=10))
    def test_node_activity_bounds(num_nodes):
        """Node activity must be in [0, 1]."""
        network = generate_multiplex_network(num_nodes)
        
        for node_id in range(num_nodes):
            activity = mls.node_activity(network, str(node_id))
            assert 0.0 <= activity <= 1.0

Running Validation Tests
------------------------

Full Test Suite
~~~~~~~~~~~~~~~

.. code-block:: bash

    # Run all tests
    pytest tests/
    
    # Run only validation tests
    pytest tests/ -k validation
    
    # Run with coverage
    pytest tests/ --cov=py3plex --cov-report=html

Property-Based Tests
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Run property tests (slower)
    pytest tests/property/
    
    # Run with more examples
    pytest tests/property/ --hypothesis-profile=thorough

Continuous Validation
~~~~~~~~~~~~~~~~~~~~~

Tests run automatically on:

* Every commit (GitHub Actions)
* Pull requests
* Scheduled nightly runs

Summary
-------

This appendix detailed validation strategies:

1. **Conservation tests** — Physical/mathematical laws must hold
2. **Reference runs** — Deterministic tests against known-good outputs
3. **Boundary tests** — Values must be in valid ranges
4. **Property-based tests** — Invariants hold for random inputs
5. **Structure tests** — Algorithmic correctness on known structures

**Key test files:**

* ``tests/test_dynamics_reference_runs.py`` — Reference dynamics data
* ``tests/test_random_walk_conservation.py`` — Probability conservation
* ``tests/property/`` — Property-based tests
* ``tests/test_centrality_correctness.py`` — Centrality validation

[For high-level testing overview → Chapter 15]
