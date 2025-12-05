"""Tests for dynamics module.

Tests cover:
- AST classes (SimulationStmt, InitialSpec)
- Process specifications (SIS, SIR, RandomWalk)
- Python builder API (D.process())
- Simulation execution
- SimulationResult exports
- Measure registry
- Error handling with suggestions
"""

import pytest
import numpy as np
from py3plex.core import multinet
from py3plex.dynamics import (
    # AST classes
    SimulationStmt,
    InitialSpec,
    Simulation,
    # Builder API
    D,
    SimulationBuilder,
    # Processes
    ProcessSpec,
    SIS,
    SIR,
    RandomWalk,
    get_process,
    list_processes,
    register_process,
    # Result
    SimulationResult,
    # Executor
    run_simulation,
    # Registry
    measure_registry,
    # Errors
    DynamicsError,
    UnknownProcessError,
    MissingInitialConditionError,
    UnknownMeasureError,
    SimulationConfigError,
    # Serializer
    sim_ast_to_dsl,
)
from py3plex.dsl import L, Q


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


class TestASTClasses:
    """Test AST dataclasses."""

    def test_initial_spec_constant(self):
        """Test InitialSpec with constant value."""
        spec = InitialSpec(constant=0.01)
        assert spec.constant == 0.01
        assert spec.query is None

    def test_initial_spec_query(self):
        """Test InitialSpec with query."""
        from py3plex.dsl.ast import SelectStmt, Target
        query = SelectStmt(target=Target.NODES)
        spec = InitialSpec(query=query)
        assert spec.constant is None
        assert spec.query is not None

    def test_initial_spec_validation(self):
        """Test InitialSpec validation."""
        with pytest.raises(ValueError, match="must have either"):
            InitialSpec()  # Neither constant nor query

    def test_simulation_stmt(self):
        """Test SimulationStmt creation."""
        stmt = SimulationStmt(
            process_name="SIS",
            steps=100,
            replicates=10,
        )
        assert stmt.process_name == "SIS"
        assert stmt.steps == 100
        assert stmt.replicates == 10
        assert stmt.measures == []

    def test_simulation(self):
        """Test Simulation wrapper."""
        stmt = SimulationStmt(process_name="SIS", steps=100)
        sim = Simulation(stmt=stmt)
        assert sim.stmt == stmt
        assert sim.dsl_version == "1.0"


class TestProcessSpec:
    """Test ProcessSpec classes."""

    def test_sis_defaults(self):
        """Test SIS default parameters."""
        assert SIS.name == "SIS"
        assert SIS.params["beta"] == 0.3
        assert SIS.params["mu"] == 0.1
        assert "infected" in SIS.required_initial

    def test_sir_defaults(self):
        """Test SIR default parameters."""
        assert SIR.name == "SIR"
        assert SIR.params["beta"] == 0.2
        assert SIR.params["gamma"] == 0.05

    def test_random_walk_defaults(self):
        """Test RandomWalk default parameters."""
        assert RandomWalk.name == "RANDOM_WALK"
        assert RandomWalk.params["teleport"] == 0.05
        assert "start_node" in RandomWalk.required_initial

    def test_process_spec_callable(self):
        """Test ProcessSpec is callable for parameter override."""
        custom = SIS(beta=0.5, mu=0.2)
        assert custom.params["beta"] == 0.5
        assert custom.params["mu"] == 0.2
        assert custom.name == "SIS"

    def test_list_processes(self):
        """Test listing registered processes."""
        processes = list_processes()
        assert "SIS" in processes
        assert "SIR" in processes
        assert "RANDOM_WALK" in processes

    def test_get_process(self):
        """Test getting process by name."""
        spec = get_process("SIS")
        assert spec.name == "SIS"

    def test_get_unknown_process(self):
        """Test getting unknown process raises error."""
        with pytest.raises(UnknownProcessError) as exc_info:
            get_process("SISS")  # typo
        assert "SIS" in str(exc_info.value)  # suggestion


class TestBuilderAPI:
    """Test Python builder API."""

    def test_d_process(self):
        """Test D.process() factory."""
        builder = D.process(SIS)
        assert isinstance(builder, SimulationBuilder)
        assert builder._stmt.process_name == "SIS"

    def test_d_process_with_params(self):
        """Test D.process() with parameter overrides."""
        builder = D.process(SIS(beta=0.5))
        assert builder._stmt.params["beta"] == 0.5

    def test_d_process_by_name(self):
        """Test D.process() with string name."""
        builder = D.process("SIR")
        assert builder._stmt.process_name == "SIR"

    def test_steps(self):
        """Test steps() method."""
        builder = D.process(SIS).steps(100)
        assert builder._stmt.steps == 100

    def test_replicates(self):
        """Test replicates() method."""
        builder = D.process(SIS).replicates(20)
        assert builder._stmt.replicates == 20

    def test_seed(self):
        """Test seed() method."""
        builder = D.process(SIS).seed(42)
        assert builder._stmt.seed == 42

    def test_measure(self):
        """Test measure() method."""
        builder = D.process(SIS).measure("prevalence", "incidence")
        assert "prevalence" in builder._stmt.measures
        assert "incidence" in builder._stmt.measures

    def test_initial_constant(self):
        """Test initial() with constant value."""
        builder = D.process(SIS).initial(infected=0.01)
        assert "infected" in builder._stmt.initial
        assert builder._stmt.initial["infected"].constant == 0.01

    def test_initial_query(self):
        """Test initial() with query builder."""
        query = Q.nodes().where(layer="social")
        builder = D.process(SIS).initial(infected=query)
        assert "infected" in builder._stmt.initial
        assert builder._stmt.initial["infected"].query is not None

    def test_on_layers(self):
        """Test on_layers() method."""
        builder = D.process(SIS).on_layers(L["social"] + L["work"])
        assert builder._stmt.layer_expr is not None

    def test_coupling(self):
        """Test coupling() method."""
        builder = D.process(SIS).coupling(node_replicas="strong")
        assert builder._stmt.coupling["node_replicas"] == "strong"

    def test_with_params(self):
        """Test with_params() method."""
        builder = D.process(SIS).with_params(beta=0.5)
        assert builder._stmt.params["beta"] == 0.5

    def test_to(self):
        """Test to() export target."""
        builder = D.process(SIS).to("pandas")
        assert builder._stmt.export_target == "pandas"

    def test_chaining(self):
        """Test method chaining."""
        builder = (
            D.process(SIS(beta=0.3))
             .on_layers(L["social"])
             .initial(infected=0.01)
             .steps(100)
             .measure("prevalence")
             .replicates(10)
             .seed(42)
        )
        assert builder._stmt.process_name == "SIS"
        assert builder._stmt.steps == 100
        assert builder._stmt.replicates == 10

    def test_to_ast(self):
        """Test to_ast() method."""
        builder = D.process(SIS).steps(100)
        stmt = builder.to_ast()
        assert isinstance(stmt, SimulationStmt)
        assert stmt.steps == 100

    def test_to_dsl(self):
        """Test to_dsl() method."""
        builder = (
            D.process(SIS(beta=0.3, mu=0.1))
             .initial(infected=0.01)
             .steps(100)
             .measure("prevalence")
        )
        dsl = builder.to_dsl()
        assert "SIMULATE SIS" in dsl
        assert "FOR 100 STEPS" in dsl
        assert "MEASURE prevalence" in dsl


class TestSimulationExecution:
    """Test simulation execution."""

    def test_run_sis_basic(self, sample_network):
        """Test basic SIS simulation."""
        sim = (
            D.process(SIS(beta=0.3, mu=0.1))
             .initial(infected=0.5)
             .steps(10)
             .measure("prevalence")
             .seed(42)
        )
        result = sim.run(sample_network)
        
        assert isinstance(result, SimulationResult)
        assert result.process_name == "SIS"
        assert "prevalence" in result.measures

    def test_run_sis_replicates(self, sample_network):
        """Test SIS with multiple replicates."""
        sim = (
            D.process(SIS)
             .initial(infected=0.5)
             .steps(10)
             .measure("prevalence")
             .replicates(5)
             .seed(42)
        )
        result = sim.run(sample_network)
        
        assert result.meta["replicates"] == 5
        df = result.to_pandas("prevalence")
        assert df["replicate"].nunique() == 5

    def test_run_sis_layer_filter(self, sample_network):
        """Test SIS with layer filtering."""
        sim = (
            D.process(SIS)
             .on_layers(L["social"])
             .initial(infected=0.5)
             .steps(10)
             .measure("prevalence")
             .seed(42)
        )
        result = sim.run(sample_network)
        
        # Should only have 3 nodes (social layer)
        assert result.meta["network_nodes"] == 3

    def test_run_sir(self, sample_network):
        """Test SIR simulation."""
        sim = (
            D.process(SIR(beta=0.3, gamma=0.1))
             .initial(infected=0.5)
             .steps(20)
             .measure("prevalence")
             .seed(42)
        )
        result = sim.run(sample_network)
        
        assert result.process_name == "SIR"

    def test_run_random_walk(self, sample_network):
        """Test random walk simulation."""
        sim = (
            D.process(RandomWalk(teleport=0.1))
             .initial(start_node="A")
             .steps(50)
             .measure("visit_frequency")
             .seed(42)
        )
        result = sim.run(sample_network)
        
        assert result.process_name == "RANDOM_WALK"

    def test_run_multiple_measures(self, sample_network):
        """Test collecting multiple measures."""
        sim = (
            D.process(SIS)
             .initial(infected=0.5)
             .steps(10)
             .measure("prevalence", "incidence")
             .seed(42)
        )
        result = sim.run(sample_network)
        
        assert "prevalence" in result.measures
        assert "incidence" in result.measures

    def test_reproducibility(self, sample_network):
        """Test that same seed gives same results."""
        sim = (
            D.process(SIS)
             .initial(infected=0.5)
             .steps(10)
             .measure("prevalence")
             .seed(42)
        )
        
        result1 = sim.run(sample_network)
        result2 = sim.run(sample_network)
        
        np.testing.assert_array_equal(
            result1.data["prevalence"],
            result2.data["prevalence"]
        )


class TestSimulationResult:
    """Test SimulationResult class."""

    def test_result_creation(self):
        """Test SimulationResult creation."""
        result = SimulationResult(
            process_name="SIS",
            measures=["prevalence"],
            data={"prevalence": np.array([[0.1, 0.2, 0.3]])},
            meta={"steps": 3, "replicates": 1}
        )
        assert result.process_name == "SIS"
        assert "prevalence" in result.measures

    def test_to_pandas(self, sample_network):
        """Test to_pandas export."""
        sim = (
            D.process(SIS)
             .initial(infected=0.5)
             .steps(10)
             .measure("prevalence")
             .seed(42)
        )
        result = sim.run(sample_network)
        df = result.to_pandas("prevalence")
        
        assert "replicate" in df.columns
        assert "t" in df.columns
        assert "value" in df.columns

    def test_to_pandas_all_measures(self, sample_network):
        """Test to_pandas with all measures."""
        sim = (
            D.process(SIS)
             .initial(infected=0.5)
             .steps(10)
             .measure("prevalence", "incidence")
             .seed(42)
        )
        result = sim.run(sample_network)
        dfs = result.to_pandas()
        
        assert isinstance(dfs, dict)
        assert "prevalence" in dfs
        assert "incidence" in dfs

    def test_to_dict(self, sample_network):
        """Test to_dict export."""
        sim = (
            D.process(SIS)
             .initial(infected=0.5)
             .steps(5)
             .measure("prevalence")
             .seed(42)
        )
        result = sim.run(sample_network)
        d = result.to_dict()
        
        assert d["process_name"] == "SIS"
        assert "data" in d
        assert "meta" in d

    def test_summary(self, sample_network):
        """Test summary method."""
        sim = (
            D.process(SIS)
             .initial(infected=0.5)
             .steps(10)
             .measure("prevalence")
             .replicates(5)
             .seed(42)
        )
        result = sim.run(sample_network)
        summary = result.summary()
        
        assert "measures" in summary
        assert "prevalence" in summary["measures"]
        assert "mean" in summary["measures"]["prevalence"]

    def test_repr(self, sample_network):
        """Test __repr__."""
        sim = D.process(SIS).initial(infected=0.5).steps(10).measure("prevalence").seed(42)
        result = sim.run(sample_network)
        s = repr(result)
        assert "SimulationResult" in s
        assert "SIS" in s


class TestMeasureRegistry:
    """Test measure registry."""

    def test_sis_measures(self):
        """Test SIS measures are registered."""
        measures = measure_registry.list_measures("SIS")
        assert "prevalence" in measures
        assert "incidence" in measures
        assert "prevalence_by_layer" in measures

    def test_sir_measures(self):
        """Test SIR measures are registered."""
        measures = measure_registry.list_measures("SIR")
        assert "prevalence" in measures
        assert "R_t" in measures

    def test_random_walk_measures(self):
        """Test random walk measures."""
        measures = measure_registry.list_measures("RANDOM_WALK")
        assert "visit_frequency" in measures

    def test_global_measures(self):
        """Test global measures available for all processes."""
        measures = measure_registry.list_measures("SIS")
        assert "state_counts" in measures

    def test_has_measure(self):
        """Test has() method."""
        assert measure_registry.has("SIS", "prevalence")
        assert not measure_registry.has("SIS", "nonexistent")

    def test_get_unknown_measure(self):
        """Test getting unknown measure raises error."""
        with pytest.raises(UnknownMeasureError) as exc_info:
            measure_registry.get("SIS", "prevelance")  # typo
        assert "prevalence" in str(exc_info.value)  # suggestion


class TestErrorHandling:
    """Test error handling."""

    def test_unknown_process_error(self):
        """Test UnknownProcessError."""
        with pytest.raises(UnknownProcessError) as exc_info:
            D.process("SISS")  # typo
        err = exc_info.value
        assert "SISS" in str(err)
        assert "SIS" in str(err)  # suggestion

    def test_missing_initial_error(self, sample_network):
        """Test MissingInitialConditionError."""
        sim = D.process(SIS).steps(10).measure("prevalence")
        # Missing 'infected' initial condition
        with pytest.raises(MissingInitialConditionError):
            sim.run(sample_network)

    def test_unknown_measure_error(self, sample_network):
        """Test UnknownMeasureError."""
        sim = (
            D.process(SIS)
             .initial(infected=0.5)
             .steps(10)
             .measure("nonexistent")
        )
        with pytest.raises(UnknownMeasureError):
            sim.run(sample_network)

    def test_invalid_steps(self, sample_network):
        """Test invalid steps configuration."""
        sim = D.process(SIS).initial(infected=0.5).steps(0).measure("prevalence")
        with pytest.raises(SimulationConfigError):
            sim.run(sample_network)

    def test_invalid_replicates(self, sample_network):
        """Test invalid replicates configuration."""
        sim = D.process(SIS).initial(infected=0.5).steps(10).replicates(0).measure("prevalence")
        with pytest.raises(SimulationConfigError):
            sim.run(sample_network)


class TestDSLSerializer:
    """Test DSL serialization."""

    def test_simple_simulation(self):
        """Test serializing simple simulation."""
        sim = D.process(SIS).initial(infected=0.01).steps(100)
        dsl = sim.to_dsl()
        assert "SIMULATE SIS" in dsl
        assert "FOR 100 STEPS" in dsl

    def test_with_measures(self):
        """Test serializing with MEASURE clause."""
        sim = D.process(SIS).initial(infected=0.01).steps(100).measure("prevalence", "incidence")
        dsl = sim.to_dsl()
        assert "MEASURE prevalence, incidence" in dsl

    def test_with_replicates(self):
        """Test serializing with REPLICATES clause."""
        sim = D.process(SIS).initial(infected=0.01).steps(100).replicates(20)
        dsl = sim.to_dsl()
        assert "REPLICATES 20" in dsl

    def test_with_seed(self):
        """Test serializing with SEED clause."""
        sim = D.process(SIS).initial(infected=0.01).steps(100).seed(42)
        dsl = sim.to_dsl()
        assert "SEED 42" in dsl

    def test_with_layers(self):
        """Test serializing with ON clause."""
        sim = D.process(SIS).on_layers(L["social"]).initial(infected=0.01).steps(100)
        dsl = sim.to_dsl()
        assert "ON" in dsl
        assert "LAYER" in dsl

    def test_with_coupling(self):
        """Test serializing with COUPLING clause."""
        sim = D.process(SIS).coupling(node_replicas="strong").initial(infected=0.01).steps(100)
        dsl = sim.to_dsl()
        assert "COUPLING" in dsl


class TestIntegration:
    """Integration tests for dynamics module."""

    def test_complete_workflow(self, sample_network):
        """Test complete simulation workflow."""
        # Build simulation
        sim = (
            D.process(SIS(beta=0.3, mu=0.1))
             .on_layers(L["social"])
             .initial(infected=0.5)
             .steps(20)
             .measure("prevalence", "incidence")
             .replicates(10)
             .seed(42)
        )
        
        # Execute
        result = sim.run(sample_network)
        
        # Verify result
        assert result.process_name == "SIS"
        assert len(result.measures) == 2
        
        # Export to pandas
        df_prev = result.to_pandas("prevalence")
        assert len(df_prev) == 200  # 10 replicates * 20 steps
        
        # Get summary
        summary = result.summary()
        assert summary["replicates"] == 10
        assert summary["steps"] == 20

    def test_query_based_initial(self, sample_network):
        """Test using query for initial condition."""
        # Use query to select initial infected nodes
        query = Q.nodes().where(layer="social")
        
        sim = (
            D.process(SIS)
             .initial(infected=query)
             .steps(10)
             .measure("prevalence")
             .seed(42)
        )
        
        result = sim.run(sample_network)
        assert result.process_name == "SIS"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
