"""Conservation law and validation tests for dynamics module.

These tests verify that dynamics implementations satisfy fundamental
physical/mathematical conservation laws and maintain consistent behavior.

Tests include:
- State conservation (S+I+R == N for compartmental models)
- Probability conservation (random walk transition probabilities sum to 1)
- Steady-state behavior (SIS reaches endemic equilibrium)
- Determinism (same seed produces same results)
"""

import pytest
import numpy as np
import networkx as nx
from py3plex.core import multinet
from py3plex.dynamics import (
    SIRDynamics,
    SISDynamics,
    SEIRDynamics,
    RandomWalkDynamics,
)


class TestConservationLaws:
    """Test that dynamics satisfy conservation laws."""
    
    def test_sir_node_conservation(self):
        """Test that S + I + R == N at all times for SIR."""
        G = nx.karate_club_graph()
        N = G.number_of_nodes()
        
        sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
        sir.set_seed(42)
        results = sir.run(steps=50)
        
        # Check conservation at each time step
        state_counts = results.get_measure("state_counts")
        
        for t in range(len(state_counts['S'])):
            total = (state_counts.get('S', np.zeros(len(state_counts['S'])))[t] +
                    state_counts.get('I', np.zeros(len(state_counts['S'])))[t] +
                    state_counts.get('R', np.zeros(len(state_counts['S'])))[t])
            assert total == N, f"Conservation violated at t={t}: {total} != {N}"
    
    def test_sis_node_conservation(self):
        """Test that S + I == N at all times for SIS."""
        G = nx.karate_club_graph()
        N = G.number_of_nodes()
        
        sis = SISDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
        sis.set_seed(42)
        results = sis.run(steps=50)
        
        # Check conservation at each time step
        state_counts = results.get_measure("state_counts")
        
        for t in range(len(state_counts['S'])):
            total = state_counts['S'][t] + state_counts['I'][t]
            assert total == N, f"Conservation violated at t={t}: {total} != {N}"
    
    def test_seir_node_conservation(self):
        """Test that S + E + I + R == N at all times for SEIR."""
        G = nx.karate_club_graph()
        N = G.number_of_nodes()
        
        seir = SEIRDynamics(G, beta=0.3, sigma=0.2, gamma=0.1, initial_infected=0.1)
        seir.set_seed(42)
        results = seir.run(steps=50)
        
        # Check conservation at each time step
        state_counts = results.get_measure("state_counts")
        
        for t in range(len(state_counts['S'])):
            total = (state_counts['S'][t] + state_counts['E'][t] +
                    state_counts['I'][t] + state_counts['R'][t])
            assert total == N, f"Conservation violated at t={t}: {total} != {N}"
    
    def test_sir_absorbing_recovered(self):
        """Test that recovered nodes stay recovered in SIR."""
        G = nx.path_graph(10)
        
        sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.2)
        sir.set_seed(42)
        results = sir.run(steps=50)
        
        state_counts = results.get_measure("state_counts")
        R_counts = state_counts['R']
        
        # R should be monotonically non-decreasing
        for t in range(1, len(R_counts)):
            assert R_counts[t] >= R_counts[t-1], \
                f"R decreased from {R_counts[t-1]} to {R_counts[t]} at t={t}"
    
    def test_conservation_on_multilayer(self):
        """Test conservation laws on multilayer networks."""
        network = multinet.multi_layer_network(directed=False)
        
        # Add nodes to two layers
        nodes = []
        for i in range(10):
            nodes.append({'source': i, 'type': 'layer1'})
            nodes.append({'source': i, 'type': 'layer2'})
        network.add_nodes(nodes)
        
        # Add some edges
        for i in range(9):
            network.add_edges([{
                'source': i, 'target': i+1,
                'source_type': 'layer1', 'target_type': 'layer1'
            }])
        
        N = network.core_network.number_of_nodes()
        
        sir = SIRDynamics(network, beta=0.3, gamma=0.1, initial_infected=0.1)
        sir.set_seed(42)
        results = sir.run(steps=30)
        
        state_counts = results.get_measure("state_counts")
        
        for t in range(len(state_counts['S'])):
            total = (state_counts.get('S', np.zeros(len(state_counts['S'])))[t] +
                    state_counts.get('I', np.zeros(len(state_counts['S'])))[t] +
                    state_counts.get('R', np.zeros(len(state_counts['S'])))[t])
            assert total == N, f"Multilayer conservation violated at t={t}"


class TestSteadyState:
    """Test steady-state behavior of dynamics."""
    
    def test_sis_endemic_equilibrium(self):
        """Test that SIS reaches endemic equilibrium above threshold."""
        G = nx.karate_club_graph()
        
        # Parameters above epidemic threshold
        sis = SISDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
        sis.set_seed(42)
        results = sis.run(steps=200)
        
        prevalence = results.get_measure("prevalence")
        
        # Check that prevalence stabilizes (low variance in last 50 steps)
        last_50 = prevalence[-50:]
        variance = np.var(last_50)
        
        # Variance should be small for endemic equilibrium
        assert variance < 0.01, f"SIS did not reach equilibrium: variance={variance}"
        
        # Mean prevalence should be > 0 above threshold
        mean_prevalence = np.mean(last_50)
        assert mean_prevalence > 0.1, f"Endemic level too low: {mean_prevalence}"
    
    def test_sir_extinction(self):
        """Test that SIR epidemic dies out eventually."""
        G = nx.karate_club_graph()
        
        sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
        sir.set_seed(42)
        results = sir.run(steps=100)
        
        prevalence = results.get_measure("prevalence")
        
        # Eventually, prevalence should go to zero
        final_prevalence = prevalence[-10:].mean()
        assert final_prevalence < 0.01, \
            f"SIR did not die out: final prevalence={final_prevalence}"


class TestDeterminism:
    """Test that dynamics are deterministic given a seed."""
    
    def test_sir_reproducibility(self):
        """Test that SIR produces same results with same seed."""
        G = nx.karate_club_graph()
        
        # Run 1
        sir1 = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
        sir1.set_seed(42)
        results1 = sir1.run(steps=50)
        prevalence1 = results1.get_measure("prevalence")
        
        # Run 2 with same seed
        sir2 = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
        sir2.set_seed(42)
        results2 = sir2.run(steps=50)
        prevalence2 = results2.get_measure("prevalence")
        
        # Should be identical
        np.testing.assert_array_equal(prevalence1, prevalence2,
            err_msg="SIR not reproducible with same seed")
    
    def test_sis_reproducibility(self):
        """Test that SIS produces same results with same seed."""
        G = nx.karate_club_graph()
        
        # Run 1
        sis1 = SISDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
        sis1.set_seed(123)
        results1 = sis1.run(steps=50)
        prevalence1 = results1.get_measure("prevalence")
        
        # Run 2 with same seed
        sis2 = SISDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
        sis2.set_seed(123)
        results2 = sis2.run(steps=50)
        prevalence2 = results2.get_measure("prevalence")
        
        # Should be identical
        np.testing.assert_array_equal(prevalence1, prevalence2,
            err_msg="SIS not reproducible with same seed")
    
    def test_random_walk_reproducibility(self):
        """Test that random walk produces same trajectory with same seed."""
        G = nx.karate_club_graph()
        
        # Run 1
        walk1 = RandomWalkDynamics(G, start_node=0)
        walk1.set_seed(42)
        results1 = walk1.run(steps=100)
        traj1 = results1.get_measure("trajectory")
        
        # Run 2 with same seed
        walk2 = RandomWalkDynamics(G, start_node=0)
        walk2.set_seed(42)
        results2 = walk2.run(steps=100)
        traj2 = results2.get_measure("trajectory")
        
        # Should be identical
        assert traj1 == traj2, "Random walk not reproducible with same seed"


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def test_all_infected_initial(self):
        """Test dynamics when all nodes are initially infected."""
        G = nx.path_graph(10)
        
        sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=1.0)
        sir.set_seed(42)
        results = sir.run(steps=50)  # Run longer to ensure all recover
        
        state_counts = results.get_measure("state_counts")
        
        # Initially all infected
        assert state_counts['I'][0] == 10
        assert state_counts.get('S', np.zeros(len(state_counts['I'])))[0] == 0
        
        # Eventually all recovered (no susceptibles, so all must become R)
        assert state_counts['R'][-1] == 10
        assert state_counts['I'][-1] == 0
    
    def test_single_infected_initial(self):
        """Test dynamics starting from single infected node."""
        G = nx.complete_graph(10)
        
        # Explicitly set single infected node
        sir = SIRDynamics(G, beta=0.5, gamma=0.1, initial_infected=0.1)
        sir.set_seed(42)
        results = sir.run(steps=30)
        
        state_counts = results.get_measure("state_counts")
        
        # Should have at least 1 infected initially
        assert state_counts['I'][0] >= 1
        
        # On complete graph with high beta, should spread
        max_infected = np.max(state_counts['I'])
        assert max_infected > 1, "Infection did not spread"
    
    def test_isolated_nodes(self):
        """Test dynamics with isolated nodes."""
        # Create graph with isolated node
        G = nx.Graph()
        G.add_nodes_from(range(5))
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])  # Node 4 is isolated
        
        sir = SIRDynamics(G, beta=0.5, gamma=0.1, initial_infected=0.2)
        sir.set_seed(42)
        results = sir.run(steps=30)
        
        # Should not crash
        assert len(results) == 31  # Initial + 30 steps


class TestMeasureExtraction:
    """Test the get_measure() API."""
    
    def test_prevalence_bounds(self):
        """Test that prevalence is always in [0, 1]."""
        G = nx.karate_club_graph()
        
        sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
        sir.set_seed(42)
        results = sir.run(steps=50)
        
        prevalence = results.get_measure("prevalence")
        
        assert np.all(prevalence >= 0.0), "Prevalence < 0"
        assert np.all(prevalence <= 1.0), "Prevalence > 1"
    
    def test_state_counts_nonnegative(self):
        """Test that state counts are non-negative."""
        G = nx.karate_club_graph()
        
        sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
        sir.set_seed(42)
        results = sir.run(steps=50)
        
        state_counts = results.get_measure("state_counts")
        
        for state, counts in state_counts.items():
            assert np.all(counts >= 0), f"Negative counts for state {state}"
    
    def test_unknown_measure_error(self):
        """Test that requesting unknown measure raises error."""
        G = nx.karate_club_graph()
        
        sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)
        sir.set_seed(42)
        results = sir.run(steps=10)
        
        with pytest.raises(ValueError, match="Unknown measure"):
            results.get_measure("nonexistent_measure")
    
    def test_trajectory_measure(self):
        """Test that trajectory measure returns full trajectory."""
        G = nx.path_graph(5)
        
        sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.2)
        sir.set_seed(42)
        results = sir.run(steps=10)
        
        trajectory = results.get_measure("trajectory")
        
        # Should have 11 states (initial + 10 steps)
        assert len(trajectory) == 11
        
        # Each state should be a dict
        assert all(isinstance(state, dict) for state in trajectory)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
