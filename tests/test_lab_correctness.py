"""Additional correctness-focused tests for py3plex.lab."""

from typing import Any, Dict

import pytest

from py3plex.lab import ExperimentConfig, Pipeline, Report, Step


def test_experiment_config_to_dict_isolated_from_mutations():
    """to_dict should return a deep-copied structure safe from external mutation."""
    metadata = {"nested": {"version": 1}}
    config = ExperimentConfig(name="cfg", metadata=metadata)

    as_dict = config.to_dict()
    as_dict["metadata"]["nested"]["version"] = 2

    assert config.metadata["nested"]["version"] == 1
    assert as_dict["metadata"]["nested"]["version"] == 2
    assert as_dict["metadata"] is not metadata


def test_pipeline_uses_state_returned_by_steps():
    """Pipeline must thread the exact state returned by each step."""
    replaced_state: Dict[str, Any] = {}

    class ReplaceStateStep(Step):
        def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal replaced_state
            replaced_state = {
                "graph": "from_replace",
                "config": state["config"],
                "results": [{"step": self.name}],
            }
            return replaced_state

    class AssertStateStep(Step):
        def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
            assert state is replaced_state
            assert state["graph"] == "from_replace"
            assert state["results"][0]["step"] == "replace"
            state["results"].append({"step": self.name})
            return state

    pipeline = Pipeline(
        config=ExperimentConfig(name="pipeline"),
        steps=[ReplaceStateStep("replace"), AssertStateStep("assert")],
    )

    report = pipeline.fit_run(graph=None)

    assert [r["step"] for r in report.records] == ["replace", "assert"]


def test_pipeline_runs_start_from_fresh_state_each_time():
    """fit_run should not leak results between successive invocations."""
    class CountingStep(Step):
        def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
            state["results"].append({"run_index": len(state["results"])})
            return state

    pipeline = Pipeline(config=ExperimentConfig(name="fresh"), steps=[CountingStep("c")])

    first = pipeline.fit_run(graph=None)
    second = pipeline.fit_run(graph=None)

    assert first.records == [{"run_index": 0}]
    assert second.records == [{"run_index": 0}]


def test_report_to_markdown_unions_keys_in_first_seen_order(tmp_path):
    """Markdown export should include union of record keys preserving first-seen order."""
    report = Report(
        config=ExperimentConfig(name="order"),
        records=[{"a": 1, "b": 2}, {"b": 3, "c": 4}],
    )
    out_path = tmp_path / "report.md"

    report.to_markdown(str(out_path))
    content = out_path.read_text().splitlines()

    header = next(line for line in content if line.startswith("| a"))
    row_with_blank = next(line for line in content if line.startswith("|  |"))

    assert header == "| a | b | c |"
    assert row_with_blank.startswith("|  | 3 | 4 |")


def test_report_from_state_requires_config_and_results_keys():
    """Report.from_state should raise if required keys are absent."""
    with pytest.raises(KeyError):
        Report.from_state({"results": []})


def test_pipeline_raises_if_step_returns_state_missing_required_keys():
    """Pipeline assumes steps return a state dict containing 'config' and 'results'."""

    class BreakStateStep(Step):
        def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
            return {}

    pipeline = Pipeline(config=ExperimentConfig(name="broken"), steps=[BreakStateStep("break")])

    with pytest.raises(KeyError):
        pipeline.fit_run(graph=None)


def test_report_to_markdown_omits_metadata_when_empty_dict(tmp_path):
    """Empty metadata should not render a metadata line (consistent with truthy check)."""
    report = Report(config=ExperimentConfig(name="md", seed=0, metadata={}), records=[])
    out_path = tmp_path / "report.md"

    report.to_markdown(str(out_path))
    content = out_path.read_text()

    assert "- **Metadata**:" not in content


def test_report_to_markdown_accepts_pathlib_paths(tmp_path):
    """`to_markdown` should accept Path-like objects supported by `open()`."""
    report = Report(config=ExperimentConfig(name="md"), records=[{"a": 1}])
    out_path = tmp_path / "report.md"

    report.to_markdown(out_path)

    assert out_path.exists()
    assert out_path.read_text().startswith("# md")


def test_property_markdown_table_columns_match_union_first_seen_order(tmp_path):
    """Property: markdown table columns match union of keys in first-seen order."""
    hypothesis = pytest.importorskip("hypothesis")
    st = pytest.importorskip("hypothesis.strategies")

    key_st = st.sampled_from(["a", "b", "c", "d", "e"])
    record_st = st.lists(st.tuples(key_st, st.integers()), min_size=0, max_size=5).map(
        lambda items: dict(items)
    )

    @hypothesis.given(records=st.lists(record_st, min_size=1, max_size=8))
    @hypothesis.settings(max_examples=60)
    def check(records):
        report = Report(config=ExperimentConfig(name="prop"), records=records)
        out_path = tmp_path / "prop.md"
        report.to_markdown(out_path)

        # If there are no keys at all, markdown still emits a table with empty header.
        expected_keys = list(dict.fromkeys(key for r in records for key in r.keys()))

        lines = out_path.read_text().splitlines()
        table_header = next((line for line in lines if line.startswith("| ")), None)
        if expected_keys:
            assert table_header == "| " + " | ".join(expected_keys) + " |"
        else:
            assert table_header == "|  |"

    check()
