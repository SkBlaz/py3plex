#!/usr/bin/env python3
"""
Example 1: Basic Pipeline - Load and Compute Statistics

Load a small random multilayer network, compute core statistics, and print a
layer-by-layer summary. The random generator is seeded for determinism and the
script is safe to run headlessly.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

# Allow running the example without installing the package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from py3plex.pipeline import ComputeStats, LoadStep, Pipeline

DEFAULT_SEED = 42


def _print_results(result: dict) -> None:
    """Pretty-print pipeline statistics output."""
    print(f"Nodes: {result['nodes']}")
    print(f"Edges: {result['edges']}")
    print(f"Density: {result['density']:.4f}")

    if "layers" in result:
        print(f"Layers: {result['layers']}")
    if "layer_densities" in result:
        print("\nLayer densities:")
        for layer, density in result["layer_densities"].items():
            print(f"  {layer}: {density:.4f}")


def build_pipeline() -> Pipeline:
    """Create the minimal stats pipeline."""
    return Pipeline(
        [
            ("load", LoadStep(generator="random_er", n=50, l=3, p=0.1)),
            ("stats", ComputeStats(include_layer_stats=True)),
        ]
    )


def main() -> int:
    """Run the basic statistics example."""
    np.random.seed(DEFAULT_SEED)

    print("=" * 70)
    print("Example 1: Basic Statistics Pipeline")
    print("=" * 70)

    pipe = build_pipeline()
    print("\nPipeline structure:")
    print(pipe)

    print("\nRunning pipeline...")
    result = pipe.run()

    print("\n" + "=" * 70)
    print("Results:")
    print("=" * 70)
    _print_results(result)

    print("\n" + "=" * 70)
    print("Example completed!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
