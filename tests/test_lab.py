"""
Tests for py3plex.lab module.

Tests cover:
- ExperimentConfig dataclass functionality
- Step abstract base class behavior
- Pipeline execution flow
- Report generation and export
"""

import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
import networkx as nx

from py3plex.lab import ExperimentConfig, Step, Pipeline, Report


class TestExperimentConfig:
    """Test ExperimentConfig dataclass."""

    def test_basic_initialization(self):
        """Test basic config creation."""
        config = ExperimentConfig(name="test_experiment")
        assert config.name == "test_experiment"
        assert config.seed is None
        assert config.metadata is None

    def test_with_seed(self):
        """Test config with seed."""
        config = ExperimentConfig(name="test", seed=42)
        assert config.seed == 42

    def test_with_metadata(self):
        """Test config with metadata."""
        meta = {"description": "Test experiment", "version": 1}
        config = ExperimentConfig(name="test", metadata=meta)
        assert config.metadata == meta

    def test_to_dict_basic(self):
        """Test to_dict returns JSON-serializable dict."""
        config = ExperimentConfig(name="my_experiment")
        result = config.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "my_experiment"
        assert result["seed"] is None
        assert result["metadata"] is None

    def test_to_dict_full(self):
        """Test to_dict with all fields populated."""
        config = ExperimentConfig(
            name="full_experiment", seed=123, metadata={"key": "value", "count": 5}
        )
        result = config.to_dict()

        assert result["name"] == "full_experiment"
        assert result["seed"] == 123
        assert result["metadata"] == {"key": "value", "count": 5}


class TestStep:
    """Test Step abstract base class."""

    def test_abstract_class_cannot_be_instantiated(self):
        """Step cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Step("test_step")

    def test_concrete_step_requires_run_implementation(self):
        """Concrete step must implement run method."""

        class PartialStep(Step):
            pass

        with pytest.raises(TypeError):
            PartialStep("partial")

    def test_concrete_step_with_run(self):
        """Concrete step with run method can be instantiated."""

        class ConcreteStep(Step):
            def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
                return state

        step = ConcreteStep("my_step")
        assert step.name == "my_step"

    def test_step_run_receives_and_returns_state(self):
        """Step.run receives state and can modify it."""

        class ModifyingStep(Step):
            def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
                state["results"].append({"step": self.name, "value": 42})
                return state

        step = ModifyingStep("modify_step")
        config = ExperimentConfig(name="test")
        state = {"graph": None, "config": config, "results": []}

        result = step.run(state)

        assert len(result["results"]) == 1
        assert result["results"][0]["step"] == "modify_step"
        assert result["results"][0]["value"] == 42


class TestPipeline:
    """Test Pipeline class."""

    def test_initialization(self):
        """Test pipeline initialization."""
        config = ExperimentConfig(name="pipeline_test")

        class DummyStep(Step):
            def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
                return state

        steps = [DummyStep("step1"), DummyStep("step2")]
        pipeline = Pipeline(config=config, steps=steps)

        assert pipeline.config == config
        assert len(pipeline.steps) == 2

    def test_fit_run_initializes_state(self):
        """Test fit_run initializes state correctly."""
        config = ExperimentConfig(name="state_test", seed=42)

        class StateCheckStep(Step):
            def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
                assert "graph" in state
                assert "config" in state
                assert "results" in state
                assert state["config"] == config
                assert isinstance(state["results"], list)
                return state

        pipeline = Pipeline(config=config, steps=[StateCheckStep("check")])
        graph = nx.Graph()
        report = pipeline.fit_run(graph)

        assert isinstance(report, Report)

    def test_fit_run_executes_steps_in_order(self):
        """Test steps execute in sequence."""
        config = ExperimentConfig(name="order_test")
        execution_order = []

        class OrderStep(Step):
            def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
                execution_order.append(self.name)
                return state

        steps = [OrderStep("first"), OrderStep("second"), OrderStep("third")]
        pipeline = Pipeline(config=config, steps=steps)
        pipeline.fit_run(nx.Graph())

        assert execution_order == ["first", "second", "third"]

    def test_fit_run_accumulates_results(self):
        """Test results accumulate across steps."""
        config = ExperimentConfig(name="accumulate_test")

        class ResultStep(Step):
            def __init__(self, name: str, value: int):
                super().__init__(name)
                self.value = value

            def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
                state["results"].append({"step": self.name, "value": self.value})
                return state

        steps = [ResultStep("a", 1), ResultStep("b", 2), ResultStep("c", 3)]
        pipeline = Pipeline(config=config, steps=steps)
        report = pipeline.fit_run(nx.Graph())

        assert len(report.records) == 3
        assert report.records[0]["value"] == 1
        assert report.records[2]["value"] == 3

    def test_empty_pipeline(self):
        """Test pipeline with no steps."""
        config = ExperimentConfig(name="empty_test")
        pipeline = Pipeline(config=config, steps=[])
        report = pipeline.fit_run(nx.Graph())

        assert isinstance(report, Report)
        assert len(report.records) == 0


class TestReport:
    """Test Report class."""

    def test_initialization(self):
        """Test report initialization."""
        config = ExperimentConfig(name="report_test")
        records = [{"key": "value"}]
        report = Report(config=config, records=records)

        assert report.config == config
        assert report.records == records

    def test_from_state(self):
        """Test Report.from_state factory method."""
        config = ExperimentConfig(name="state_test")
        state = {"config": config, "results": [{"a": 1}, {"b": 2}], "graph": None}

        report = Report.from_state(state)

        assert report.config == config
        assert len(report.records) == 2

    def test_to_dataframe(self):
        """Test to_dataframe conversion."""
        pytest.importorskip("pandas")
        config = ExperimentConfig(name="df_test")
        records = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
        report = Report(config=config, records=records)

        df = report.to_dataframe()

        assert len(df) == 2
        assert list(df.columns) == ["x", "y"]
        assert df["x"].tolist() == [1, 3]

    def test_to_dataframe_empty(self):
        """Test to_dataframe with empty records."""
        pytest.importorskip("pandas")
        config = ExperimentConfig(name="empty_df_test")
        report = Report(config=config, records=[])

        df = report.to_dataframe()

        assert len(df) == 0

    def test_to_markdown_creates_file(self):
        """Test to_markdown creates a file."""
        config = ExperimentConfig(name="md_test", seed=42)
        records = [{"metric": "accuracy", "value": 0.95}]
        report = Report(config=config, records=records)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            file_path = f.name

        try:
            report.to_markdown(file_path)
            assert Path(file_path).exists()

            content = Path(file_path).read_text()
            assert "# md_test" in content
            assert "42" in content
            assert "accuracy" in content
            assert "0.95" in content
        finally:
            Path(file_path).unlink(missing_ok=True)

    def test_to_markdown_with_metadata(self):
        """Test to_markdown includes metadata."""
        config = ExperimentConfig(
            name="meta_test", seed=1, metadata={"author": "test", "version": 2}
        )
        report = Report(config=config, records=[])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            file_path = f.name

        try:
            report.to_markdown(file_path)
            content = Path(file_path).read_text()

            assert "# meta_test" in content
            assert "Metadata" in content
        finally:
            Path(file_path).unlink(missing_ok=True)

    def test_to_markdown_empty_records(self):
        """Test to_markdown with no records."""
        config = ExperimentConfig(name="no_records")
        report = Report(config=config, records=[])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            file_path = f.name

        try:
            report.to_markdown(file_path)
            content = Path(file_path).read_text()

            assert "No results recorded" in content
        finally:
            Path(file_path).unlink(missing_ok=True)


class TestPipelineIntegration:
    """Integration tests for complete experiment pipelines."""

    def test_graph_processing_pipeline(self):
        """Test pipeline that processes a graph."""
        config = ExperimentConfig(name="graph_test", seed=42)

        class NodeCountStep(Step):
            def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
                graph = state["graph"]
                state["results"].append(
                    {"metric": "node_count", "value": graph.number_of_nodes()}
                )
                return state

        class EdgeCountStep(Step):
            def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
                graph = state["graph"]
                state["results"].append(
                    {"metric": "edge_count", "value": graph.number_of_edges()}
                )
                return state

        pipeline = Pipeline(
            config=config, steps=[NodeCountStep("nodes"), EdgeCountStep("edges")]
        )

        graph = nx.karate_club_graph()
        report = pipeline.fit_run(graph)

        assert len(report.records) == 2
        assert report.records[0]["metric"] == "node_count"
        assert report.records[0]["value"] == 34
        assert report.records[1]["metric"] == "edge_count"
        assert report.records[1]["value"] == 78

    def test_pipeline_with_graph_modification(self):
        """Test pipeline step that modifies the graph."""
        config = ExperimentConfig(name="modify_graph")

        class AddNodeStep(Step):
            def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
                state["graph"].add_node("new_node")
                state["results"].append({"action": "added_node"})
                return state

        class CountStep(Step):
            def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
                count = state["graph"].number_of_nodes()
                state["results"].append({"node_count": count})
                return state

        pipeline = Pipeline(
            config=config, steps=[AddNodeStep("add"), CountStep("count")]
        )

        graph = nx.Graph()
        graph.add_nodes_from([1, 2, 3])  # Start with 3 nodes

        report = pipeline.fit_run(graph)

        assert report.records[1]["node_count"] == 4  # 3 + 1 added

    def test_full_experiment_workflow(self):
        """Test complete experiment workflow with report export."""
        pytest.importorskip("pandas")
        config = ExperimentConfig(
            name="Full Experiment",
            seed=123,
            metadata={"description": "Integration test"},
        )

        class DensityStep(Step):
            def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
                graph = state["graph"]
                density = nx.density(graph)
                state["results"].append(
                    {"step": self.name, "metric": "density", "value": density}
                )
                return state

        pipeline = Pipeline(config=config, steps=[DensityStep("density")])

        graph = nx.complete_graph(5)
        report = pipeline.fit_run(graph)

        # Verify report contents
        assert report.config.name == "Full Experiment"
        assert report.config.seed == 123
        assert len(report.records) == 1
        assert report.records[0]["value"] == 1.0  # Complete graph has density 1

        # Test DataFrame export
        df = report.to_dataframe()
        assert len(df) == 1
        assert "value" in df.columns

        # Test Markdown export
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            file_path = f.name

        try:
            report.to_markdown(file_path)
            content = Path(file_path).read_text()
            assert "Full Experiment" in content
            assert "density" in content
        finally:
            Path(file_path).unlink(missing_ok=True)
