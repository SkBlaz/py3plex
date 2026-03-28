"""Tests for optimization target diagnostics."""

from py3plex.diagnostics import (
    OptimizationArea,
    find_optimization_targets,
)
from py3plex.profiling import get_monitor


class _TinyNetwork:
    """Minimal network stub for diagnostics context."""

    def get_nodes(self):
        return [("a", "L0"), ("b", "L0"), ("a", "L1")]

    def get_edges(self):
        return [
            ("a", "b", "L0", "L0"),
            ("a", "a", "L0", "L1"),
        ]

    def get_layers(self):
        return ["L0", "L1"]


def test_find_optimization_targets_returns_expected_areas():
    report = find_optimization_targets()
    assert report.targets
    areas = {target.area for target in report.targets}
    assert OptimizationArea.CENTRALITY in areas
    assert OptimizationArea.NULL_MODELS in areas
    assert OptimizationArea.UNCERTAINTY in areas


def test_find_optimization_targets_area_filter():
    report = find_optimization_targets(areas=[OptimizationArea.CENTRALITY])
    assert report.targets
    assert all(target.area == OptimizationArea.CENTRALITY for target in report.targets)


def test_find_optimization_targets_collects_network_stats():
    report = find_optimization_targets(network=_TinyNetwork())
    assert report.network_stats["nodes"] == 3
    assert report.network_stats["edges"] == 2
    assert report.network_stats["layers"] == 2


def test_find_optimization_targets_includes_profile_data_for_tracked_function():
    monitor = get_monitor()
    monitor.clear()
    monitor.record(
        "py3plex.nullmodels.executor.generate_null_model",
        elapsed=0.5,
        memory_delta=0.0,
    )

    report = find_optimization_targets(include_profiling=True)
    assert report.profiling is not None
    assert "py3plex.nullmodels.executor.generate_null_model" in report.profiling
    row = report.profiling["py3plex.nullmodels.executor.generate_null_model"]
    assert row["call_count"] == 1.0
    assert row["total_time_s"] == 0.5
    assert row["avg_time_ms"] == 500.0


def test_optimization_report_to_dict_is_serializable_shape():
    report = find_optimization_targets(areas=["null_models"])
    payload = report.to_dict()
    assert payload["count"] == len(payload["targets"])
    assert payload["targets"]
    assert payload["targets"][0]["area"] == "null_models"
