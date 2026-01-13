#!/usr/bin/env python3
"""
Example 6: Complex Pipeline - Multi-step Analysis

Generate a deterministic multilayer network, filter by degree, aggregate layers,
and run Louvain community detection. Shows how to inspect steps and summarize
community sizes.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

# Allow running the example without installing the package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from py3plex.pipeline import (
    AggregateLayers,
    FilterNodes,
    LoadStep,
    LouvainCommunity,
    Pipeline,
)

DEFAULT_SEED = 42


def _print_distribution(communities: dict) -> None:
    """Print a human-friendly community size distribution and average size."""
    community_sizes = {}
    for _, comm in communities.items():
        community_sizes[comm] = community_sizes.get(comm, 0) + 1

    print("\nCommunity size distribution:")
    for comm in sorted(community_sizes):
        print(f"  Community {comm}: {community_sizes[comm]} nodes")

    avg_size = sum(community_sizes.values()) / len(community_sizes)
    print(f"\nAverage community size: {avg_size:.2f} nodes")


def build_pipeline() -> Pipeline:
    """Create the multi-step pipeline."""
    return Pipeline(
        [
            ("load", LoadStep(generator="random_er", n=60, l=4, p=0.08)),
            ("filter", FilterNodes(min_degree=2)),
            ("aggregate", AggregateLayers(method="sum")),
            ("community", LouvainCommunity(resolution=1.0)),
        ]
    )


def main() -> int:
    """Run the complex pipeline example."""
    np.random.seed(DEFAULT_SEED)

    print("=" * 70)
    print("Example 6: Complex Multi-step Pipeline")
    print("=" * 70)

    pipe = build_pipeline()
    print("\nPipeline structure:")
    print(pipe)

    print("\nPipeline steps:")
    for i, (name, step) in enumerate(pipe.steps, 1):
        print(f"  {i}. {name}: {step.__class__.__name__}")

    print("\nRunning complex pipeline...")
    try:
        result = pipe.run()
    except ImportError as exc:
        missing = getattr(exc, "name", "python-louvain")
        print(f"Optional dependency '{missing}' is missing; install it to run this example.")
        return 0

    print("\n" + "=" * 70)
    print("Final Results:")
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
