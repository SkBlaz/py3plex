#!/usr/bin/env python3
"""
Example 2: Aggregation Pipeline - Load, Aggregate, and Analyze

Generate a deterministic multilayer network, collapse layers with the `sum`
method, and compute basic statistics on the aggregated view. Safe for
headless environments.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

# Allow running the example without installing the package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from py3plex.pipeline import AggregateLayers, ComputeStats, LoadStep, Pipeline

DEFAULT_SEED = 42


def build_pipeline() -> Pipeline:
    """Create pipeline that aggregates layers before computing stats."""
    return Pipeline(
        [
            ("load", LoadStep(generator="random_er", n=40, l=4, p=0.12)),
            ("aggregate", AggregateLayers(method="sum")),
            ("stats", ComputeStats(include_layer_stats=False)),
        ]
    )


def main() -> int:
    """Run the aggregation example."""
    np.random.seed(DEFAULT_SEED)

    print("=" * 70)
    print("Example 2: Layer Aggregation Pipeline")
    print("=" * 70)

    pipe = build_pipeline()
    print("\nPipeline structure:")
    print(pipe)

    print("\nRunning pipeline...")
    result = pipe.run()

    print("\n" + "=" * 70)
    print("Aggregated Network Statistics:")
    print("=" * 70)
    print(f"Nodes: {result['nodes']}")
    print(f"Edges: {result['edges']}")
    print(f"Density: {result['density']:.4f}")

    print("\n" + "=" * 70)
    print("Example completed!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
