#!/usr/bin/env python3
"""
Example 3: Community Detection Pipeline - Load and Detect Communities

Generate a small multilayer network, run Louvain community detection, and
print the community size distribution. Randomness is seeded to make results
repeatable. Optional dependency: `python-louvain` (installed with py3plex by
default).
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

# Allow running the example without installing the package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from py3plex.pipeline import LoadStep, LouvainCommunity, Pipeline

DEFAULT_SEED = 42


def _print_distribution(communities: dict) -> None:
    """Print a human-friendly community size distribution."""
    size_by_comm = {}
    for _, comm in communities.items():
        size_by_comm[comm] = size_by_comm.get(comm, 0) + 1

    print("\nCommunity size distribution:")
    for comm in sorted(size_by_comm):
        print(f"  Community {comm}: {size_by_comm[comm]} nodes")


def build_pipeline() -> Pipeline:
    """Create the Louvain community detection pipeline."""
    return Pipeline(
        [
            ("load", LoadStep(generator="random_er", n=30, l=2, p=0.15)),
            ("community", LouvainCommunity(resolution=1.0)),
        ]
    )


def main() -> int:
    """Run the community detection example."""
    np.random.seed(DEFAULT_SEED)

    print("=" * 70)
    print("Example 3: Community Detection Pipeline")
    print("=" * 70)

    pipe = build_pipeline()
    print("\nPipeline structure:")
    print(pipe)

    print("\nRunning pipeline...")
    try:
        result = pipe.run()
    except ImportError as exc:
        missing = getattr(exc, "name", "python-louvain")
        print(f"Optional dependency '{missing}' is missing; install it to run this example.")
        return 0

    print("\n" + "=" * 70)
    print("Community Detection Results:")
    print("=" * 70)
    print(f"Algorithm: {result['algorithm']}")
    print(f"Number of communities: {result['num_communities']}")

    _print_distribution(result["communities"])

    print("\n" + "=" * 70)
    print("Example completed!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
