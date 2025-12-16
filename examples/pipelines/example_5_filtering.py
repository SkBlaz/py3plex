#!/usr/bin/env python3
"""
Example 5: Filtering Pipeline - Load, Filter, and Analyze

Generate two deterministic networks: one unfiltered baseline and one with a
minimum-degree filter applied. Compare how filtering changes node/edge counts.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

# Allow running the example without installing the package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from py3plex.pipeline import ComputeStats, FilterNodes, LoadStep, Pipeline

DEFAULT_SEED = 42


def _run_pipeline(label: str, pipeline: Pipeline) -> dict:
    """Execute a pipeline and print a short summary."""
    print(f"\n### {label} ###")
    result = pipeline.run()
    print(f"  Nodes: {result['nodes']}")
    print(f"  Edges: {result['edges']}")
    return result


def build_pipelines() -> tuple[Pipeline, Pipeline]:
    """Create baseline and filtered pipelines."""
    baseline = Pipeline(
        [
            ("load", LoadStep(generator="random_er", n=50, l=2, p=0.1, directed=False)),
            ("stats", ComputeStats(include_layer_stats=False)),
        ]
    )
    filtered = Pipeline(
        [
            ("load", LoadStep(generator="random_er", n=50, l=2, p=0.1, directed=False)),
            ("filter", FilterNodes(min_degree=3)),
            ("stats", ComputeStats(include_layer_stats=False)),
        ]
    )
    return baseline, filtered


def main() -> int:
    """Run filtering vs. no-filter comparison."""
    np.random.seed(DEFAULT_SEED)

    print("=" * 70)
    print("Example 5: Node Filtering Pipeline")
    print("=" * 70)

    baseline_pipe, filtered_pipe = build_pipelines()
    baseline_result = _run_pipeline("Baseline: Without filtering", baseline_pipe)
    filtered_result = _run_pipeline("With filtering (min_degree=3)", filtered_pipe)

    print(f"\nNodes removed: {baseline_result['nodes'] - filtered_result['nodes']}")
    print(f"Edges removed: {baseline_result['edges'] - filtered_result['edges']}")

    print("\n" + "=" * 70)
    print("Example completed!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
