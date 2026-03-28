"""Performance bottleneck diagnostics for optimization targeting.

This module provides structured, programmatic recommendations for likely
performance bottlenecks in key workflows:
- centrality robustness computations
- null model generation
- uncertainty quantification
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from py3plex.profiling import get_monitor


class OptimizationArea(str, Enum):
    """Supported optimization analysis areas."""

    CENTRALITY = "centrality"
    NULL_MODELS = "null_models"
    UNCERTAINTY = "uncertainty"


@dataclass(frozen=True)
class OptimizationTarget:
    """Single bottleneck and optimization recommendation."""

    area: OptimizationArea
    function: str
    file_path: str
    line_range: tuple[int, int]
    bottleneck: str
    complexity: str
    optimization_target: str
    expected_gain: str
    impact: str

    def to_dict(self) -> Dict[str, Any]:
        """Return JSON-serializable representation."""
        data = asdict(self)
        data["area"] = self.area.value
        return data


@dataclass
class OptimizationTargetReport:
    """Collection of optimization targets and optional runtime context."""

    targets: List[OptimizationTarget]
    network_stats: Dict[str, int]
    profiling: Optional[Dict[str, Dict[str, float]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return JSON-serializable representation."""
        return {
            "targets": [target.to_dict() for target in self.targets],
            "network_stats": self.network_stats,
            "profiling": self.profiling,
            "count": len(self.targets),
        }


_TARGETS: List[OptimizationTarget] = [
    # Centrality
    OptimizationTarget(
        area=OptimizationArea.CENTRALITY,
        function="py3plex.centrality.robustness.robustness_centrality",
        file_path="py3plex/centrality/robustness.py",
        line_range=(164, 194),
        bottleneck=(
            "For each candidate node/layer, the workflow builds a fully perturbed "
            "network and recomputes the metric from scratch."
        ),
        complexity="O(targets × metric_cost + targets × graph_copy_cost)",
        optimization_target=(
            "Avoid full network reconstruction per target by using in-place masking "
            "or cached filtered views when evaluating removals."
        ),
        expected_gain="High for large networks (often multi-x).",
        impact="high",
    ),
    OptimizationTarget(
        area=OptimizationArea.CENTRALITY,
        function="py3plex.centrality.robustness._compute_avg_shortest_path",
        file_path="py3plex/centrality/robustness.py",
        line_range=(306, 334),
        bottleneck=(
            "Average shortest path is recomputed component-by-component with "
            "nested all-pairs traversal."
        ),
        complexity="O(sum over components of n_component²)",
        optimization_target=(
            "Use approximation/sampling for path lengths on large components and "
            "cache component decomposition across repeated evaluations."
        ),
        expected_gain="High on large connected components.",
        impact="high",
    ),
    # Null models
    OptimizationTarget(
        area=OptimizationArea.NULL_MODELS,
        function="py3plex.nullmodels.executor.generate_null_model",
        file_path="py3plex/nullmodels/executor.py",
        line_range=(71, 84),
        bottleneck=(
            "Parallel samples pass the full network object to each worker, "
            "creating serialization overhead."
        ),
        complexity="O(samples × network_serialization_cost)",
        optimization_target=(
            "Pass compact immutable graph payloads (e.g., edge arrays/seed only) "
            "to workers and reconstruct minimal state inside worker."
        ),
        expected_gain="Medium to high for multiprocessing and large graphs.",
        impact="high",
    ),
    OptimizationTarget(
        area=OptimizationArea.NULL_MODELS,
        function="py3plex.nullmodels.models.configuration_model",
        file_path="py3plex/nullmodels/models.py",
        line_range=(174, 188),
        bottleneck=(
            "Nodes and edges are added one-by-one in Python loops when rebuilding "
            "randomized networks."
        ),
        complexity="O(nodes + edges) with high Python overhead",
        optimization_target=(
            "Batch edge/node insertion (single add_edges/add_nodes call) and avoid "
            "per-edge dict creation in inner loops."
        ),
        expected_gain="Medium.",
        impact="medium",
    ),
    # Uncertainty
    OptimizationTarget(
        area=OptimizationArea.UNCERTAINTY,
        function="py3plex.uncertainty.partition.CommunityDistribution._compute_coassoc_dense",
        file_path="py3plex/uncertainty/partition.py",
        line_range=(280, 288),
        bottleneck=(
            "Exact co-association matrix uses triple-nested Python loops across "
            "partitions and node pairs."
        ),
        complexity="O(partitions × nodes²)",
        optimization_target=(
            "Vectorize co-association accumulation using numpy/grouped indexing and "
            "prefer sparse incremental construction for top-k workflows."
        ),
        expected_gain="High.",
        impact="high",
    ),
    OptimizationTarget(
        area=OptimizationArea.UNCERTAINTY,
        function="py3plex.uncertainty.partition_metrics.variation_of_information",
        file_path="py3plex/uncertainty/partition_metrics.py",
        line_range=(104, 107),
        bottleneck=(
            "Mutual-information term iterates contingency table with nested Python loops."
        ),
        complexity="O(n_labels_partition1 × n_labels_partition2)",
        optimization_target=(
            "Replace nested loops with masked vectorized numpy operations over "
            "non-zero contingency entries."
        ),
        expected_gain="Medium.",
        impact="medium",
    ),
    OptimizationTarget(
        area=OptimizationArea.UNCERTAINTY,
        function="py3plex.uncertainty.selection_execution.execute_selection_uq",
        file_path="py3plex/uncertainty/selection_execution.py",
        line_range=(150, 204),
        bottleneck=(
            "Sample execution loop is serial despite independent replicate runs."
        ),
        complexity="O(samples × query_runtime)",
        optimization_target=(
            "Parallelize replicate execution with deterministic child seeds and "
            "aggregate reducer state after worker completion."
        ),
        expected_gain="Medium to high depending on sample count.",
        impact="high",
    ),
]


def _collect_network_stats(network: Any) -> Dict[str, int]:
    """Collect lightweight network statistics for report context."""
    stats = {"nodes": 0, "edges": 0, "layers": 0}

    if network is None:
        return stats

    try:
        if hasattr(network, "get_nodes"):
            stats["nodes"] = len(network.get_nodes())
        elif hasattr(network, "nodes"):
            stats["nodes"] = len(network.nodes())
    except Exception:
        pass

    try:
        if hasattr(network, "get_edges"):
            stats["edges"] = len(network.get_edges())
        elif hasattr(network, "edges"):
            stats["edges"] = len(network.edges())
    except Exception:
        pass

    try:
        if hasattr(network, "get_layers"):
            stats["layers"] = len(network.get_layers())
        elif hasattr(network, "layers"):
            stats["layers"] = len(network.layers)
    except Exception:
        pass

    return stats


def _collect_profiled_functions(targets: Sequence[OptimizationTarget]) -> Dict[str, Dict[str, float]]:
    """Pull matching profile records from the global performance monitor."""
    monitor = get_monitor()
    result: Dict[str, Dict[str, float]] = {}
    if not monitor.enabled:
        return result

    target_functions = {t.function for t in targets}
    for func_name, stats in monitor.stats.items():
        if func_name in target_functions:
            call_count = float(stats.get("call_count", 0.0))
            total_time = float(stats.get("total_time", 0.0))
            avg_ms = (total_time / call_count * 1000.0) if call_count > 0 else 0.0
            result[func_name] = {
                "call_count": call_count,
                "total_time_s": total_time,
                "avg_time_ms": avg_ms,
                "max_time_s": float(stats.get("max_time", 0.0)),
            }
    return result


def find_optimization_targets(
    network: Any = None,
    areas: Optional[Sequence[OptimizationArea | str]] = None,
    include_profiling: bool = True,
) -> OptimizationTargetReport:
    """Find likely performance bottlenecks and concrete optimization targets.

    Parameters
    ----------
    network : Any, optional
        Network object used for contextual report statistics.
    areas : Sequence[OptimizationArea | str], optional
        Restrict analysis to a subset of areas. Defaults to all areas.
    include_profiling : bool, default=True
        If True, include matching entries from global PerformanceMonitor.

    Returns
    -------
    OptimizationTargetReport
        Structured bottleneck report suitable for programmatic consumption.
    """
    normalized_areas = None
    if areas is not None:
        normalized_areas = {OptimizationArea(a) for a in areas}

    targets = [
        target for target in _TARGETS
        if normalized_areas is None or target.area in normalized_areas
    ]

    profiling = _collect_profiled_functions(targets) if include_profiling else None
    if profiling == {}:
        profiling = None

    return OptimizationTargetReport(
        targets=targets,
        network_stats=_collect_network_stats(network),
        profiling=profiling,
    )
