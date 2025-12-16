"""
Compute summary statistics and hubs for the IMDB multilayer sample.

Loads the optional `imdb_gml.gml` dataset (downloaded via `get_dataset_path`),
prints a quick summary, computes detailed statistics, and lists hub nodes by
degree. Skips gracefully if the dataset is missing.

SKIP_CI: external_deps - Requires optional dataset files.
"""

from __future__ import annotations

from pathlib import Path

from py3plex.algorithms.statistics.basic_statistics import (
    core_network_statistics,
    identify_n_hubs,
)
from py3plex.core import multinet
from py3plex.utils import get_dataset_path


def _display_statistics(stats_frame) -> None:
    """Pretty-print statistics whether returned as a dict or DataFrame-like."""
    if isinstance(stats_frame, dict):
        for key, value in stats_frame.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
    else:
        print(stats_frame)


def main() -> int:
    """Run the statistics demo."""
    print("=" * 70)
    print("NETWORK STATISTICS AND HUB IDENTIFICATION")
    print("=" * 70)

    dataset_path = Path(get_dataset_path("imdb_gml.gml"))
    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}")
        print("Skipping example. Please download the IMDB dataset first.")
        return 0

    print(f"\nLoading network from: {dataset_path}")
    multilayer_network = multinet.multi_layer_network().load_network(
        str(dataset_path),
        directed=True,
        input_type="gml",
    )
    print("[OK] Network loaded successfully!")

    print("\n" + "=" * 70)
    print("QUICK NETWORK SUMMARY")
    print("=" * 70)
    print(multilayer_network.summary())

    print("\n" + "=" * 70)
    print("DETAILED NETWORK STATISTICS")
    print("=" * 70)
    print("\nComputing core network statistics...")
    stats_frame = core_network_statistics(multilayer_network.core_network)
    print("\nStatistics:")
    print("-" * 70)
    _display_statistics(stats_frame)

    print("\n" + "=" * 70)
    print("HUB IDENTIFICATION")
    print("=" * 70)
    n_hubs = 20
    print(f"\nIdentifying top {n_hubs} hub nodes by degree...")
    top_hubs = identify_n_hubs(multilayer_network.core_network, n_hubs)

    print(f"\nTop {n_hubs} hubs (node, degree):")
    print("-" * 70)
    if isinstance(top_hubs, list):
        for rank, (node, degree) in enumerate(top_hubs, 1):
            print(f"  {rank:2d}. Node {node}: {degree} connections")
    elif isinstance(top_hubs, dict):
        sorted_hubs = sorted(top_hubs.items(), key=lambda x: x[1], reverse=True)
        for rank, (node, degree) in enumerate(sorted_hubs[:n_hubs], 1):
            print(f"  {rank:2d}. Node {node}: {degree} connections")
    else:
        print(top_hubs)

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print("\nKey Insights:")
    print("  - Network statistics reveal overall structure and connectivity patterns")
    print("  - Hub nodes are critical for network function and resilience")
    print("  - High degree nodes often bridge different communities")
    print("  - Statistics enable comparison with random or theoretical models")
    print("\nNext Steps:")
    print("  - Compare with random networks of similar size")
    print("  - Analyze hub node roles in the network context")
    print("  - Investigate communities around hub nodes")
    print("  - Study resilience by simulating hub removal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
