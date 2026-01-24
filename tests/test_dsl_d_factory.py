"""Tests for D.simulate() factory and convenience aliases.

This test suite validates the new D factory for dynamics simulations and
convenience aliases added to DynamicsBuilder:
- D.simulate(model, **params)
- .seed_infections(fraction, nodes)
- .starting_nodes(nodes)
- .steps(n)
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import D, Q, L, DynamicsBuilder


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
        {'source': 'E', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'D', 'target': 'E', 'source_type': 'work', 'target_type': 'work'},
    ]
    network.add_edges(edges)
    
    return network


class TestDFactory:
    """Test D.simulate() factory."""
    
    def test_d_simulate_basic(self):
        """Test D.simulate() with model name."""
        builder = D.simulate("SIS", beta=0.3, mu=0.1)
        
        assert isinstance(builder, DynamicsBuilder)
        assert builder._stmt.process_name == "SIS"
        assert builder._stmt.params["beta"] == 0.3
        assert builder._stmt.params["mu"] == 0.1
    
    def test_d_simulate_sir(self):
        """Test D.simulate() with SIR model."""
        builder = D.simulate("SIR", beta=0.3, gamma=0.1)
        
        assert isinstance(builder, DynamicsBuilder)
        assert builder._stmt.process_name == "SIR"
        assert builder._stmt.params["beta"] == 0.3
        assert builder._stmt.params["gamma"] == 0.1
    
    def test_d_simulate_seir(self):
        """Test D.simulate() with SEIR model."""
        builder = D.simulate("SEIR", beta=0.3, sigma=0.2, gamma=0.1)
        
        assert isinstance(builder, DynamicsBuilder)
        assert builder._stmt.process_name == "SEIR"
        assert builder._stmt.params["beta"] == 0.3
        assert builder._stmt.params["sigma"] == 0.2
        assert builder._stmt.params["gamma"] == 0.1
    
    def test_d_simulate_random_walk(self):
        """Test D.simulate() with RANDOM_WALK model."""
        builder = D.simulate("RANDOM_WALK", restart_prob=0.15)
        
        assert isinstance(builder, DynamicsBuilder)
        assert builder._stmt.process_name == "RANDOM_WALK"
        assert builder._stmt.params["restart_prob"] == 0.15
    
    def test_d_simulate_returns_same_type_as_q_dynamics(self):
        """Test that D.simulate() and Q.dynamics() return the same type."""
        d_builder = D.simulate("SIS", beta=0.3, mu=0.1)
        q_builder = Q.dynamics("SIS", beta=0.3, mu=0.1)
        
        assert type(d_builder) == type(q_builder)
        assert isinstance(d_builder, DynamicsBuilder)
        assert isinstance(q_builder, DynamicsBuilder)


class TestConvenienceAliases:
    """Test convenience aliases on DynamicsBuilder."""
    
    def test_seed_infections_with_fraction(self):
        """Test .seed_infections() with fraction."""
        builder = D.simulate("SIS", beta=0.3, mu=0.1).seed_infections(fraction=0.01)
        
        assert builder._stmt.seed_fraction == 0.01
    
    def test_seed_infections_with_nodes(self):
        """Test .seed_infections() with specific nodes."""
        nodes = [('Alice', 'social'), ('Bob', 'work')]
        builder = D.simulate("SIS", beta=0.3, mu=0.1).seed_infections(nodes=nodes)
        
        assert hasattr(builder._stmt, 'seed_nodes')
        assert builder._stmt.seed_nodes == nodes
    
    def test_seed_infections_error_both_params(self):
        """Test .seed_infections() raises error when both fraction and nodes provided."""
        with pytest.raises(ValueError, match="Provide either 'fraction' or 'nodes'"):
            D.simulate("SIS", beta=0.3, mu=0.1).seed_infections(
                fraction=0.01, 
                nodes=[('Alice', 'social')]
            )
    
    def test_seed_infections_error_no_params(self):
        """Test .seed_infections() raises error when neither param provided."""
        with pytest.raises(ValueError, match="Must provide either 'fraction' or 'nodes'"):
            D.simulate("SIS", beta=0.3, mu=0.1).seed_infections()
    
    def test_starting_nodes(self):
        """Test .starting_nodes() for random walk."""
        nodes = [('Alice', 'social'), ('Bob', 'work')]
        builder = D.simulate("RANDOM_WALK", restart_prob=0.15).starting_nodes(nodes)
        
        assert hasattr(builder._stmt, 'seed_nodes')
        assert builder._stmt.seed_nodes == nodes
    
    def test_steps_convenience(self):
        """Test .steps() convenience method."""
        builder = D.simulate("SIS", beta=0.3, mu=0.1).steps(100)
        
        assert builder._stmt.steps == 100
    
    def test_steps_can_chain_with_replicates(self):
        """Test .steps() can be chained with .run() for replicates."""
        builder = (
            D.simulate("SIS", beta=0.3, mu=0.1)
             .steps(100)
             .run(replicates=10)
        )
        
        assert builder._stmt.steps == 100
        assert builder._stmt.replicates == 10


class TestDSimulateExecution:
    """Test D.simulate() execution."""
    
    def test_d_simulate_execute_basic(self, sample_network):
        """Test D.simulate() execution works."""
        result = (
            D.simulate("SIS", beta=0.3, mu=0.1)
             .seed_infections(fraction=0.2)
             .steps(10)
             .run(replicates=2)
             .random_seed(42)
             .execute(sample_network)
        )
        
        assert result is not None
        assert hasattr(result, 'data')
    
    def test_d_simulate_with_layers(self, sample_network):
        """Test D.simulate() with layer selection."""
        result = (
            D.simulate("SIS", beta=0.3, mu=0.1)
             .on_layers(L["social"])
             .seed_infections(fraction=0.2)
             .steps(10)
             .random_seed(42)
             .execute(sample_network)
        )
        
        assert result is not None


class TestExamplesFromSpec:
    """Test examples from the issue specification."""
    
    def test_q_dynamics_sis_example(self, sample_network):
        """Test Q.dynamics SIS example from spec."""
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .on_layers(L["social"])
             .seed_infections(fraction=0.01)
             .run(steps=10, replicates=2)
             .execute(sample_network)
        )
        
        assert result is not None
    
    def test_q_dynamics_sir_example(self, sample_network):
        """Test Q.dynamics SIR example from spec."""
        result = (
            Q.dynamics("SIR", beta=0.3, gamma=0.1)
             .on_layers(L["social"] + L["work"])
             .seed_infections(nodes=[('A', 'social')])
             .run(steps=10, replicates=2)
             .execute(sample_network)
        )
        
        assert result is not None
    
    @pytest.mark.skip(reason="SEIR not yet implemented in processes.py")
    def test_q_dynamics_seir_example(self, sample_network):
        """Test Q.dynamics SEIR example from spec."""
        result = (
            Q.dynamics("SEIR", beta=0.3, sigma=0.2, gamma=0.1)
             .on_layers(L["social"])
             .seed_infections(fraction=0.01)
             .run(steps=10, replicates=2)
             .execute(sample_network)
        )
        
        assert result is not None
    
    def test_d_simulate_example(self, sample_network):
        """Test D.simulate example from spec."""
        result = (
            D.simulate("SIS", beta=0.3, mu=0.1)
             .on_layers(L["social"])
             .seed_infections(fraction=0.01)
             .steps(10)
             .execute(sample_network)
        )
        
        assert result is not None
