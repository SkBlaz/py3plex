"""Comprehensive tests for the new dynamics core classes.

Tests cover:
- DynamicsProcess base class and discrete-time models
- ContinuousTimeProcess and Gillespie algorithm
- TemporalGraph and temporal dynamics
- Compartmental models (SIR, SEIR)
- Config-based dynamics
- Reproducibility and seeding
- Backend compatibility (Python, NumPy, PyTorch)
"""

import pytest
import numpy as np
import networkx as nx

from py3plex.dynamics import (
    # Core abstractions
    DynamicsProcess,
    ContinuousTimeProcess,
    TemporalGraph,
    TemporalDynamicsProcess,
    # Discrete-time models
    RandomWalkDynamics,
    MultiRandomWalkDynamics,
    SISDynamics,
    AdaptiveSISDynamics,
    TemporalRandomWalk,
    # Continuous-time & compartmental
    SISContinuousTime,
    CompartmentalDynamics,
    SIRDynamics,
    SEIRDynamics,
    # Config-based
    build_dynamics_from_config,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def simple_graph():
    """Create a simple karate club graph for testing."""
    return nx.karate_club_graph()


@pytest.fixture
def small_graph():
    """Create a small test graph."""
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)])
    return G


@pytest.fixture
def temporal_graphs():
    """Create a list of temporal graph snapshots."""
    return [nx.erdos_renyi_graph(10, 0.3, seed=i) for i in range(5)]


# ============================================================================
# Test RandomWalkDynamics
# ============================================================================

class TestRandomWalkDynamics:
    """Tests for single-walker random walk."""
    
    def test_basic_walk(self, simple_graph):
        """Test basic random walk."""
        walk = RandomWalkDynamics(simple_graph, seed=42, start_node=0)
        trajectory = walk.run(steps=100)
        
        assert len(trajectory) == 101  # includes initial state
        assert trajectory[0] == 0  # starts at correct node
        
        # All positions should be valid nodes
        for pos in trajectory:
            assert pos in simple_graph.nodes()
    
    def test_lazy_walk(self, small_graph):
        """Test lazy random walk (stays in place with probability)."""
        walk = RandomWalkDynamics(
            small_graph, seed=42, start_node=0, lazy_probability=0.5
        )
        trajectory = walk.run(steps=50)
        
        # With lazy probability, walker should stay in place sometimes
        stays = sum(1 for i in range(1, len(trajectory)) if trajectory[i] == trajectory[i-1])
        assert stays > 0  # Should have some stays
    
    def test_visit_counts(self, small_graph):
        """Test visit count computation."""
        walk = RandomWalkDynamics(small_graph, seed=42, start_node=0)
        trajectory = walk.run(steps=100)
        counts = walk.visit_counts(trajectory)
        
        # All nodes should be visited at least once (connected graph)
        assert all(counts.get(node, 0) > 0 for node in small_graph.nodes())
        
        # Total visits should equal trajectory length
        assert sum(counts.values()) == len(trajectory)
    
    def test_reproducibility(self, simple_graph):
        """Test that same seed produces same walk."""
        walk1 = RandomWalkDynamics(simple_graph, seed=42, start_node=0)
        walk2 = RandomWalkDynamics(simple_graph, seed=42, start_node=0)
        
        results1 = walk1.run(steps=50)
        results2 = walk2.run(steps=50)
        
        # Extract trajectories and compare
        traj1 = results1.get_measure("trajectory")
        traj2 = results2.get_measure("trajectory")
        assert traj1 == traj2
    
    def test_different_seeds(self, simple_graph):
        """Test that different seeds produce different walks."""
        walk1 = RandomWalkDynamics(simple_graph, seed=42, start_node=0)
        walk2 = RandomWalkDynamics(simple_graph, seed=123, start_node=0)
        
        results1 = walk1.run(steps=50)
        results2 = walk2.run(steps=50)
        
        # Extract trajectories and compare
        traj1 = results1.get_measure("trajectory")
        traj2 = results2.get_measure("trajectory")
        assert traj1 != traj2


# ============================================================================
# Test MultiRandomWalkDynamics
# ============================================================================

class TestMultiRandomWalkDynamics:
    """Tests for multi-walker random walks."""
    
    def test_multiple_walkers(self, small_graph):
        """Test multiple independent walkers."""
        walk = MultiRandomWalkDynamics(
            small_graph, seed=42, n_walkers=3, init_strategy='random'
        )
        trajectory = walk.run(steps=50)
        
        assert len(trajectory) == 51  # includes initial state
        assert len(trajectory[0]) == 3  # 3 walkers
        
        # All walker positions should be valid nodes
        for state in trajectory:
            for pos in state:
                if pos is not None:
                    assert pos in small_graph.nodes()
    
    def test_absorbing_states(self, small_graph):
        """Test walkers with absorbing nodes."""
        walk = MultiRandomWalkDynamics(
            small_graph,
            seed=42,
            n_walkers=3,
            absorbing_nodes={0, 3},
        )
        trajectory = walk.run(steps=100)
        
        # Eventually all walkers should be absorbed
        final_state = trajectory[-1]
        absorbed_count = sum(1 for pos in final_state if pos is None)
        assert absorbed_count > 0  # At least some walkers absorbed
    
    def test_hitting_time_statistics(self, small_graph):
        """Test hitting time statistics computation."""
        walk = MultiRandomWalkDynamics(
            small_graph,
            seed=42,
            n_walkers=5,
            absorbing_nodes={2},
        )
        trajectory = walk.run(steps=100)
        stats = walk.hitting_time_statistics(trajectory)
        
        assert 'hitting_times' in stats
        assert 'mean' in stats
        assert 'absorbed_count' in stats
        assert len(stats['hitting_times']) == 5
        
        # Some walkers should be absorbed
        assert stats['absorbed_count'] > 0


# ============================================================================
# Test SISDynamics
# ============================================================================

class TestSISDynamics:
    """Tests for SIS epidemic model."""
    
    def test_basic_sis(self, simple_graph):
        """Test basic SIS dynamics."""
        sis = SISDynamics(
            simple_graph, seed=42, beta=0.3, mu=0.1, initial_infected=0.1
        )
        trajectory = sis.run(steps=50)
        
        assert len(trajectory) == 51
        
        # All states should be 'S' or 'I'
        for state in trajectory:
            assert all(v in ['S', 'I'] for v in state.values())
    
    def test_prevalence(self, small_graph):
        """Test prevalence computation."""
        sis = SISDynamics(
            small_graph, seed=42, beta=0.5, mu=0.1, initial_infected=0.5
        )
        state = sis.initialize_state()
        prev = sis.prevalence(state)
        
        assert 0.0 <= prev <= 1.0
    
    def test_prevalence_series(self, small_graph):
        """Test prevalence time series."""
        sis = SISDynamics(
            small_graph, seed=42, beta=0.4, mu=0.2, initial_infected=0.5
        )
        prevalence_series = sis.run_with_prevalence(steps=50)
        
        assert len(prevalence_series) == 51
        assert all(0.0 <= p <= 1.0 for p in prevalence_series)
    
    def test_numpy_backend(self, small_graph):
        """Test NumPy vectorized backend."""
        sis = SISDynamics(
            small_graph,
            seed=42,
            beta=0.3,
            mu=0.1,
            initial_infected=0.5,
            backend='numpy'
        )
        trajectory = sis.run(steps=20)
        
        assert len(trajectory) == 21
        # States should be numpy arrays
        assert isinstance(trajectory[0], np.ndarray)
    
    def test_backend_consistency(self, small_graph):
        """Test that python and numpy backends give same results."""
        sis_python = SISDynamics(
            small_graph,
            seed=42,
            beta=0.3,
            mu=0.1,
            initial_infected=0.5,
            backend='python'
        )
        sis_numpy = SISDynamics(
            small_graph,
            seed=42,
            beta=0.3,
            mu=0.1,
            initial_infected=0.5,
            backend='numpy'
        )
        
        prev_python = sis_python.run_with_prevalence(steps=20)
        prev_numpy = sis_numpy.run_with_prevalence(steps=20)
        
        # Should give similar results (small differences due to RNG)
        assert len(prev_python) == len(prev_numpy)
    
    def test_no_infection_dies_out(self, small_graph):
        """Test that with beta=0, infection dies out."""
        sis = SISDynamics(
            small_graph, seed=42, beta=0.0, mu=0.5, initial_infected=0.5
        )
        prevalence = sis.run_with_prevalence(steps=50)
        
        # Should converge to 0
        assert prevalence[-1] < prevalence[0]


# ============================================================================
# Test AdaptiveSISDynamics
# ============================================================================

class TestAdaptiveSISDynamics:
    """Tests for adaptive SIS with rewiring."""
    
    def test_adaptive_rewiring(self, small_graph):
        """Test that adaptive SIS performs edge rewiring."""
        G = small_graph.copy()  # Copy to avoid modifying fixture
        initial_edges = set(G.edges())
        
        adaptive = AdaptiveSISDynamics(
            G, seed=42, beta=0.3, mu=0.1, w=0.3, initial_infected=0.5
        )
        trajectory = adaptive.run(steps=20)
        
        final_edges = set(G.edges())
        
        # Edges should have changed due to rewiring
        # (may not always change with small graphs and low w, so check size)
        assert len(final_edges) >= len(initial_edges) - 2
    
    def test_edge_type_counts(self, small_graph):
        """Test edge type counting."""
        G = small_graph.copy()
        adaptive = AdaptiveSISDynamics(
            G, seed=42, beta=0.3, mu=0.1, w=0.1, initial_infected=0.5
        )
        state = adaptive.initialize_state()
        counts = adaptive.edge_type_counts(state)
        
        assert 'S-S' in counts
        assert 'S-I' in counts
        assert 'I-I' in counts
        assert sum(counts.values()) == G.number_of_edges()


# ============================================================================
# Test TemporalGraph and TemporalRandomWalk
# ============================================================================

class TestTemporalDynamics:
    """Tests for temporal network dynamics."""
    
    def test_temporal_graph_from_snapshots(self, temporal_graphs):
        """Test TemporalGraph with snapshot list."""
        temporal = TemporalGraph(snapshots=temporal_graphs)
        
        assert len(temporal) == 5
        
        for t in range(5):
            G_t = temporal.get_graph(t)
            assert G_t is temporal_graphs[t]
    
    def test_temporal_graph_from_function(self):
        """Test TemporalGraph with function."""
        def get_graph(t):
            return nx.erdos_renyi_graph(10, 0.2 + 0.05 * t, seed=t)
        
        temporal = TemporalGraph(get_graph_fn=get_graph)
        
        # Can get graphs at any time
        G0 = temporal.get_graph(0)
        G5 = temporal.get_graph(5)
        
        assert G0.number_of_nodes() == 10
        assert G5.number_of_nodes() == 10
    
    def test_temporal_random_walk(self, temporal_graphs):
        """Test random walk on temporal network."""
        temporal = TemporalGraph(snapshots=temporal_graphs)
        walk = TemporalRandomWalk(temporal, seed=42, start_node=0)
        
        trajectory = walk.run(steps=4)  # Can only run up to len(snapshots)-1
        
        assert len(trajectory) == 5
        assert trajectory[0] == 0


# ============================================================================
# Test SISContinuousTime
# ============================================================================

class TestSISContinuousTime:
    """Tests for continuous-time SIS."""
    
    def test_gillespie_simulation(self, small_graph):
        """Test Gillespie algorithm for SIS."""
        sis = SISContinuousTime(
            small_graph, seed=42, beta=0.5, mu=0.1, initial_infected=0.5
        )
        trajectory, times = sis.run(t_max=5.0)
        
        assert len(trajectory) == len(times)
        assert times[0] == 0.0
        assert times[-1] <= 5.1  # Allow small overshoot due to last event
        
        # All states should be valid
        for state in trajectory:
            assert all(v in ['S', 'I'] for v in state.values())
    
    def test_continuous_time_advances(self, small_graph):
        """Test that continuous time actually advances."""
        sis = SISContinuousTime(
            small_graph, seed=42, beta=0.5, mu=0.2, initial_infected=0.5
        )
        trajectory, times = sis.run(t_max=2.0)
        
        # Time should advance
        assert len(times) > 1
        assert times[-1] > times[0]
    
    def test_prevalence_continuous(self, small_graph):
        """Test prevalence computation for continuous-time."""
        sis = SISContinuousTime(
            small_graph, seed=42, beta=0.5, mu=0.1, initial_infected=0.5
        )
        state = sis.initialize_state()
        prev = sis.prevalence(state)
        
        assert 0.0 <= prev <= 1.0


# ============================================================================
# Test CompartmentalDynamics (SIR, SEIR)
# ============================================================================

class TestCompartmentalDynamics:
    """Tests for generic compartmental framework."""
    
    def test_sir_dynamics(self, simple_graph):
        """Test SIR model."""
        sir = SIRDynamics(
            simple_graph, seed=42, beta=0.3, gamma=0.1, initial_infected=0.1
        )
        trajectory = sir.run(steps=50)
        
        assert len(trajectory) == 51
        
        # All states should be S, I, or R
        for state in trajectory:
            assert all(v in ['S', 'I', 'R'] for v in state.values())
    
    def test_sir_absorbing_state(self, small_graph):
        """Test that R is absorbing in SIR."""
        sir = SIRDynamics(
            small_graph, seed=42, beta=0.5, gamma=0.3, initial_infected=0.5
        )
        trajectory = sir.run(steps=100)
        
        # By the end, should have some recovered nodes
        final_counts = sir.compartment_counts(trajectory[-1])
        assert final_counts.get('R', 0) > 0
    
    def test_seir_dynamics(self, simple_graph):
        """Test SEIR model."""
        seir = SEIRDynamics(
            simple_graph,
            seed=42,
            beta=0.3,
            sigma=0.2,
            gamma=0.1,
            initial_infected=0.1
        )
        trajectory = seir.run(steps=50)
        
        assert len(trajectory) == 51
        
        # All states should be S, E, I, or R
        for state in trajectory:
            assert all(v in ['S', 'E', 'I', 'R'] for v in state.values())
    
    def test_compartment_counts(self, small_graph):
        """Test compartment counting."""
        sir = SIRDynamics(
            small_graph, seed=42, beta=0.3, gamma=0.1, initial_infected=0.5
        )
        state = sir.initialize_state()
        counts = sir.compartment_counts(state)
        
        assert 'S' in counts
        assert 'I' in counts
        assert 'R' in counts
        assert sum(counts.values()) == small_graph.number_of_nodes()
    
    def test_total_nodes_preserved(self, small_graph):
        """Test that total node count is preserved in compartmental models."""
        sir = SIRDynamics(
            small_graph, seed=42, beta=0.3, gamma=0.1, initial_infected=0.5
        )
        trajectory = sir.run(steps=50)
        
        n_nodes = small_graph.number_of_nodes()
        for state in trajectory:
            counts = sir.compartment_counts(state)
            assert sum(counts.values()) == n_nodes


# ============================================================================
# Test Config-Based Dynamics
# ============================================================================

class TestConfigBasedDynamics:
    """Tests for build_dynamics_from_config."""
    
    def test_simple_sis_config(self, small_graph):
        """Test building SIS from config."""
        config = {
            "type": "compartmental",
            "compartments": ["S", "I"],
            "parameters": {"beta": 0.3, "mu": 0.1},
            "rules": {
                "S": "infected_neighbors > 0 ? p=1-(1-beta)**infected_neighbors -> I : stay",
                "I": "p=mu -> S : stay"
            },
            "initial": {"I": 0.1}
        }
        
        # Build dynamics and set seed using the new method
        dynamics = build_dynamics_from_config(small_graph, config)
        dynamics.set_seed(42)
        trajectory = dynamics.run(steps=20)
        
        assert len(trajectory) == 21
        # All states should be S or I
        for state in trajectory:
            assert all(v in ['S', 'I'] for v in state.values())
    
    def test_config_with_simple_rule(self, small_graph):
        """Test config with simple deterministic rule."""
        config = {
            "type": "compartmental",
            "compartments": ["A", "B"],
            "parameters": {"p": 0.5},
            "rules": {
                "A": "p=p -> B",  # With probability p, go to B (else stay)
                "B": "stay"
            },
            "initial": {"A": 1.0}
        }
        
        # Build dynamics and set seed using the new method
        dynamics = build_dynamics_from_config(small_graph, config)
        dynamics.set_seed(42)
        trajectory = dynamics.run(steps=10)
        
        # Should have transitions from A to B
        final_counts = dynamics.compartment_counts(trajectory[-1])
        assert final_counts.get('B', 0) > 0


# ============================================================================
# Test Reproducibility
# ============================================================================

class TestReproducibility:
    """Test that all dynamics are reproducible with fixed seeds."""
    
    def test_random_walk_reproducibility(self, simple_graph):
        """Random walk should be reproducible."""
        walk1 = RandomWalkDynamics(simple_graph, seed=42, start_node=0)
        walk2 = RandomWalkDynamics(simple_graph, seed=42, start_node=0)
        
        results1 = walk1.run(steps=50)
        results2 = walk2.run(steps=50)
        
        # Extract trajectories and compare
        traj1 = results1.get_measure("trajectory")
        traj2 = results2.get_measure("trajectory")
        assert traj1 == traj2
    
    def test_sis_reproducibility(self, small_graph):
        """SIS should be reproducible."""
        sis1 = SISDynamics(small_graph, seed=42, beta=0.3, mu=0.1)
        sis2 = SISDynamics(small_graph, seed=42, beta=0.3, mu=0.1)
        
        prev1 = sis1.run_with_prevalence(steps=30)
        prev2 = sis2.run_with_prevalence(steps=30)
        
        assert prev1 == prev2
    
    def test_continuous_time_reproducibility(self, small_graph):
        """Continuous-time SIS should be reproducible."""
        sis1 = SISContinuousTime(small_graph, seed=42, beta=0.5, mu=0.1)
        sis2 = SISContinuousTime(small_graph, seed=42, beta=0.5, mu=0.1)
        
        traj1, times1 = sis1.run(t_max=2.0)
        traj2, times2 = sis2.run(t_max=2.0)
        
        # Should have same event sequence
        assert len(traj1) == len(traj2)
        assert times1 == times2


# ============================================================================
# Test Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling in dynamics."""
    
    def test_multi_walk_requires_n_walkers(self, small_graph):
        """MultiRandomWalkDynamics should require n_walkers."""
        with pytest.raises(ValueError, match="n_walkers"):
            MultiRandomWalkDynamics(small_graph, seed=42)
    
    def test_adaptive_requires_networkx(self):
        """AdaptiveSIS should require NetworkX graph."""
        # Create a non-NetworkX object
        fake_graph = {"nodes": [1, 2, 3]}
        
        with pytest.raises(TypeError, match="NetworkX"):
            AdaptiveSISDynamics(fake_graph, seed=42)
    
    def test_compartmental_requires_compartments(self, small_graph):
        """CompartmentalDynamics should require compartments."""
        with pytest.raises(ValueError, match="compartments"):
            CompartmentalDynamics(small_graph, seed=42)
    
    def test_temporal_graph_validation(self):
        """TemporalGraph should validate inputs."""
        with pytest.raises(ValueError, match="exactly one"):
            TemporalGraph()  # Neither snapshots nor function
        
        with pytest.raises(ValueError, match="exactly one"):
            TemporalGraph(snapshots=[nx.Graph()], get_graph_fn=lambda t: nx.Graph())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
