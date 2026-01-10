"""
Community Detection Example: Louvain and (optional) Infomap

Teaches:
- Load a network from a sparse `.mat` file (default: `datasets/cora.mat`)
- Detect communities with Louvain (Python-only)
- Optionally compare with Infomap if the binary is available
- Save headless visualizations instead of opening GUI windows

Prerequisites:
- Dataset: `cora.mat` available via `py3plex.utils.get_dataset_path`
- Optional: Infomap binary on PATH for the Infomap section
- Optional: matplotlib for saving plots (Agg backend is used)

SKIP_CI: external_deps - Requires specific dataset files (cora.mat)
"""

from __future__ import annotations

import argparse
import os
import random
from collections import Counter
from typing import Dict, Iterable, Tuple

import numpy as np

try:
    import matplotlib

    matplotlib.use("Agg")
except ImportError:
    matplotlib = None

try:
    from py3plex.algorithms.community_detection import community_wrapper as cw
    from py3plex.core import multinet
    from py3plex.utils import get_dataset_path
    from py3plex.visualization.colors import colors_default
    from py3plex.visualization.multilayer import hairball_plot, plt
except ImportError as exc:  # pragma: no cover - handled with a clear message
    cw = None
    multinet = None
    get_dataset_path = None
    colors_default = []
    hairball_plot = None
    plt = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

DEFAULT_SEED = 42
DEFAULT_LOUVAIN_PLOT = "/tmp/communities_louvain.png"
DEFAULT_INFOMAP_PLOT = "/tmp/communities_infomap.png"


def parse_args() -> argparse.Namespace:
    """Configure and parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Community detection and visualization example (headless-friendly)"
    )
    parser.add_argument(
        "--input_network",
        default=get_dataset_path("cora.mat") if get_dataset_path else "cora.mat",
        help="Path to input network file (default: datasets/cora.mat)",
    )
    parser.add_argument(
        "--input_type",
        default="sparse",
        help="Input format type (default: sparse)",
    )
    parser.add_argument(
        "--iterations",
        default=200,
        type=int,
        help="Layout iterations for visualization (default: 200)",
    )
    parser.add_argument(
        "--seed",
        default=DEFAULT_SEED,
        type=int,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--plot_path",
        default=DEFAULT_LOUVAIN_PLOT,
        help="Path to save the Louvain plot (use 'none' to skip saving)",
    )
    parser.add_argument(
        "--infomap_binary",
        default="./infomap",
        help="Path to Infomap binary (used only if reachable)",
    )
    parser.add_argument(
        "--infomap_plot_path",
        default=DEFAULT_INFOMAP_PLOT,
        help="Where to save the Infomap plot (use 'none' to skip saving)",
    )
    parser.add_argument(
        "--skip_infomap",
        action="store_true",
        help="Skip the optional Infomap comparison step",
    )
    parser.add_argument(
        "--save_edgelist",
        action="store_true",
        help="Serialize the network to edgelist format after detection",
    )
    parser.add_argument(
        "--skip_visualization",
        action="store_true",
        help="Skip visualization (layout computation) to speed up execution",
    )
    return parser.parse_args()


def load_network(path: str, input_type: str) -> multinet.multi_layer_network:
    """Load the input network and ensure sparse matrices are converted."""
    print(f"\nLoading network from {path} (type={input_type})...")
    network = multinet.multi_layer_network().load_network(
        input_file=path,
        directed=False,
        input_type=input_type,
    )

    if input_type == "sparse":
        print("Converting sparse matrix to px format...")
        network.sparse_to_px()

    print("\nNetwork statistics:")
    print("-" * 70)
    network.basic_stats()
    return network


def _select_top_labels(partition: Dict[Tuple[str, str], int], top_n: int) -> Iterable[int]:
    """Return the top N community labels by size."""
    partition_counts = Counter(partition.values())
    return list(partition_counts.keys())[0:top_n]


def visualize_partition(
    network: multinet.multi_layer_network,
    partition: Dict[Tuple[str, str], int],
    iterations: int,
    plot_path: str,
    title: str,
    skip_visualization: bool = False,
) -> None:
    """Render a headless community plot if matplotlib is available."""
    if skip_visualization:
        print("Visualization skipped (--skip_visualization flag set).")
        return
    if plot_path.lower() == "none":
        print("Visualization disabled (plot_path set to 'none').")
        return
    if hairball_plot is None or plt is None or matplotlib is None:
        print("matplotlib not available; skipping visualization.")
        return

    top_n = 10
    top_n_communities = _select_top_labels(partition, top_n)
    color_pool = [x for x in colors_default if x != "black"]
    color_mappings = dict(zip(top_n_communities, color_pool[:top_n]))

    network_colors = [
        color_mappings.get(partition[node], "black") for node in network.get_nodes()
    ]

    print(f"Saving {title} visualization to {plot_path}")
    hairball_plot(
        network.core_network,
        color_list=network_colors,
        layout_parameters={"iterations": iterations},
        scale_by_size=True,
        layout_algorithm="force",
        legend=False,
    )
    plt.title(title)
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()


def run_louvain(network: multinet.multi_layer_network) -> Dict[Tuple[str, str], int]:
    """Run Louvain community detection and report statistics."""
    print("\n" + "=" * 70)
    print("LOUVAIN COMMUNITY DETECTION")
    print("=" * 70)
    print("Running Louvain algorithm (optimizes network modularity)...")

    partition = cw.louvain_communities(network)
    community_sizes = Counter(partition.values())

    print("\nCommunity detection complete!")
    print(f"  Total communities found: {len(community_sizes)}")
    print(f"  Largest community: {max(community_sizes.values())} nodes")
    print(f"  Smallest community: {min(community_sizes.values())} nodes")
    avg_size = sum(community_sizes.values()) / len(community_sizes)
    print(f"  Average community size: {avg_size:.1f} nodes")
    return partition


def try_infomap(
    network: multinet.multi_layer_network,
    binary_path: str,
    iterations: int,
    seed: int,
    plot_path: str,
    skip_visualization: bool = False,
) -> None:
    """Attempt Infomap community detection with graceful fallbacks."""
    print("\n" + "=" * 70)
    print("INFOMAP COMMUNITY DETECTION (OPTIONAL)")
    print("=" * 70)
    print(
        """
Note: Infomap requires an external binary that is not bundled.
Options:
  1. Download from: https://www.mapequation.org/infomap/
  2. Install via: pip install infomap
  3. Use Louvain (above) as a Python-only alternative
"""
    )

    try:
        print("Running Infomap algorithm...")
        partition = cw.infomap_communities(
            network,
            binary=binary_path,
            multiplex=False,
            verbose=True,
            seed=seed,
        )
        community_sizes = Counter(partition.values())
        print("\nInfomap detection complete!")
        print(f"  Total communities found: {len(community_sizes)}")

        visualize_partition(
            network,
            partition,
            iterations=iterations,
            plot_path=plot_path,
            title="Infomap communities",
            skip_visualization=skip_visualization,
        )
    except FileNotFoundError as exc:
        print(f"[X] Infomap binary not found: {exc}")
        print("  Using Louvain results from above instead.")
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[X] Error running Infomap: {exc}")
        print("  Using Louvain results from above instead.")


def maybe_save_edgelist(network: multinet.multi_layer_network) -> None:
    """Persist the network as an edgelist if requested."""
    output_file = "tmp_network.txt"
    print(f"Saving network to: {output_file}")
    network.serialize_to_edgelist(edgelist_file=output_file)
    print("[OK] Network saved successfully!")
    print("  Node mapping saved in: network.node_map")


def main() -> int:
    """Entry point for running the community detection walkthrough."""
    if IMPORT_ERROR:
        print(f"Error importing dependencies: {IMPORT_ERROR}")
        print("Install py3plex (and matplotlib for plots) to run this example.")
        return 1

    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)

    print("=" * 70)
    print("COMMUNITY DETECTION AND VISUALIZATION")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Input file: {args.input_network}")
    print(f"  Input type: {args.input_type}")
    print(f"  Layout iterations: {args.iterations}")
    print(f"  Random seed: {args.seed}")
    print(f"  Louvain plot: {args.plot_path}")

    if not os.path.exists(args.input_network):
        print(f"Error: Input file '{args.input_network}' not found.")
        print("Please specify a valid network file using --input_network")
        return 1

    network = load_network(args.input_network, args.input_type)
    partition = run_louvain(network)
    visualize_partition(
        network,
        partition,
        iterations=args.iterations,
        plot_path=args.plot_path,
        title="Louvain communities",
        skip_visualization=args.skip_visualization,
    )

    if not args.skip_infomap:
        try_infomap(
            network,
            binary_path=args.infomap_binary,
            iterations=args.iterations,
            seed=args.seed,
            plot_path=args.infomap_plot_path,
            skip_visualization=args.skip_visualization,
        )
    else:
        print("Infomap step skipped by user request.")

    if args.save_edgelist:
        maybe_save_edgelist(network)
    else:
        print("Edgelist export disabled (use --save_edgelist to enable)")

    print("\n" + "=" * 70)
    print("COMMUNITY DETECTION COMPLETE")
    print("=" * 70)

    print("\nKey takeaways:")
    print("  [OK] Louvain: Fast, Python-only, optimizes modularity")
    print("  [OK] Infomap: Flow-based, requires binary, very accurate")
    print("  [OK] Both reveal hierarchical community structure")
    print("  [OK] Visualizations help validate detected communities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
