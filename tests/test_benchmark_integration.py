"""Integration test for complete benchmark workflow.

Tests the end-to-end benchmark execution with real algorithms.
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import B, L


class TestBenchmarkIntegration:
    """Integration tests for benchmark execution."""

    @pytest.fixture
    def test_network(self):
        """Create a small test network."""
        net = multinet.multi_layer_network(directed=False)

        # Add 15 nodes
        nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(15)]
        net.add_nodes(nodes)

        # Create two groups with denser connections
        # Group 1: 0-7
        for i in range(8):
            for j in range(i + 1, 8):
                if (i + j) % 2 == 0:  # 50% connectivity
                    net.add_edges([{
                        "source": f"N{i}",
                        "target": f"N{j}",
                        "source_type": "layer1",
                        "target_type": "layer1",
                    }])

        # Group 2: 8-14
        for i in range(8, 15):
            for j in range(i + 1, 15):
                if (i + j) % 2 == 0:
                    net.add_edges([{
                        "source": f"N{i}",
                        "target": f"N{j}",
                        "source_type": "layer1",
                        "target_type": "layer1",
                    }])

        # Sparse between groups
        net.add_edges([{
            "source": "N3",
            "target": "N10",
            "source_type": "layer1",
            "target_type": "layer1",
        }])

        return net

    @pytest.mark.integration
    def test_simple_benchmark_execution(self, test_network):
        """Test simple benchmark with Louvain."""
        res = (
            B.community()
            .on(test_network)
            .layers(L["layer1"])
            .algorithms("louvain")
            .metrics("modularity", "n_communities", "runtime_ms")
            .repeat(1, seed=42)
            .execute()
        )

        # Check result structure
        assert res is not None
        assert len(res.items) > 0

        # Check DataFrame conversion
        df = res.to_pandas()
        assert "algorithm" in df.columns
        assert "modularity" in df.columns
        assert "runtime_ms" in df.columns

        # Check benchmark helper
        assert hasattr(res, "benchmark")

    @pytest.mark.integration
    def test_grid_search_benchmark(self, test_network):
        """Test benchmark with grid search."""
        res = (
            B.community()
            .on(test_network)
            .layers(L["layer1"])
            .algorithms(
                ("louvain", {"grid": {"resolution": [0.8, 1.0, 1.2]}})
            )
            .metrics("modularity", "runtime_ms")
            .repeat(1, seed=42)
            .execute()
        )

        df = res.to_pandas()

        # Should have 3 configs
        assert len(df) == 3

        # Check configs are different
        assert len(df["config_id"].unique()) == 3

    @pytest.mark.integration
    def test_benchmark_with_repeats(self, test_network):
        """Test benchmark with multiple repeats."""
        res = (
            B.community()
            .on(test_network)
            .algorithms("louvain")
            .metrics("modularity")
            .repeat(3, seed=42)
            .execute()
        )

        df = res.to_pandas()

        # Should have 3 repeats
        assert len(df) == 3
        assert "repeat_id" in df.columns
        assert set(df["repeat_id"]) == {0, 1, 2}

    @pytest.mark.integration
    @pytest.mark.slow
    def test_benchmark_helper_methods(self, test_network):
        """Test benchmark helper views."""
        res = (
            B.community()
            .on(test_network)
            .algorithms(
                "louvain",
                ("louvain", {"resolution": 1.2}),
            )
            .metrics("modularity", "runtime_ms")
            .repeat(2, seed=42)
            .execute()
        )

        # Test runs()
        runs = res.benchmark.runs()
        assert len(runs) == 4  # 2 algorithms x 2 repeats

        # Test protocol()
        protocol = res.benchmark.protocol()
        assert protocol["repeat"] == 2
        assert protocol["seed"] == 42

        # Test summary() - may be empty if not implemented
        summary = res.benchmark.summary()
        # Just check it doesn't crash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
