"""
Parse the MLKing multiplex dataset with the generic parser.

Demonstrates two loading approaches for a multiplex folder: explicit file
loading (edges + layer mapping + temporal activity) and the folder-aware parser
that discovers everything automatically. Prerequisite: MLKing dataset available
via `py3plex.utils.get_multilayer_dataset_path`.

SKIP_CI: slow - Takes more than 5 seconds to complete
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Tuple

from py3plex.core import multinet
from py3plex.utils import get_multilayer_dataset_path

DATASET_ROOT = Path(get_multilayer_dataset_path("MLKing"))


def load_with_explicit_files(root: Path) -> Optional[multinet.multi_layer_network]:
    """Load edges, layers, and temporal activity when files are present."""
    edge_path = root / "MLKing2013_multiplex.edges"
    layer_map_path = root / "MLKing2013_layers.txt"
    activity_path = root / "MLKing2013_activity.txt"

    if not edge_path.exists():
        print(f"Edges file missing: {edge_path}")
        return None

    network = multinet.multi_layer_network().load_network(
        str(edge_path),
        directed=True,
        input_type="multiplex_edges",
    )

    if layer_map_path.exists():
        network.load_layer_name_mapping(str(layer_map_path))
    else:
        print(f"Layer mapping not found at {layer_map_path}")

    if activity_path.exists():
        network.load_network_activity(str(activity_path))
    else:
        print(f"Activity file not found at {activity_path}")

    return network


def load_via_folder_parser(root: Path) -> Optional[multinet.multi_layer_network]:
    """Load the multiplex folder directly if it exists."""
    if not root.exists():
        print(f"Dataset folder missing: {root}")
        return None

    return multinet.multi_layer_network().load_network(
        str(root),
        directed=True,
        input_type="multiplex_folder",
    )


def show_activity_samples(network: multinet.multi_layer_network, limit: int = 5) -> None:
    """Print a handful of activity entries to illustrate temporal structure."""
    print("\nSample temporal activity entries:")
    for idx, (timestamp, activated_edges) in enumerate(network.activity.items()):
        print(f"  {timestamp}: {activated_edges[0:3]}")
        if idx + 1 >= limit:
            break


def show_neighbors(network: multinet.multi_layer_network, node_id: str) -> None:
    """Display neighbors across layers for a given node."""
    print(f"\nNeighbors of node {node_id!r} on layer '1':")
    neighbors: Iterable[Tuple[str, str]] = network.get_neighbors(node_id, layer_id="1")
    print(list(neighbors))


def main() -> int:
    """Run both parsing approaches if the dataset is available."""
    print("=== Generic Multiplex Parser Demo ===\n")
    print(f"Dataset root: {DATASET_ROOT}")

    network = load_with_explicit_files(DATASET_ROOT)
    folder_network = load_via_folder_parser(DATASET_ROOT)

    chosen = folder_network or network
    if not chosen:
        print("Dataset not available; skipping example.")
        return 0

    chosen.basic_stats()
    activity = getattr(chosen, "activity", None)
    if activity is not None:
        show_activity_samples(chosen)
    show_neighbors(chosen, node_id="68")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
