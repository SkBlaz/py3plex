#!/usr/bin/env python3
"""
Example 4: Leiden Multilayer Pipeline - Advanced Community Detection

Generate a deterministic multilayer network and run the Leiden algorithm for
community detection. Requires the optional `leidenalg` package.

Runtime: FAST (< 5 seconds)
SKIP_CI: external_deps - Requires leidenalg package
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

# Allow running the example without installing the package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from py3plex.pipeline import LeidenMultilayer, LoadStep, Pipeline

DEFAULT_SEED = 42


def _print_sample_assignments(communities: dict, limit: int = 10) -> None:
    """Print a small sample of community assignments."""
    print("\nSample community assignments:")
    for i, ((node, layer), community) in enumerate(sorted(communities.items())[:limit]):
        print(f"  Node {node} in layer {layer}: Community {community}")

    remaining = len(communities) - limit
    if remaining > 0:
        print(f"  ... and {remaining} more node-layer pairs")


def build_pipeline() -> Pipeline:
    """Create the Leiden multilayer community detection pipeline."""
    return Pipeline(
        [
            ("load", LoadStep(generator="random_er", n=25, l=3, p=0.2)),
            (
                "community",
                LeidenMultilayer(
                    interlayer_coupling=1.0,
                    resolution=1.0,
                    seed=DEFAULT_SEED,
                    max_iter=100,
                ),
            ),
        ]
    )


def main() -> int:
    """Run the Leiden community detection example."""
    np.random.seed(DEFAULT_SEED)

    print("=" * 70)
    print("Example 4: Leiden Multilayer Community Detection Pipeline")
    print("=" * 70)

    pipe = build_pipeline()
    print("\nPipeline structure:")
    print(pipe)

    print("\nRunning pipeline...")
    try:
        result = pipe.run()
    except ImportError:
        print("\n" + "=" * 70)
        print("ERROR: Optional dependency 'leidenalg' is not installed.")
        print("=" * 70)
        print("\nTo run this example, install leidenalg:")
        print("  pip install leidenalg")
        print("\nSkipping example.")
        print("=" * 70)
        return 0

    print("\n" + "=" * 70)
    print("Leiden Multilayer Results:")
    print("=" * 70)
    print(result.summary())
    _print_sample_assignments(result.communities, limit=10)

    print("\n" + "=" * 70)
    print("Example completed!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
