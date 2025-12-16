#!/usr/bin/env python3
"""
Example 7: Save and Load Pipeline - Persisting Results

Generate and aggregate a multilayer network, save it to disk, then load it in a
second pipeline to verify consistency. Uses a temporary directory and seeded
randomness for reproducibility.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

import numpy as np

# Allow running the example without installing the package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from py3plex.pipeline import (
    AggregateLayers,
    ComputeStats,
    LoadStep,
    Pipeline,
    SaveNetwork,
)

DEFAULT_SEED = 42


def _run_and_report(pipe: Pipeline, title: str) -> dict:
    """Execute a pipeline and print its basic stats."""
    print(f"\n### {title} ###")
    result = pipe.run()
    print(f"  Nodes: {result['nodes']}")
    print(f"  Edges: {result['edges']}")
    return result


def build_pipelines(output_path: Path) -> tuple[Pipeline, Pipeline]:
    """Create pipelines for saving then loading a network."""
    pipe_generate = Pipeline(
        [
            ("load", LoadStep(generator="random_er", n=30, l=3, p=0.15)),
            ("aggregate", AggregateLayers(method="sum")),
            ("save", SaveNetwork(path=str(output_path), format="graphml")),
            ("stats", ComputeStats(include_layer_stats=False)),
        ]
    )
    pipe_load = Pipeline(
        [
            ("load", LoadStep(path=str(output_path), input_type="graphml")),
            ("stats", ComputeStats(include_layer_stats=False)),
        ]
    )
    return pipe_generate, pipe_load


def main() -> int:
    """Run the save/load pipeline example."""
    np.random.seed(DEFAULT_SEED)

    print("=" * 70)
    print("Example 7: Save and Load Pipeline")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as temp_dir:
        network_path = Path(temp_dir) / "aggregated_network.graphml"
        print(f"\nTemporary directory: {temp_dir}")

        pipe_generate, pipe_load = build_pipelines(network_path)
        result1 = _run_and_report(pipe_generate, "Pipeline 1: Generate and Save")
        print(f"  Saved network to: {network_path}")

        result2 = _run_and_report(pipe_load, "Pipeline 2: Load and Analyze")
        print(f"  Loaded network from: {network_path}")

        print("\n### Verification ###")
        if result1["nodes"] == result2["nodes"] and result1["edges"] == result2["edges"]:
            print("✓ Network successfully saved and loaded!")
        else:
            print("✗ Mismatch in saved/loaded network")

    print("\n" + "=" * 70)
    print("Example completed!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
