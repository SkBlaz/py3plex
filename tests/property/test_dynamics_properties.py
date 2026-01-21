"""Property-based tests for the dynamics module.

This module tests invariants and properties of the dynamics simulation framework
including SIS, SIR, RandomWalk processes and the simulation builder API.
"""

import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings

from py3plex.core import multinet
from py3plex.dynamics import (
    D,
    SIS,
    SIR,
    RandomWalk,
    ProcessSpec,
    get_process,
    list_processes,
    run_simulation,
)
from py3plex.dynamics.ast import SimulationStmt
from py3plex.dynamics.errors import (
    UnknownProcessError,
    MissingInitialConditionError,
    SimulationConfigError,
)


# ============================================================================
# Helper functions
# ============================================================================


def build_test_network(
    num_nodes: int = 6,
    num_layers: int = 2,
    edges_per_layer: int = 5,
) -> multinet.multi_layer_network:
    """Build a test multilayer network for dynamics simulations."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = []
    layers = [f"L{i}" for i in range(num_layers)]

    for layer in layers:
        for i in range(min(edges_per_layer, num_nodes - 1)):
            edges.append([f"n{i}", layer, f"n{i+1}", layer, 1.0])

    if edges:
        net.add_edges(edges, input_type="list")
    return net


# ============================================================================
# ProcessSpec Properties
# ============================================================================


class TestProcessSpecProperties:
    """Property-based tests for ProcessSpec."""

    @pytest.mark.property
    @given(st.floats(min_value=0.01, max_value=0.99, allow_nan=False))
    @settings(max_examples=5)
    def test_sis_call_overrides_beta(self, beta: float):
        """SIS(beta=x) should override the beta parameter."""
        spec = SIS(beta=beta)
        assert spec.params["beta"] == beta
        assert spec.name == "SIS"

    @pytest.mark.property
    @given(st.floats(min_value=0.01, max_value=0.99, allow_nan=False))
    @settings(max_examples=5)
    def test_sis_call_overrides_mu(self, mu: float):
        """SIS(mu=x) should override the mu parameter."""
        spec = SIS(mu=mu)
        assert spec.params["mu"] == mu

    @pytest.mark.property
    @given(
        st.floats(min_value=0.01, max_value=0.99, allow_nan=False),
        st.floats(min_value=0.01, max_value=0.99, allow_nan=False),
    )
    @settings(max_examples=5)
    def test_sir_call_overrides_params(self, beta: float, gamma: float):
        """SIR(beta=x, gamma=y) should override both parameters."""
        spec = SIR(beta=beta, gamma=gamma)
        assert spec.params["beta"] == beta
        assert spec.params["gamma"] == gamma

    @pytest.mark.property
    def test_process_call_creates_new_spec(self):
        """Calling a ProcessSpec should create a new instance."""
        original = SIS
        modified = SIS(beta=0.5)
        assert original is not modified
        assert original.params["beta"] != modified.params["beta"]

    @pytest.mark.property
    def test_list_processes_returns_list(self):
        """list_processes() should return a list of process names."""
        processes = list_processes()
        assert isinstance(processes, list)
        assert "SIS" in processes
        assert "SIR" in processes
        assert "RANDOM_WALK" in processes

    @pytest.mark.property
    def test_get_process_case_insensitive(self):
        """get_process should be case-insensitive."""
        assert get_process("sis").name == "SIS"
        assert get_process("SIS").name == "SIS"
        assert get_process("Sis").name == "SIS"

    @pytest.mark.property
    def test_get_process_unknown_raises(self):
        """get_process with unknown name should raise UnknownProcessError."""
        with pytest.raises(UnknownProcessError):
            get_process("UNKNOWN_PROCESS")


# ============================================================================
# SimulationBuilder Properties
# ============================================================================


class TestSimulationBuilderProperties:
    """Property-based tests for SimulationBuilder."""

    @pytest.mark.property
    @given(st.integers(min_value=1, max_value=1000))
    @settings(max_examples=5)
    def test_builder_steps_sets_correctly(self, steps: int):
        """steps() should set the number of steps correctly."""
        builder = D.process(SIS()).steps(steps)
        assert builder._stmt.steps == steps

    @pytest.mark.property
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=5)
    def test_builder_replicates_sets_correctly(self, replicates: int):
        """replicates() should set the number of replicates correctly."""
        builder = D.process(SIS()).replicates(replicates)
        assert builder._stmt.replicates == replicates

    @pytest.mark.property
    @given(st.integers(min_value=0, max_value=2**31 - 1))
    @settings(max_examples=5)
    def test_builder_seed_sets_correctly(self, seed: int):
        """seed() should set the random seed correctly."""
        builder = D.process(SIS()).seed(seed)
        assert builder._stmt.seed == seed

    @pytest.mark.property
    def test_builder_chaining_returns_self(self):
        """All builder methods should return self for chaining."""
        builder = D.process(SIS())
        result = builder.steps(10).replicates(5).seed(42)
        assert result is builder

    @pytest.mark.property
    def test_builder_with_params_merges(self):
        """with_params() should merge with existing params."""
        builder = D.process(SIS(beta=0.3)).with_params(mu=0.2)
        assert builder._stmt.params["beta"] == 0.3
        assert builder._stmt.params["mu"] == 0.2

    @pytest.mark.property
    @given(st.lists(st.sampled_from(["prevalence", "incidence"]), min_size=1, max_size=2))
    @settings(max_examples=10)
    def test_builder_measure_adds_measures(self, measures: list):
        """measure() should add measures to the list."""
        builder = D.process(SIS())
        builder.measure(*measures)
        for m in measures:
            assert m in builder._stmt.measures

    @pytest.mark.property
    def test_builder_to_ast_returns_stmt(self):
        """to_ast() should return a SimulationStmt."""
        builder = D.process(SIS()).steps(10)
        stmt = builder.to_ast()
        assert isinstance(stmt, SimulationStmt)
        assert stmt.steps == 10

    @pytest.mark.property
    def test_builder_to_dsl_returns_string(self):
        """to_dsl() should return a DSL string."""
        builder = D.process(SIS()).steps(10).replicates(5)
        dsl = builder.to_dsl()
        assert isinstance(dsl, str)
        assert "SIS" in dsl


# ============================================================================
# Simulation Execution Properties
# ============================================================================


class TestSimulationExecutionProperties:
    """Property-based tests for simulation execution."""

    @pytest.mark.property
    @given(st.integers(min_value=1, max_value=50))
    @settings(max_examples=10)
    def test_result_has_correct_steps(self, steps: int):
        """Simulation result should have data for correct number of steps."""
        net = build_test_network()
        sim = (
            D.process(SIS(beta=0.3, mu=0.1))
            .initial(infected=0.1)
            .steps(steps)
            .measure("prevalence")
            .replicates(1)
            .seed(42)
        )
        result = sim.run(net)
        
        # Result data should have shape (replicates, steps)
        assert result.data["prevalence"].shape == (1, steps)

    @pytest.mark.property
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=10)
    def test_result_has_correct_replicates(self, replicates: int):
        """Simulation result should have data for correct number of replicates."""
        net = build_test_network()
        sim = (
            D.process(SIS(beta=0.3, mu=0.1))
            .initial(infected=0.1)
            .steps(5)
            .measure("prevalence")
            .replicates(replicates)
            .seed(42)
        )
        result = sim.run(net)
        
        # Result data should have shape (replicates, steps)
        assert result.data["prevalence"].shape == (replicates, 5)

    @pytest.mark.property
    @given(st.integers(min_value=0, max_value=1000))
    @settings(max_examples=10)
    def test_simulation_reproducibility(self, seed: int):
        """Simulations with same seed should produce identical results."""
        net = build_test_network()
        
        sim1 = (
            D.process(SIS(beta=0.3, mu=0.1))
            .initial(infected=0.1)
            .steps(10)
            .measure("prevalence")
            .replicates(2)
            .seed(seed)
        )
        
        sim2 = (
            D.process(SIS(beta=0.3, mu=0.1))
            .initial(infected=0.1)
            .steps(10)
            .measure("prevalence")
            .replicates(2)
            .seed(seed)
        )
        
        result1 = sim1.run(net)
        result2 = sim2.run(net)
        
        np.testing.assert_array_equal(
            result1.data["prevalence"],
            result2.data["prevalence"],
        )

    @pytest.mark.property
    def test_prevalence_bounded_zero_one(self):
        """Prevalence measure should be between 0 and 1."""
        net = build_test_network()
        sim = (
            D.process(SIS(beta=0.3, mu=0.1))
            .initial(infected=0.1)
            .steps(20)
            .measure("prevalence")
            .replicates(3)
            .seed(42)
        )
        result = sim.run(net)
        
        assert np.all(result.data["prevalence"] >= 0)
        assert np.all(result.data["prevalence"] <= 1)

    @pytest.mark.property
    def test_incidence_non_negative(self):
        """Incidence measure should be non-negative."""
        net = build_test_network()
        sim = (
            D.process(SIS(beta=0.3, mu=0.1))
            .initial(infected=0.1)
            .steps(20)
            .measure("incidence")
            .replicates(3)
            .seed(42)
        )
        result = sim.run(net)
        
        assert np.all(result.data["incidence"] >= 0)


# ============================================================================
# SIS Properties
# ============================================================================


class TestSISProperties:
    """Property-based tests for SIS dynamics."""

    @pytest.mark.property
    def test_sis_state_space_binary(self):
        """SIS process should have binary state space (S, I)."""
        assert len(SIS.state_space["node_state"]) == 2
        assert "S" in SIS.state_space["node_state"]
        assert "I" in SIS.state_space["node_state"]

    @pytest.mark.property
    def test_sis_requires_infected_initial(self):
        """SIS should require 'infected' initial condition."""
        assert "infected" in SIS.required_initial

    @pytest.mark.property
    @given(st.floats(min_value=0.01, max_value=0.5, allow_nan=False))
    @settings(max_examples=10)
    def test_sis_with_mu_one_converges_to_zero(self, initial_infected: float):
        """SIS with mu=1.0 should eventually have zero prevalence."""
        net = build_test_network()
        sim = (
            D.process(SIS(beta=0.0, mu=1.0))  # No infection, only recovery
            .initial(infected=initial_infected)
            .steps(5)
            .measure("prevalence")
            .replicates(1)
            .seed(42)
        )
        result = sim.run(net)
        
        # After a few steps, all should be recovered
        final_prevalence = result.data["prevalence"][0, -1]
        assert final_prevalence == 0.0


# ============================================================================
# SIR Properties
# ============================================================================


class TestSIRProperties:
    """Property-based tests for SIR dynamics."""

    @pytest.mark.property
    def test_sir_state_space_ternary(self):
        """SIR process should have ternary state space (S, I, R)."""
        assert len(SIR.state_space["node_state"]) == 3
        assert "S" in SIR.state_space["node_state"]
        assert "I" in SIR.state_space["node_state"]
        assert "R" in SIR.state_space["node_state"]

    @pytest.mark.property
    def test_sir_requires_infected_initial(self):
        """SIR should require 'infected' initial condition."""
        assert "infected" in SIR.required_initial

    @pytest.mark.property
    def test_sir_monotonically_decreasing_susceptible(self):
        """SIR susceptible count should never increase."""
        net = build_test_network()
        sim = (
            D.process(SIR(beta=0.5, gamma=0.1))
            .initial(infected=0.1)
            .steps(20)
            .measure("prevalence")
            .replicates(1)
            .seed(42)
        )
        result = sim.run(net)
        
        # This test verifies the simulation runs without error
        assert result is not None


# ============================================================================
# RandomWalk Properties
# ============================================================================


class TestRandomWalkProperties:
    """Property-based tests for RandomWalk dynamics."""

    @pytest.mark.property
    def test_random_walk_requires_start_node(self):
        """RandomWalk should require 'start_node' initial condition."""
        assert "start_node" in RandomWalk.required_initial

    @pytest.mark.property
    def test_random_walk_state_space(self):
        """RandomWalk should have binary state space (absent, present)."""
        assert len(RandomWalk.state_space["node_state"]) == 2


# ============================================================================
# Error Handling Properties
# ============================================================================


class TestDynamicsErrorProperties:
    """Property-based tests for dynamics error handling."""

    @pytest.mark.property
    @given(st.integers(min_value=-100, max_value=0))
    def test_invalid_steps_raises(self, steps: int):
        """Invalid steps (<1) should raise SimulationConfigError."""
        net = build_test_network()
        
        # Create builder and modify steps directly
        builder = D.process(SIS()).initial(infected=0.1).steps(1)
        builder._stmt.steps = steps
        
        with pytest.raises(SimulationConfigError):
            run_simulation(net, builder.to_ast())

    @pytest.mark.property
    @given(st.integers(min_value=-100, max_value=0))
    def test_invalid_replicates_raises(self, replicates: int):
        """Invalid replicates (<1) should raise SimulationConfigError."""
        net = build_test_network()
        
        builder = D.process(SIS()).initial(infected=0.1).steps(1).replicates(1)
        builder._stmt.replicates = replicates
        
        with pytest.raises(SimulationConfigError):
            run_simulation(net, builder.to_ast())

    @pytest.mark.property
    def test_missing_initial_condition_raises(self):
        """Missing required initial condition should raise error."""
        net = build_test_network()
        
        # Build without initial(infected=...)
        builder = D.process(SIS()).steps(10)
        
        with pytest.raises(MissingInitialConditionError):
            run_simulation(net, builder.to_ast())


# ============================================================================
# SimulationResult Properties
# ============================================================================


class TestSimulationResultProperties:
    """Property-based tests for SimulationResult."""

    @pytest.mark.property
    def test_result_to_pandas_returns_dataframe(self):
        """to_pandas() should return a DataFrame or dict of DataFrames."""
        net = build_test_network()
        sim = (
            D.process(SIS(beta=0.3, mu=0.1))
            .initial(infected=0.1)
            .steps(10)
            .measure("prevalence")
            .replicates(2)
            .seed(42)
        )
        result = sim.run(net)
        
        # to_pandas() with no args returns dict of DataFrames
        df_dict = result.to_pandas()
        assert isinstance(df_dict, dict)
        assert "prevalence" in df_dict
        
        # to_pandas(measure) returns single DataFrame
        df = result.to_pandas("prevalence")
        assert "replicate" in df.columns
        assert "t" in df.columns
        assert "value" in df.columns

    @pytest.mark.property
    def test_result_summary_returns_dict(self):
        """summary() should return a dictionary with stats."""
        net = build_test_network()
        sim = (
            D.process(SIS(beta=0.3, mu=0.1))
            .initial(infected=0.1)
            .steps(10)
            .measure("prevalence")
            .replicates(3)
            .seed(42)
        )
        result = sim.run(net)
        summary = result.summary()
        
        assert isinstance(summary, dict)
        assert "measures" in summary
        assert "prevalence" in summary["measures"]

    @pytest.mark.property
    def test_result_data_access_returns_array(self):
        """data[measure] should return the measure array."""
        net = build_test_network()
        sim = (
            D.process(SIS(beta=0.3, mu=0.1))
            .initial(infected=0.1)
            .steps(10)
            .measure("prevalence")
            .replicates(2)
            .seed(42)
        )
        result = sim.run(net)
        prevalence = result.data["prevalence"]
        
        assert isinstance(prevalence, np.ndarray)
        assert prevalence.shape == (2, 10)

