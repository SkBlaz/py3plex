"""Tests for DSL extensions.

Tests cover:
- Multilayer network comparison (COMPARE)
- Null models & randomization (NULLMODEL)
- Path queries & flow (PATH)
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import (
    # New AST classes
    CompareStmt,
    NullModelStmt,
    PathStmt,
    ExtendedQuery,
    LayerExpr,
    LayerTerm,
    # Builder API
    C,
    CompareBuilder,
    N,
    NullModelBuilder,
    P,
    PathBuilder,
    L,
)
from py3plex.comparison import (
    compare_networks,
    multiplex_jaccard,
    degree_change,
    ComparisonResult,
    metric_registry,
)
from py3plex.nullmodels import (
    generate_null_model,
    NullModelResult,
    model_registry,
)
from py3plex.paths import (
    find_paths,
    shortest_path,
    random_walk,
    PathResult,
    path_registry,
)


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)

    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'Alice', 'type': 'work'},
        {'source': 'Bob', 'type': 'work'},
        {'source': 'Diana', 'type': 'work'},
    ]
    network.add_nodes(nodes)

    edges = [
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
        {'source': 'Bob', 'target': 'Diana', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    ]
    network.add_edges(edges)

    return network


@pytest.fixture
def sample_network_2():
    """Create a second sample network for comparison."""
    network = multinet.multi_layer_network(directed=False)

    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'Alice', 'type': 'work'},
        {'source': 'Bob', 'type': 'work'},
    ]
    network.add_nodes(nodes)

    edges = [
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    ]
    network.add_edges(edges)

    return network


# ==============================================================================
# Part A: Multilayer Network Comparison Tests
# ==============================================================================


class TestCompareAST:
    """Test COMPARE AST classes."""

    def test_compare_stmt_creation(self):
        """Test CompareStmt creation."""
        stmt = CompareStmt(
            network_a="baseline",
            network_b="treatment",
            metric_name="multiplex_jaccard",
        )
        assert stmt.network_a == "baseline"
        assert stmt.network_b == "treatment"
        assert stmt.metric_name == "multiplex_jaccard"
        assert stmt.measures == []
        assert stmt.export_target is None

    def test_compare_stmt_with_layers(self):
        """Test CompareStmt with layer expression."""
        layer_expr = LayerExpr(
            terms=[LayerTerm("social"), LayerTerm("work")],
            ops=["+"]
        )
        stmt = CompareStmt(
            network_a="A",
            network_b="B",
            metric_name="degree_change",
            layer_expr=layer_expr,
            measures=["global_distance", "per_node_difference"],
        )
        assert stmt.layer_expr.get_layer_names() == ["social", "work"]
        assert "global_distance" in stmt.measures


class TestCompareBuilder:
    """Test C (Compare) builder API."""

    def test_c_compare_factory(self):
        """Test C.compare() factory."""
        builder = C.compare("baseline", "treatment")
        assert isinstance(builder, CompareBuilder)
        assert builder._stmt.network_a == "baseline"
        assert builder._stmt.network_b == "treatment"

    def test_using_method(self):
        """Test .using() method."""
        builder = C.compare("A", "B").using("degree_change")
        assert builder._stmt.metric_name == "degree_change"

    def test_on_layers_method(self):
        """Test .on_layers() method."""
        builder = C.compare("A", "B").on_layers(L["social"] + L["work"])
        assert builder._stmt.layer_expr is not None
        assert len(builder._stmt.layer_expr.terms) == 2

    def test_measure_method(self):
        """Test .measure() method."""
        builder = C.compare("A", "B").measure("global_distance", "layerwise_distance")
        assert "global_distance" in builder._stmt.measures
        assert "layerwise_distance" in builder._stmt.measures

    def test_to_method(self):
        """Test .to() method."""
        builder = C.compare("A", "B").to("pandas")
        assert builder._stmt.export_target == "pandas"

    def test_chaining(self):
        """Test method chaining."""
        builder = (
            C.compare("baseline", "treatment")
             .using("multiplex_jaccard")
             .on_layers(L["social"])
             .measure("global_distance")
             .to("pandas")
        )
        assert builder._stmt.network_a == "baseline"
        assert builder._stmt.metric_name == "multiplex_jaccard"

    def test_to_ast(self):
        """Test .to_ast() method."""
        builder = C.compare("A", "B").using("multiplex_jaccard")
        ast = builder.to_ast()
        assert isinstance(ast, CompareStmt)
        assert ast.network_a == "A"


class TestCompareMetrics:
    """Test comparison metrics."""

    def test_multiplex_jaccard(self, sample_network, sample_network_2):
        """Test multiplex_jaccard metric."""
        result = multiplex_jaccard(sample_network, sample_network_2)
        
        assert "global_distance" in result
        assert "layerwise_distance" in result
        assert 0 <= result["global_distance"] <= 1

    def test_degree_change(self, sample_network, sample_network_2):
        """Test degree_change metric."""
        result = degree_change(sample_network, sample_network_2)
        
        assert "global_distance" in result
        assert "per_node_difference" in result

    def test_metric_registry(self):
        """Test metric registry."""
        assert metric_registry.has("multiplex_jaccard")
        assert metric_registry.has("degree_change")
        assert metric_registry.has("layer_edge_overlap")
        assert not metric_registry.has("unknown_metric")


class TestCompareNetworks:
    """Test compare_networks function."""

    def test_basic_comparison(self, sample_network, sample_network_2):
        """Test basic network comparison."""
        result = compare_networks(
            sample_network,
            sample_network_2,
            metric="multiplex_jaccard",
        )
        
        assert isinstance(result, ComparisonResult)
        assert result.metric_name == "multiplex_jaccard"
        assert result.global_distance is not None

    def test_comparison_with_layers(self, sample_network, sample_network_2):
        """Test comparison with specific layers."""
        result = compare_networks(
            sample_network,
            sample_network_2,
            metric="multiplex_jaccard",
            layers=["social"],
        )
        
        assert result.global_distance is not None

    def test_comparison_result_exports(self, sample_network, sample_network_2):
        """Test ComparisonResult export methods."""
        result = compare_networks(
            sample_network,
            sample_network_2,
            metric="multiplex_jaccard",
            measures=["global_distance", "layerwise_distance"],
        )
        
        # to_pandas
        df = result.to_pandas()
        assert "metric" in df.columns
        assert "global_distance" in df.columns
        
        # to_dict
        d = result.to_dict()
        assert "metric_name" in d
        assert "global_distance" in d
        
        # to_json
        json_str = result.to_json()
        assert "multiplex_jaccard" in json_str

    def test_builder_execute(self, sample_network, sample_network_2):
        """Test executing comparison via builder."""
        networks = {"A": sample_network, "B": sample_network_2}
        
        result = (
            C.compare("A", "B")
             .using("multiplex_jaccard")
             .measure("global_distance")
             .execute(networks)
        )
        
        assert isinstance(result, ComparisonResult)
        assert result.global_distance is not None


# ==============================================================================
# Part B: Null Models & Randomization Tests
# ==============================================================================


class TestNullModelAST:
    """Test NULLMODEL AST classes."""

    def test_nullmodel_stmt_creation(self):
        """Test NullModelStmt creation."""
        stmt = NullModelStmt(model_type="configuration")
        
        assert stmt.model_type == "configuration"
        assert stmt.num_samples == 1
        assert stmt.seed is None
        assert stmt.params == {}

    def test_nullmodel_stmt_with_params(self):
        """Test NullModelStmt with parameters."""
        stmt = NullModelStmt(
            model_type="configuration",
            num_samples=100,
            seed=42,
            params={"preserve_degree": True},
        )
        
        assert stmt.num_samples == 100
        assert stmt.seed == 42
        assert stmt.params["preserve_degree"] is True


class TestNullModelBuilder:
    """Test N (NullModel) builder API."""

    def test_n_model_factory(self):
        """Test N.model() factory."""
        builder = N.model("configuration")
        assert isinstance(builder, NullModelBuilder)
        assert builder._stmt.model_type == "configuration"

    def test_convenience_factories(self):
        """Test convenience factory methods."""
        assert N.configuration()._stmt.model_type == "configuration"
        assert N.erdos_renyi()._stmt.model_type == "erdos_renyi"
        assert N.layer_shuffle()._stmt.model_type == "layer_shuffle"
        assert N.edge_swap()._stmt.model_type == "edge_swap"

    def test_samples_method(self):
        """Test .samples() method."""
        builder = N.configuration().samples(100)
        assert builder._stmt.num_samples == 100

    def test_seed_method(self):
        """Test .seed() method."""
        builder = N.configuration().seed(42)
        assert builder._stmt.seed == 42

    def test_with_params_method(self):
        """Test .with_params() method."""
        builder = N.configuration().with_params(preserve_degree=True)
        assert builder._stmt.params["preserve_degree"] is True

    def test_on_layers_method(self):
        """Test .on_layers() method."""
        builder = N.configuration().on_layers(L["social"])
        assert builder._stmt.layer_expr is not None

    def test_chaining(self):
        """Test method chaining."""
        builder = (
            N.configuration()
             .on_layers(L["social"])
             .samples(50)
             .seed(42)
             .with_params(preserve_degree=True)
        )
        
        assert builder._stmt.num_samples == 50
        assert builder._stmt.seed == 42


class TestNullModelGeneration:
    """Test null model generation."""

    def test_configuration_model(self, sample_network):
        """Test configuration model generation."""
        result = generate_null_model(
            sample_network,
            model="configuration",
            num_samples=3,
            seed=42,
        )
        
        assert isinstance(result, NullModelResult)
        assert result.num_samples == 3
        assert result.seed == 42
        assert len(result.samples) == 3

    def test_erdos_renyi_model(self, sample_network):
        """Test Erdős-Rényi model generation."""
        result = generate_null_model(
            sample_network,
            model="erdos_renyi",
            num_samples=2,
            seed=42,
        )
        
        assert result.num_samples == 2

    def test_layer_shuffle_model(self, sample_network):
        """Test layer shuffle model generation."""
        result = generate_null_model(
            sample_network,
            model="layer_shuffle",
            num_samples=2,
            seed=42,
        )
        
        assert result.num_samples == 2

    def test_edge_swap_model(self, sample_network):
        """Test edge swap model generation."""
        result = generate_null_model(
            sample_network,
            model="edge_swap",
            num_samples=2,
            seed=42,
        )
        
        assert result.num_samples == 2

    def test_model_registry(self):
        """Test model registry."""
        assert model_registry.has("configuration")
        assert model_registry.has("erdos_renyi")
        assert model_registry.has("layer_shuffle")
        assert model_registry.has("edge_swap")
        assert not model_registry.has("unknown_model")

    def test_result_iteration(self, sample_network):
        """Test iterating over NullModelResult."""
        result = generate_null_model(
            sample_network,
            model="configuration",
            num_samples=3,
            seed=42,
        )
        
        count = 0
        for sample in result:
            count += 1
            assert sample is not None
        
        assert count == 3

    def test_result_indexing(self, sample_network):
        """Test indexing NullModelResult."""
        result = generate_null_model(
            sample_network,
            model="configuration",
            num_samples=3,
            seed=42,
        )
        
        assert result[0] is not None
        assert result[1] is not None
        assert result[2] is not None

    def test_builder_execute(self, sample_network):
        """Test executing null model via builder."""
        result = (
            N.configuration()
             .samples(5)
             .seed(42)
             .execute(sample_network)
        )
        
        assert isinstance(result, NullModelResult)
        assert result.num_samples == 5


# ==============================================================================
# Part C: Path Queries & Flow Tests
# ==============================================================================


class TestPathAST:
    """Test PATH AST classes."""

    def test_path_stmt_creation(self):
        """Test PathStmt creation."""
        stmt = PathStmt(
            path_type="shortest",
            source="Alice",
            target="Bob",
        )
        
        assert stmt.path_type == "shortest"
        assert stmt.source == "Alice"
        assert stmt.target == "Bob"
        assert stmt.cross_layer is False

    def test_path_stmt_random_walk(self):
        """Test PathStmt for random walk."""
        stmt = PathStmt(
            path_type="random_walk",
            source="Alice",
            params={"steps": 100, "teleport": 0.1},
        )
        
        assert stmt.path_type == "random_walk"
        assert stmt.target is None
        assert stmt.params["steps"] == 100


class TestPathBuilder:
    """Test P (Path) builder API."""

    def test_p_shortest_factory(self):
        """Test P.shortest() factory."""
        builder = P.shortest("Alice", "Bob")
        assert isinstance(builder, PathBuilder)
        assert builder._stmt.path_type == "shortest"
        assert builder._stmt.source == "Alice"
        assert builder._stmt.target == "Bob"

    def test_p_all_paths_factory(self):
        """Test P.all_paths() factory."""
        builder = P.all_paths("Alice", "Bob")
        assert builder._stmt.path_type == "all"

    def test_p_random_walk_factory(self):
        """Test P.random_walk() factory."""
        builder = P.random_walk("Alice")
        assert builder._stmt.path_type == "random_walk"
        assert builder._stmt.target is None

    def test_p_flow_factory(self):
        """Test P.flow() factory."""
        builder = P.flow("Alice", "Bob")
        assert builder._stmt.path_type == "flow"

    def test_crossing_layers_method(self):
        """Test .crossing_layers() method."""
        builder = P.shortest("Alice", "Bob").crossing_layers()
        assert builder._stmt.cross_layer is True
        
        builder2 = P.shortest("Alice", "Bob").crossing_layers(False)
        assert builder2._stmt.cross_layer is False

    def test_on_layers_method(self):
        """Test .on_layers() method."""
        builder = P.shortest("Alice", "Bob").on_layers(L["social"])
        assert builder._stmt.layer_expr is not None

    def test_with_params_method(self):
        """Test .with_params() method."""
        builder = P.random_walk("Alice").with_params(steps=100, teleport=0.1)
        assert builder._stmt.params["steps"] == 100
        assert builder._stmt.params["teleport"] == 0.1

    def test_limit_method(self):
        """Test .limit() method."""
        builder = P.all_paths("Alice", "Bob").limit(10)
        assert builder._stmt.limit == 10

    def test_chaining(self):
        """Test method chaining."""
        builder = (
            P.shortest("Alice", "Bob")
             .on_layers(L["social"] + L["work"])
             .crossing_layers()
             .limit(5)
        )
        
        assert builder._stmt.cross_layer is True
        assert builder._stmt.limit == 5


class TestPathAlgorithms:
    """Test path finding algorithms."""

    def test_shortest_path(self, sample_network):
        """Test shortest path finding."""
        result = find_paths(
            sample_network,
            source="Alice",
            target="Bob",
            path_type="shortest",
        )
        
        assert isinstance(result, PathResult)
        assert result.path_type == "shortest"
        assert result.num_paths >= 0

    def test_all_paths(self, sample_network):
        """Test finding all paths."""
        result = find_paths(
            sample_network,
            source="Alice",
            target="Charlie",
            path_type="all",
            limit=10,
        )
        
        assert result.path_type == "all"

    def test_random_walk(self, sample_network):
        """Test random walk."""
        result = find_paths(
            sample_network,
            source="Alice",
            path_type="random_walk",
            steps=50,
            seed=42,
        )
        
        assert result.path_type == "random_walk"
        assert len(result.visit_frequency) > 0

    def test_flow(self, sample_network):
        """Test flow analysis."""
        result = find_paths(
            sample_network,
            source="Alice",
            target="Charlie",
            path_type="flow",
        )
        
        assert result.path_type == "flow"

    def test_path_registry(self):
        """Test path algorithm registry."""
        assert path_registry.has("shortest")
        assert path_registry.has("all")
        assert path_registry.has("random_walk")
        assert path_registry.has("flow")
        assert not path_registry.has("unknown_algorithm")

    def test_result_exports(self, sample_network):
        """Test PathResult export methods."""
        result = find_paths(
            sample_network,
            source="Alice",
            target="Charlie",
            path_type="shortest",
        )
        
        # to_dict
        d = result.to_dict()
        assert "path_type" in d
        assert "source" in d
        assert "num_paths" in d

    def test_builder_execute(self, sample_network):
        """Test executing path query via builder."""
        result = (
            P.shortest("Alice", "Charlie")
             .on_layers(L["social"])
             .execute(sample_network)
        )
        
        assert isinstance(result, PathResult)


class TestPathResultProperties:
    """Test PathResult properties."""

    def test_num_paths_property(self, sample_network):
        """Test num_paths property."""
        result = find_paths(
            sample_network,
            source="Alice",
            target="Charlie",
            path_type="all",
        )
        
        assert result.num_paths == len(result.paths)

    def test_shortest_path_length_property(self, sample_network):
        """Test shortest_path_length property."""
        result = find_paths(
            sample_network,
            source="Alice",
            target="Charlie",
            path_type="all",
        )
        
        if result.num_paths > 0:
            assert result.shortest_path_length is not None
            assert result.shortest_path_length >= 0

    def test_iteration(self, sample_network):
        """Test iterating over paths."""
        result = find_paths(
            sample_network,
            source="Alice",
            target="Charlie",
            path_type="all",
        )
        
        for path in result:
            assert isinstance(path, list)


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestIntegration:
    """Integration tests for DSL extensions."""

    def test_compare_then_nullmodel(self, sample_network):
        """Test comparing a network with its null model."""
        # Generate null model
        null_result = generate_null_model(
            sample_network,
            model="configuration",
            num_samples=1,
            seed=42,
        )
        
        # Compare original with null model
        comparison = compare_networks(
            sample_network,
            null_result[0],
            metric="multiplex_jaccard",
        )
        
        assert comparison.global_distance is not None

    def test_path_then_compare(self, sample_network, sample_network_2):
        """Test finding paths and comparing networks."""
        # Find paths in both networks
        paths_1 = find_paths(
            sample_network,
            source="Alice",
            target="Bob",
            path_type="shortest",
        )
        
        paths_2 = find_paths(
            sample_network_2,
            source="Alice",
            target="Bob",
            path_type="shortest",
        )
        
        # Compare networks
        comparison = compare_networks(
            sample_network,
            sample_network_2,
            metric="multiplex_jaccard",
        )
        
        assert paths_1.num_paths >= 0
        assert paths_2.num_paths >= 0
        assert comparison.global_distance is not None

    def test_extended_query_ast(self):
        """Test ExtendedQuery AST creation."""
        compare_stmt = CompareStmt(
            network_a="A",
            network_b="B",
            metric_name="multiplex_jaccard",
        )
        
        query = ExtendedQuery(
            kind="compare",
            compare=compare_stmt,
        )
        
        assert query.kind == "compare"
        assert query.compare is not None
        assert query.select is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
