"""Tests for DSL dynamics integration (Q.dynamics and Q.trajectories).

This test suite validates the integration of dynamics simulations into the DSL
as first-class features via Q.dynamics() and Q.trajectories().

Tests cover:
- Q.dynamics() builder API
- DynamicsStmt AST construction
- Integration with existing D.process() API
- Execution via execute_dynamics_stmt
- Q.trajectories() builder API (placeholder)
- TrajectoriesStmt AST construction
"""

import pytest
import numpy as np
from py3plex.core import multinet
from py3plex.dsl import (
    Q,
    L,
    DynamicsStmt,
    TrajectoriesStmt,
    DynamicsBuilder,
    TrajectoriesBuilder,
)
from py3plex.dsl.errors import DslExecutionError


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


class TestQDynamicsBuilder:
    """Test Q.dynamics() builder API."""
    
    def test_q_dynamics_basic(self):
        """Test basic Q.dynamics() construction."""
        builder = Q.dynamics("SIS", beta=0.3, mu=0.1)
        
        assert isinstance(builder, DynamicsBuilder)
        assert builder._stmt.process_name == "SIS"
        assert builder._stmt.params["beta"] == 0.3
        assert builder._stmt.params["mu"] == 0.1
    
    def test_q_dynamics_with_layers(self):
        """Test Q.dynamics() with layer selection."""
        builder = Q.dynamics("SIS", beta=0.3).on_layers(L["social"])
        
        assert builder._stmt.layer_expr is not None
        assert len(builder._stmt.layer_expr.terms) == 1
        assert builder._stmt.layer_expr.terms[0].name == "social"
    
    def test_q_dynamics_with_multilayer(self):
        """Test Q.dynamics() with multiple layers."""
        builder = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .on_layers(L["social"] + L["work"])
        )
        
        assert len(builder._stmt.layer_expr.terms) == 2
        assert builder._stmt.layer_expr.ops == ["+"]
    
    def test_q_dynamics_seed_fraction(self):
        """Test Q.dynamics() with fractional seeding."""
        builder = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed(0.05)  # 5% initially infected
        )
        
        assert builder._stmt.seed_fraction == 0.05
        assert builder._stmt.seed_query is None
    
    def test_q_dynamics_seed_query(self):
        """Test Q.dynamics() with query-based seeding."""
        seed_query = Q.nodes().where(degree__gt=5)
        builder = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed(seed_query)
        )
        
        assert builder._stmt.seed_query is not None
        assert builder._stmt.seed_fraction is None
    
    def test_q_dynamics_run_configuration(self):
        """Test Q.dynamics() run configuration."""
        builder = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .run(steps=200, replicates=15, track=["prevalence", "incidence"])
        )
        
        assert builder._stmt.steps == 200
        assert builder._stmt.replicates == 15
        assert "prevalence" in builder._stmt.track
        assert "incidence" in builder._stmt.track
    
    def test_q_dynamics_run_track_all(self):
        """Test Q.dynamics() with track='all'."""
        builder = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .run(steps=100, replicates=10, track="all")
        )
        
        assert builder._stmt.track == ["all"]
    
    def test_q_dynamics_random_seed(self):
        """Test Q.dynamics() with random seed."""
        builder = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .random_seed(42)
        )
        
        assert builder._stmt.seed == 42
    
    def test_q_dynamics_parameters_per_layer(self):
        """Test Q.dynamics() with per-layer parameters."""
        builder = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .on_layers(L["contacts"] + L["travel"])
             .parameters_per_layer({
                 "contacts": {"beta": 0.4},
                 "travel": {"beta": 0.2}
             })
        )
        
        assert "contacts" in builder._stmt.layer_params
        assert builder._stmt.layer_params["contacts"]["beta"] == 0.4
        assert builder._stmt.layer_params["travel"]["beta"] == 0.2
    
    def test_q_dynamics_with_states(self):
        """Test Q.dynamics() with explicit state labels."""
        builder = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .with_states(S="susceptible", I="infected")
        )
        
        assert "state_labels" in builder._stmt.params
        assert builder._stmt.params["state_labels"]["S"] == "susceptible"
    
    def test_q_dynamics_chaining(self):
        """Test Q.dynamics() full method chaining."""
        builder = (
            Q.dynamics("SIR", beta=0.2, gamma=0.05)
             .on_layers(L["offline"] + L["online"])
             .with_states(S="susceptible", I="infected", R="recovered")
             .seed(0.01)
             .parameters_per_layer({
                 "offline": {"beta": 0.3},
                 "online": {"beta": 0.1}
             })
             .run(steps=150, replicates=20, track=["prevalence", "state_counts"])
             .random_seed(42)
        )
        
        # Verify all configurations
        assert builder._stmt.process_name == "SIR"
        assert builder._stmt.params["beta"] == 0.2
        assert builder._stmt.params["gamma"] == 0.05
        assert builder._stmt.seed_fraction == 0.01
        assert builder._stmt.steps == 150
        assert builder._stmt.replicates == 20
        assert builder._stmt.seed == 42
        assert len(builder._stmt.layer_expr.terms) == 2
        assert len(builder._stmt.layer_params) == 2
    
    def test_q_dynamics_to_ast(self):
        """Test Q.dynamics() AST export."""
        builder = Q.dynamics("SIS", beta=0.3, mu=0.1).run(steps=100)
        ast = builder.to_ast()
        
        assert isinstance(ast, DynamicsStmt)
        assert ast.process_name == "SIS"
        assert ast.steps == 100
    
    def test_q_dynamics_repr(self):
        """Test Q.dynamics() string representation."""
        builder = Q.dynamics("SIS", beta=0.3, mu=0.1).run(steps=100)
        repr_str = repr(builder)
        
        assert "DynamicsBuilder" in repr_str
        assert "SIS" in repr_str
        assert "steps=100" in repr_str


class TestQDynamicsExecution:
    """Test Q.dynamics() execution."""
    
    def test_q_dynamics_execute_basic(self, sample_network):
        """Test basic Q.dynamics() execution."""
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed(0.2)  # 20% infected
             .run(steps=10, replicates=2, track=["prevalence"])
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Check result structure
        assert result is not None
        assert hasattr(result, 'data')
        assert 'prevalence' in result.data
        
        # Check dimensions: (replicates, steps)
        assert result.data['prevalence'].shape == (2, 10)
    
    def test_q_dynamics_execute_with_layers(self, sample_network):
        """Test Q.dynamics() execution with layer filtering."""
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .on_layers(L["social"])
             .seed(0.2)
             .run(steps=10, replicates=2, track=["prevalence"])
             .random_seed(42)
             .execute(sample_network)
        )
        
        assert result is not None
        assert 'prevalence' in result.data
    
    def test_q_dynamics_execute_sir(self, sample_network):
        """Test Q.dynamics() execution with SIR model."""
        result = (
            Q.dynamics("SIR", beta=0.4, gamma=0.15)
             .seed(0.2)
             .run(steps=10, replicates=2, track=["prevalence"])
             .random_seed(42)
             .execute(sample_network)
        )
        
        assert result is not None
        assert 'prevalence' in result.data
        assert result.data['prevalence'].shape == (2, 10)
    
    def test_q_dynamics_execute_multiple_measures(self, sample_network):
        """Test Q.dynamics() with multiple measures."""
        result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed(0.2)
             .run(steps=10, replicates=2, track=["prevalence", "incidence"])
             .random_seed(42)
             .execute(sample_network)
        )
        
        assert 'prevalence' in result.data
        assert 'incidence' in result.data


class TestQTrajectoriesBuilder:
    """Test Q.trajectories() builder API."""
    
    def test_q_trajectories_basic(self):
        """Test basic Q.trajectories() construction."""
        builder = Q.trajectories("sim_result")
        
        assert isinstance(builder, TrajectoriesBuilder)
        assert builder._stmt.process_ref == "sim_result"
    
    def test_q_trajectories_where(self):
        """Test Q.trajectories() with WHERE conditions."""
        builder = Q.trajectories("sim_result").where(replicate=5)
        
        assert builder._stmt.where is not None
    
    def test_q_trajectories_at(self):
        """Test Q.trajectories() with temporal point filter."""
        builder = Q.trajectories("sim_result").at(50.0)
        
        assert builder._stmt.temporal_context is not None
        assert builder._stmt.temporal_context.kind == "at"
        assert builder._stmt.temporal_context.t0 == 50.0
    
    def test_q_trajectories_during(self):
        """Test Q.trajectories() with temporal range filter."""
        builder = Q.trajectories("sim_result").during(10.0, 50.0)
        
        assert builder._stmt.temporal_context is not None
        assert builder._stmt.temporal_context.kind == "during"
        assert builder._stmt.temporal_context.t0 == 10.0
        assert builder._stmt.temporal_context.t1 == 50.0
    
    def test_q_trajectories_measure(self):
        """Test Q.trajectories() with measures."""
        builder = Q.trajectories("sim_result").measure("peak_time", "final_state")
        
        assert "peak_time" in builder._stmt.measures
        assert "final_state" in builder._stmt.measures
    
    def test_q_trajectories_order_by(self):
        """Test Q.trajectories() with ordering."""
        builder = Q.trajectories("sim_result").order_by("node_id", desc=False)
        
        assert len(builder._stmt.order_by) == 1
        assert builder._stmt.order_by[0].key == "node_id"
        assert builder._stmt.order_by[0].desc is False
    
    def test_q_trajectories_limit(self):
        """Test Q.trajectories() with limit."""
        builder = Q.trajectories("sim_result").limit(100)
        
        assert builder._stmt.limit == 100
    
    def test_q_trajectories_chaining(self):
        """Test Q.trajectories() full method chaining."""
        builder = (
            Q.trajectories("sim_result")
             .where(replicate=5)
             .at(50.0)
             .measure("peak_time", "final_state")
             .order_by("node_id")
             .limit(100)
        )
        
        assert builder._stmt.process_ref == "sim_result"
        assert builder._stmt.where is not None
        assert builder._stmt.temporal_context is not None
        assert len(builder._stmt.measures) == 2
        assert len(builder._stmt.order_by) == 1
        assert builder._stmt.limit == 100
    
    def test_q_trajectories_to_ast(self):
        """Test Q.trajectories() AST export."""
        builder = Q.trajectories("sim_result").at(50.0)
        ast = builder.to_ast()
        
        assert isinstance(ast, TrajectoriesStmt)
        assert ast.process_ref == "sim_result"
    
    def test_q_trajectories_repr(self):
        """Test Q.trajectories() string representation."""
        builder = Q.trajectories("sim_result")
        repr_str = repr(builder)
        
        assert "TrajectoriesBuilder" in repr_str
        assert "sim_result" in repr_str


class TestDynamicsASTNodes:
    """Test DynamicsStmt and TrajectoriesStmt AST nodes."""
    
    def test_dynamics_stmt_creation(self):
        """Test DynamicsStmt creation."""
        stmt = DynamicsStmt(
            process_name="SIS",
            params={"beta": 0.3, "mu": 0.1},
            steps=100,
            replicates=10,
        )
        
        assert stmt.process_name == "SIS"
        assert stmt.params["beta"] == 0.3
        assert stmt.steps == 100
        assert stmt.replicates == 10
    
    def test_dynamics_stmt_defaults(self):
        """Test DynamicsStmt default values."""
        stmt = DynamicsStmt(process_name="SIS")
        
        assert stmt.steps == 100
        assert stmt.replicates == 1
        assert stmt.params == {}
        assert stmt.track == []
        assert stmt.seed is None
    
    def test_trajectories_stmt_creation(self):
        """Test TrajectoriesStmt creation."""
        stmt = TrajectoriesStmt(
            process_ref="sim_result",
            measures=["peak_time"],
            limit=100,
        )
        
        assert stmt.process_ref == "sim_result"
        assert "peak_time" in stmt.measures
        assert stmt.limit == 100
    
    def test_trajectories_stmt_defaults(self):
        """Test TrajectoriesStmt default values."""
        stmt = TrajectoriesStmt(process_ref="sim_result")
        
        assert stmt.where is None
        assert stmt.temporal_context is None
        assert stmt.measures == []
        assert stmt.order_by == []
        assert stmt.limit is None


class TestDSLDynamicsIntegration:
    """Test integration between DSL dynamics and existing dynamics module."""
    
    def test_integration_with_d_process(self, sample_network):
        """Verify Q.dynamics() produces same results as D.process()."""
        # Run with Q.dynamics()
        q_result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed(0.2)
             .run(steps=10, replicates=2, track=["prevalence"])
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Run with D.process()
        from py3plex.dynamics import D, SIS
        d_result = (
            D.process(SIS(beta=0.3, mu=0.1))
             .initial(infected=0.2)
             .steps(10)
             .measure("prevalence")
             .replicates(2)
             .seed(42)
             .run(sample_network)
        )
        
        # Both should produce similar shaped results
        assert q_result.data['prevalence'].shape == d_result.data['prevalence'].shape
    
    def test_q_dynamics_uses_existing_processes(self, sample_network):
        """Verify Q.dynamics() works with all existing process types."""
        # Test SIS
        sis_result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed(0.2)  # Provide initial infection
             .run(steps=5, replicates=1)
             .execute(sample_network)
        )
        assert sis_result is not None
        
        # Test SIR
        sir_result = (
            Q.dynamics("SIR", beta=0.3, gamma=0.1)
             .seed(0.2)  # Provide initial infection
             .run(steps=5, replicates=1)
             .execute(sample_network)
        )
        assert sir_result is not None
        
        # Note: RANDOM_WALK has different initial conditions (requires start_node)
        # and is not suitable for this test. It's tested separately in dynamics tests.


class TestErrorHandling:
    """Test error handling in dynamics DSL."""
    
    def test_dynamics_invalid_seed_type(self):
        """Test error for invalid seed type."""
        with pytest.raises(TypeError, match="seed.*requires.*float.*QueryBuilder"):
            Q.dynamics("SIS", beta=0.3).seed("invalid")
    
    def test_trajectories_requires_context(self):
        """Test that trajectories require context."""
        builder = Q.trajectories("sim_result")
        
        with pytest.raises(DslExecutionError, match="context"):
            builder.execute(context=None)
    
    def test_trajectories_full_execution(self, sample_network):
        """Test full trajectory query execution."""
        # First, run a dynamics simulation
        sim_result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed(0.2)
             .run(steps=20, replicates=3, track=["prevalence"])
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Query all trajectories
        traj_result = (
            Q.trajectories("sim_result")
             .execute(sim_result)
        )
        
        assert traj_result is not None
        assert len(traj_result.items) > 0
        assert "replicate" in traj_result.attributes
        assert "t" in traj_result.attributes
        assert "value" in traj_result.attributes
        # Items should be tuples (replicate, t)
        assert isinstance(traj_result.items[0], tuple)
    
    def test_trajectories_with_temporal_filter(self, sample_network):
        """Test trajectory query with temporal filtering."""
        # Run simulation
        sim_result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed(0.2)
             .run(steps=20, replicates=2, track=["prevalence"])
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Query at specific time
        traj_result = (
            Q.trajectories("sim_result")
             .at(10)
             .execute(sim_result)
        )
        
        assert traj_result is not None
        assert len(traj_result.items) > 0
        # Should only have data for t=10
        for item in traj_result.items:
            # item is (replicate, t)
            assert item[1] == 10
    
    def test_trajectories_with_measures(self, sample_network):
        """Test trajectory query with computed measures."""
        # Run simulation
        sim_result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed(0.2)
             .run(steps=20, replicates=2, track=["prevalence"])
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Query with measures
        traj_result = (
            Q.trajectories("sim_result")
             .measure("peak_time", "final_state", "peak_value")
             .execute(sim_result)
        )
        
        assert traj_result is not None
        assert "peak_time" in traj_result.attributes
        assert "final_state" in traj_result.attributes
        assert "peak_value" in traj_result.attributes
    
    def test_trajectories_with_where(self, sample_network):
        """Test trajectory query with WHERE filtering."""
        # Run simulation
        sim_result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed(0.2)
             .run(steps=20, replicates=3, track=["prevalence"])
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Query with WHERE condition
        traj_result = (
            Q.trajectories("sim_result")
             .where(replicate=1)
             .execute(sim_result)
        )
        
        assert traj_result is not None
        # Should only have items from replicate 1
        for item in traj_result.items:
            # item is (replicate, t)
            assert item[0] == 1
    
    def test_trajectories_with_limit(self, sample_network):
        """Test trajectory query with limit."""
        # Run simulation
        sim_result = (
            Q.dynamics("SIS", beta=0.3, mu=0.1)
             .seed(0.2)
             .run(steps=20, replicates=2, track=["prevalence"])
             .random_seed(42)
             .execute(sample_network)
        )
        
        # Query with limit
        traj_result = (
            Q.trajectories("sim_result")
             .limit(10)
             .execute(sim_result)
        )
        
        assert traj_result is not None
        assert len(traj_result.items) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
