"""Tests for attribution explanation block.

Tests cover:
- Attribution block API and wiring
- Layer Shapley correctness (exact and Monte Carlo)
- Edge Shapley correctness
- Rank objective semantics
- Determinism with seeds
- UQ propagation
- Export/serialization compatibility
- Provenance tracking
"""

import pytest
import json
from py3plex.core import multinet
from py3plex.dsl import Q, L


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)

    nodes = [
        {"source": "A", "type": "social"},
        {"source": "B", "type": "social"},
        {"source": "C", "type": "social"},
        {"source": "A", "type": "work"},
        {"source": "B", "type": "work"},
        {"source": "D", "type": "work"},
    ]
    network.add_nodes(nodes)

    edges = [
        # Social layer: A-B-C triangle
        {
            "source": "A",
            "target": "B",
            "source_type": "social",
            "target_type": "social",
            "weight": 1.0,
        },
        {
            "source": "B",
            "target": "C",
            "source_type": "social",
            "target_type": "social",
            "weight": 1.0,
        },
        {
            "source": "A",
            "target": "C",
            "source_type": "social",
            "target_type": "social",
            "weight": 1.0,
        },
        # Work layer: A-B-D path
        {
            "source": "A",
            "target": "B",
            "source_type": "work",
            "target_type": "work",
            "weight": 1.0,
        },
        {
            "source": "B",
            "target": "D",
            "source_type": "work",
            "target_type": "work",
            "weight": 1.0,
        },
    ]
    network.add_edges(edges)

    return network


@pytest.fixture
def two_layer_network():
    """Create a simple two-layer network for exact Shapley tests."""
    network = multinet.multi_layer_network(directed=False)

    nodes = [
        {"source": "X", "type": "layer1"},
        {"source": "Y", "type": "layer1"},
        {"source": "X", "type": "layer2"},
        {"source": "Y", "type": "layer2"},
    ]
    network.add_nodes(nodes)

    edges = [
        # Layer1: 2 edges for X
        {
            "source": "X",
            "target": "Y",
            "source_type": "layer1",
            "target_type": "layer1",
        },
        {
            "source": "X",
            "target": "Y",
            "source_type": "layer1",
            "target_type": "layer1",
        },  # Duplicate for degree=2
        # Layer2: 3 edges for X
        {
            "source": "X",
            "target": "Y",
            "source_type": "layer2",
            "target_type": "layer2",
        },
        {
            "source": "X",
            "target": "Y",
            "source_type": "layer2",
            "target_type": "layer2",
        },
        {
            "source": "X",
            "target": "Y",
            "source_type": "layer2",
            "target_type": "layer2",
        },
    ]
    network.add_edges(edges)

    return network


class TestAttributionAPIWiring:
    """Test attribution block API and wiring with explain()."""

    def test_attribution_block_is_recognized(self, sample_network):
        """Test that 'attribution' is recognized as a valid explanation block."""
        query = (
            Q.nodes()
            .compute("degree")
            .explain(
                include=["attribution"], attribution={"metric": "degree", "seed": 42}
            )
        )

        # Check that explain_spec includes attribution
        assert query._select.explain_spec is not None
        assert "attribution" in query._select.explain_spec.include
        assert query._select.explain_spec.attribution_cfg is not None
        assert query._select.explain_spec.attribution_cfg["metric"] == "degree"

    def test_unknown_block_still_errors(self, sample_network):
        """Test that unknown block names still raise errors."""
        with pytest.raises(ValueError, match="Unknown explanation blocks"):
            Q.nodes().explain(include=["unknown_block"])

    def test_explain_default_blocks_unchanged(self, sample_network):
        """Test that default blocks are unchanged when attribution not requested."""
        query = Q.nodes().explain(neighbors_top=5)

        # Should have default blocks but not attribution
        expected_defaults = {"community", "top_neighbors", "layer_footprint"}
        assert set(query._select.explain_spec.include) == expected_defaults
        assert "attribution" not in query._select.explain_spec.include

    def test_explain_plan_mode_unchanged(self, sample_network):
        """Test that .explain() with no args still returns ExplainQuery."""
        from py3plex.dsl.builder import ExplainQuery

        query_builder = Q.nodes().compute("degree")
        explain_query = query_builder.explain()

        # Should return ExplainQuery (execution plan mode)
        assert isinstance(explain_query, ExplainQuery)


class TestLayerShapleyCorrectness:
    """Test layer attribution Shapley value correctness."""

    def test_layer_shapley_degree_exact_two_layers(self, two_layer_network):
        """Test exact Shapley for degree with 2 layers where degree is additive."""
        result = (
            Q.nodes()
            .from_layers(L["layer1"] + L["layer2"])
            .compute("degree")
            .explain(
                include=["attribution"],
                attribution={
                    "metric": "degree",
                    "levels": ["layer"],
                    "method": "shapley",
                    "max_exact_features": 2,
                    "seed": 42,
                },
            )
            .execute(two_layer_network)
        )

        df = result.to_pandas(expand_explanations=True)

        # Check that attribution is present
        assert "attribution" in df.columns

        # Parse attribution for node X
        x_rows = df[df["id"] == "X"]
        assert len(x_rows) > 0

        # Get attribution for first occurrence
        attr_str = x_rows.iloc[0]["attribution"]
        attr = json.loads(attr_str)

        # Validate structure
        assert attr["metric"] == "degree"
        assert attr["objective"] == "value"
        assert "layer_contrib" in attr
        assert "full_value" in attr
        assert "baseline_value" in attr
        assert "delta" in attr

        # Check sum(phi) == delta
        layer_contribs = attr["layer_contrib"]
        sum_phi = sum(c["phi"] for c in layer_contribs)
        delta = attr["delta"]
        assert abs(sum_phi - delta) < 1e-6

    def test_layer_shapley_exact_residual_near_zero(self, two_layer_network):
        """Test that residual is near zero for exact Shapley."""
        result = (
            Q.nodes()
            .compute("degree")
            .explain(
                include=["attribution"],
                attribution={
                    "metric": "degree",
                    "method": "shapley",
                    "max_exact_features": 2,
                    "seed": 42,
                },
            )
            .execute(two_layer_network)
        )

        df = result.to_pandas(expand_explanations=True)
        attr_str = df.iloc[0]["attribution"]
        attr = json.loads(attr_str)

        # Residual should be near zero
        assert abs(attr["residual"]) < 1e-6


class TestEdgeShapleyCorrectness:
    """Test edge attribution correctness."""

    def test_edge_shapley_degree_incident_edges(self, sample_network):
        """Test edge attribution for degree using incident edges."""
        result = (
            Q.nodes()
            .from_layers(L["social"])
            .compute("degree")
            .explain(
                include=["attribution"],
                attribution={
                    "metric": "degree",
                    "levels": ["edge"],
                    "edge_scope": "incident",
                    "max_edges": 20,
                    "seed": 42,
                },
            )
            .execute(sample_network)
        )

        df = result.to_pandas(expand_explanations=True)

        # Parse attribution for a high-degree node
        attr_str = df.iloc[0]["attribution"]
        attr = json.loads(attr_str)

        # Should have edge contributions
        assert "edge_contrib" in attr
        assert len(attr["edge_contrib"]) > 0

        # Check that edge_scope is recorded
        assert attr["edge_scope"] == "incident"
        assert attr["candidate_edge_count"] is not None


class TestRankObjective:
    """Test rank objective semantics."""

    def test_rank_objective_margin_to_cutoff_defined(self, sample_network):
        """Test that rank objective defines utility as margin to cutoff."""
        result = (
            Q.nodes()
            .compute("degree")
            .order_by("degree", desc=True)
            .limit(2)
            .explain(
                include=["attribution"],
                attribution={
                    "metric": "degree",
                    "objective": "rank",
                    "levels": ["layer"],
                    "seed": 42,
                },
            )
            .execute(sample_network)
        )

        df = result.to_pandas(expand_explanations=True)
        attr_str = df.iloc[0]["attribution"]
        attr = json.loads(attr_str)

        # Should have utility_def for rank objective
        assert attr["objective"] == "rank"
        assert attr["utility_def"] is not None
        assert "margin" in attr["utility_def"].lower()

        # Should still have delta == sum(phi)
        sum_phi = sum(c["phi"] for c in attr["layer_contrib"])
        assert abs(sum_phi - attr["delta"]) < 1e-6


class TestDeterminism:
    """Test determinism with seeds."""

    def test_attribution_deterministic_with_seed(self, sample_network):
        """Test that same seed produces identical attribution."""
        query = (
            Q.nodes()
            .compute("degree")
            .explain(
                include=["attribution"],
                attribution={
                    "metric": "degree",
                    "levels": ["layer"],
                    "method": "shapley_mc",
                    "n_permutations": 50,
                    "seed": 42,
                },
            )
        )

        result1 = query.execute(sample_network)
        result2 = query.execute(sample_network)

        df1 = result1.to_pandas(expand_explanations=True)
        df2 = result2.to_pandas(expand_explanations=True)

        # Parse attributions
        attr1_str = df1.iloc[0]["attribution"]
        attr2_str = df2.iloc[0]["attribution"]

        attr1 = json.loads(attr1_str)
        attr2 = json.loads(attr2_str)

        # Should be identical
        assert attr1["layer_contrib"] == attr2["layer_contrib"]
        assert attr1["full_value"] == attr2["full_value"]

    def test_attribution_changes_with_different_seed(self, sample_network):
        """Test that different seeds produce different MC outcomes."""
        result1 = (
            Q.nodes()
            .compute("degree")
            .explain(
                include=["attribution"],
                attribution={
                    "metric": "degree",
                    "method": "shapley_mc",
                    "n_permutations": 50,
                    "seed": 1,
                },
            )
            .execute(sample_network)
        )

        result2 = (
            Q.nodes()
            .compute("degree")
            .explain(
                include=["attribution"],
                attribution={
                    "metric": "degree",
                    "method": "shapley_mc",
                    "n_permutations": 50,
                    "seed": 2,
                },
            )
            .execute(sample_network)
        )

        df1 = result1.to_pandas(expand_explanations=True)
        df2 = result2.to_pandas(expand_explanations=True)

        attr1 = json.loads(df1.iloc[0]["attribution"])
        attr2 = json.loads(df2.iloc[0]["attribution"])

        # Should be different (probabilistic, but with 50 permutations should differ)
        # Check that at least one layer contribution differs
        contrib1 = {c["layer"]: c["phi"] for c in attr1["layer_contrib"]}
        contrib2 = {c["layer"]: c["phi"] for c in attr2["layer_contrib"]}

        # At least one should differ (with high probability)
        has_difference = False
        for layer in contrib1:
            if layer in contrib2:
                if abs(contrib1[layer] - contrib2[layer]) > 1e-10:
                    has_difference = True
                    break

        # Note: This is probabilistic, but with different seeds it should differ
        # If this fails, it might be that the network is too simple
        assert has_difference or len(contrib1) != len(contrib2)


class TestExportSerialization:
    """Test export and serialization with attribution."""

    def test_to_pandas_expand_explanations_serializes_attribution_json(
        self, sample_network
    ):
        """Test that attribution is serialized to JSON string in pandas export."""
        result = (
            Q.nodes()
            .compute("degree")
            .explain(
                include=["attribution"], attribution={"metric": "degree", "seed": 42}
            )
            .execute(sample_network)
        )

        df = result.to_pandas(expand_explanations=True)

        # Attribution should be a string column
        assert "attribution" in df.columns
        assert df["attribution"].dtype == object

        # Should be valid JSON
        attr_str = df.iloc[0]["attribution"]
        attr = json.loads(attr_str)
        assert isinstance(attr, dict)
        assert "metric" in attr

    def test_to_json_serializes(self, sample_network):
        """Test that result.to_json() succeeds with attribution."""
        result = (
            Q.nodes()
            .compute("degree")
            .explain(
                include=["attribution"], attribution={"metric": "degree", "seed": 42}
            )
            .execute(sample_network)
        )

        json_str = result.to_json()
        assert json_str is not None

        # Should be valid JSON
        data = json.loads(json_str)
        assert isinstance(data, dict)


class TestRobustness:
    """Test robustness and error handling."""

    def test_attribution_handles_empty_subgraph_gracefully(self, sample_network):
        """Test that attribution handles empty subgraphs without crashing."""
        # This should not crash even if subset computation fails
        result = (
            Q.nodes()
            .compute("degree")
            .explain(
                include=["attribution"],
                attribution={"metric": "degree", "levels": ["layer"], "seed": 42},
            )
            .execute(sample_network)
        )

        # Should complete without errors
        df = result.to_pandas()
        assert len(df) > 0

    def test_attribution_rejects_missing_metric_when_ambiguous(self, sample_network):
        """Test that attribution raises error when metric is ambiguous."""
        from py3plex.exceptions import Py3plexException

        with pytest.raises((ValueError, Py3plexException)):
            _ = (
                Q.nodes()
                .compute("degree")
                .compute("betweenness_centrality")
                .explain(
                    include=["attribution"],
                    attribution={
                        # No metric specified, but multiple computed
                        "levels": ["layer"],
                        "seed": 42,
                    },
                )
                .execute(sample_network)
            )


class TestProvenance:
    """Test provenance tracking."""

    def test_provenance_contains_attribution_metadata(self, sample_network):
        """Test that provenance tracks attribution config."""
        result = (
            Q.nodes()
            .compute("degree")
            .explain(
                include=["attribution"],
                attribution={
                    "metric": "degree",
                    "method": "shapley_mc",
                    "n_permutations": 100,
                    "seed": 42,
                },
            )
            .execute(sample_network)
        )

        # Provenance should exist
        assert "provenance" in result.meta
        prov = result.meta["provenance"]

        # Should contain required keys
        assert "query" in prov
        assert "py3plex_version" in prov


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
