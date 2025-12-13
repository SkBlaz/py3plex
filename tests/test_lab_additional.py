"""Additional tests for py3plex.lab module."""

import networkx as nx
import pytest

from py3plex.lab import ExperimentConfig, Pipeline, Report, Step


def test_pipeline_propagates_step_error():
    """Errors raised inside a step should propagate and halt execution."""
    config = ExperimentConfig(name="failing_pipeline")
    graph = nx.Graph()

    class FailingStep(Step):
        def run(self, state):
            raise ValueError("intentional failure")

    class SpyStep(Step):
        def __init__(self, name):
            super().__init__(name)
            self.called = False

        def run(self, state):
            self.called = True
            return state

    spy = SpyStep("spy")
    pipeline = Pipeline(config=config, steps=[FailingStep("fail"), spy])

    with pytest.raises(ValueError, match="intentional failure"):
        pipeline.fit_run(graph)

    assert spy.called is False


def test_pipeline_passes_mutated_state_between_steps():
    """State mutations in one step must be visible to subsequent steps."""
    config = ExperimentConfig(name="state_pipeline")
    graph = nx.Graph()

    class FirstStep(Step):
        def run(self, state):
            state["extra"] = "present"
            state["results"].append({"step": self.name, "value": 1})
            return state

    class SecondStep(Step):
        def run(self, state):
            assert state["extra"] == "present"
            state["results"].append(
                {"step": self.name, "count": len(state["results"])}
            )
            return state

    pipeline = Pipeline(config=config, steps=[FirstStep("first"), SecondStep("second")])
    report = pipeline.fit_run(graph)

    assert report.records[0]["value"] == 1
    assert report.records[1]["count"] == 1  # sees prior record


def test_report_to_markdown_merges_keys_preserving_order(tmp_path):
    """Markdown export should include union of record keys in first-seen order."""
    config = ExperimentConfig(name="markdown_keys")
    records = [{"alpha": 1, "gamma": 3}, {"beta": 2}]
    report = Report(config=config, records=records)

    output = tmp_path / "report.md"
    report.to_markdown(str(output))

    content = output.read_text()
    assert "| alpha | gamma | beta |" in content
    assert "| 1 | 3 |  |" in content  # missing beta leaves blank
    assert "|  |  | 2 |" in content  # missing alpha/gamma leave blanks
