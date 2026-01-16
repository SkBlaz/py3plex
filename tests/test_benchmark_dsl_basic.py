"""Basic tests for benchmark DSL builder.

Tests the B.community() builder API and basic execution.
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import B, L
from py3plex.dsl.ast import BenchmarkNode, BenchmarkAlgorithmSpec, BenchmarkProtocol


class TestBenchmarkDSLBasic:
    """Basic DSL builder tests."""

    @pytest.fixture
    def simple_network(self):
        """Create a simple test network."""
        net = multinet.multi_layer_network(directed=False)

        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(10)]
        net.add_nodes(nodes)

        # Create a ring
        for i in range(10):
            net.add_edges([{
                "source": f"N{i}",
                "target": f"N{(i+1)%10}",
                "source_type": "layer1",
                "target_type": "layer1",
            }])

        return net

    def test_builder_exists(self):
        """Test that B.community() builder exists."""
        builder = B.community()
        assert builder is not None
        assert hasattr(builder, "on")
        assert hasattr(builder, "algorithms")
        assert hasattr(builder, "execute")

    def test_builder_fluent_api(self, simple_network):
        """Test fluent API chaining."""
        builder = (
            B.community()
            .on(simple_network)
            .layers(L["layer1"])
            .algorithms("louvain")
            .metrics("modularity")
            .repeat(1, seed=42)
        )

        assert builder is not None
        ast = builder.to_ast()
        assert isinstance(ast, BenchmarkNode)

    def test_ast_generation(self, simple_network):
        """Test AST generation from builder."""
        builder = (
            B.community()
            .on(simple_network)
            .algorithms("louvain", ("leiden", {"gamma": 1.0}))
            .metrics("modularity", "runtime_ms")
        )

        ast = builder.to_ast()

        assert ast.benchmark_type == "community"
        assert len(ast.algorithm_specs) == 2
        assert ast.algorithm_specs[0].algorithm == "louvain"
        assert ast.algorithm_specs[1].algorithm == "leiden"
        assert ast.metrics == ["modularity", "runtime_ms"]

    def test_grid_spec(self):
        """Test grid specification in algorithm spec."""
        builder = B.community().algorithms(
            ("louvain", {"grid": {"resolution": [0.8, 1.0, 1.2]}})
        )

        ast = builder.to_ast()
        spec = ast.algorithm_specs[0]

        assert spec.algorithm == "louvain"
        assert "grid" in spec.params
        assert spec.params["grid"]["resolution"] == [0.8, 1.0, 1.2]

    def test_protocol_settings(self):
        """Test protocol configuration."""
        builder = (
            B.community()
            .repeat(5, seed=42)
            .budget(runtime_ms=10_000, evals=100)
            .n_jobs(4)
        )

        ast = builder.to_ast()
        protocol = ast.protocol

        assert protocol.repeat == 5
        assert protocol.seed == 42
        assert protocol.budget_limit_ms == 10_000
        assert protocol.budget_limit_evals == 100
        assert protocol.n_jobs == 4

    def test_uq_configuration(self):
        """Test UQ configuration."""
        builder = B.community().uq(method="seed", n_samples=20, ci=0.95, seed=42)

        ast = builder.to_ast()
        uq = ast.protocol.uq_config

        assert uq is not None
        assert uq.method == "seed"
        assert uq.n_samples == 20
        assert uq.ci == 0.95
        assert uq.seed == 42

    def test_selection_modes(self):
        """Test selection mode configuration."""
        # Wins mode
        builder1 = B.community().select("wins")
        assert builder1.to_ast().selection_mode == "wins"

        # Pareto mode
        builder2 = B.community().select("pareto")
        assert builder2.to_ast().selection_mode == "pareto"

        # Weighted mode
        builder3 = B.community().select(("weighted", {"modularity": 0.6}))
        ast3 = builder3.to_ast()
        assert ast3.selection_mode == "weighted"
        assert ast3.selection_weights == {"modularity": 0.6}

    def test_default_metrics(self):
        """Test default metrics are added when not specified."""
        # Without UQ
        builder1 = B.community()
        ast1 = builder1.to_ast()
        assert "modularity" in ast1.metrics
        assert "runtime_ms" in ast1.metrics
        assert "stability" not in ast1.metrics

        # With UQ
        builder2 = B.community().uq(method="seed", n_samples=10)
        ast2 = builder2.to_ast()
        assert "stability" in ast2.metrics

    def test_validation_missing_dataset(self):
        """Test validation catches missing dataset."""
        builder = B.community().algorithms("louvain")

        with pytest.raises(ValueError, match="Must specify dataset"):
            builder.execute()

    def test_validation_missing_algorithms(self, simple_network):
        """Test validation catches missing algorithms."""
        builder = B.community().on(simple_network)

        with pytest.raises(ValueError, match="Must specify algorithms"):
            builder.execute()

    def test_protocol_factory(self):
        """Test protocol factory method."""
        protocol = B.protocol(repeat=5, seed=42, budget_ms=10_000)

        assert isinstance(protocol, BenchmarkProtocol)
        assert protocol.repeat == 5
        assert protocol.seed == 42
        assert protocol.budget_limit_ms == 10_000

    def test_using_protocol(self, simple_network):
        """Test using a pre-configured protocol."""
        protocol = B.protocol(repeat=3, seed=123)

        builder = (
            B.community()
            .on(simple_network)
            .algorithms("louvain")
            .using(protocol)
        )

        ast = builder.to_ast()
        assert ast.protocol.repeat == 3
        assert ast.protocol.seed == 123


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
