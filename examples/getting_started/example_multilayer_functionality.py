"""
Core multilayer network functionality.

Demonstrates how to load a multilayer network, explore nodes/edges, extract
subnetworks, and compute centrality on a layer. Prerequisites: bundled
`multiedgelist.txt` dataset (included in the repo) and py3plex installed.

SKIP_CI: external_deps - Requires specific dataset files
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from py3plex.core import multinet
from py3plex.utils import get_dataset_path

DATASET_PATH = Path(get_dataset_path("multiedgelist.txt"))


def load_multilayer_network() -> Optional[multinet.multi_layer_network]:
    """Load the example multiedgelist network."""
    if not DATASET_PATH.exists():
        print(f"Error: Dataset file '{DATASET_PATH}' not found.")
        print("This example requires a multiedgelist dataset.")
        return None

    print(f"\nLoading multilayer network from: {DATASET_PATH}")
    network = multinet.multi_layer_network().load_network(
        str(DATASET_PATH),
        input_type="multiedgelist",
        directed=False,
    )
    print("Network loaded successfully!\n")
    return network


def preview_edges(network: multinet.multi_layer_network, limit: int = 5) -> None:
    """Print a few edges with attributes."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: ITERATING THROUGH EDGES")
    print("=" * 70)
    network.monitor("Edge iteration:")
    print("Format: ((node1, layer1), (node2, layer2), {'weight': w})\n")

    for idx, edge in enumerate(network.get_edges(data=True)):
        if idx >= limit:
            break
        print(f"  {edge}")

    total_edges = len(list(network.get_edges()))
    print(f"\n  ... (showing {min(limit, total_edges)} of {total_edges} total edges)")


def preview_nodes(network: multinet.multi_layer_network, limit: int = 5) -> None:
    """Print a few nodes with attributes."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: ITERATING THROUGH NODES")
    print("=" * 70)
    network.monitor("Node iteration:")
    print("Format: (node_id, layer_id, {attributes})\n")

    for idx, node in enumerate(network.get_nodes(data=True)):
        if idx >= limit:
            break
        print(f"  {node}")

    total_nodes = len(list(network.get_nodes()))
    print(f"\n  ... (showing {min(limit, total_nodes)} of {total_nodes} total node-layer pairs)")


def extract_layer_subnetwork(
    network: multinet.multi_layer_network, layer_id: str
) -> multinet.multi_layer_network:
    """Return a subnetwork for a specific layer."""
    sub = network.subnetwork([layer_id], subset_by="layers")
    layer_nodes = list(sub.get_nodes())
    print(f"Nodes in layer '{layer_id}': {len(layer_nodes)}")
    network.monitor(f"Sample nodes: {layer_nodes[:5]}")
    return sub


def extract_node_subnetwork(
    network: multinet.multi_layer_network, node_name: str
) -> Iterable:
    """Return instances of a node across layers."""
    sub = network.subnetwork([node_name], subset_by="node_names")
    node_instances = list(sub.get_nodes())
    print(f"Instances of node '{node_name}': {len(node_instances)}")
    network.monitor(f"Node instances: {node_instances}")
    return node_instances


def extract_node_layer_pairs(network: multinet.multi_layer_network) -> Iterable:
    """Return a subnetwork for specific node-layer pairs."""
    sub = network.subnetwork(
        [('1', '1'), ('2', '1')],
        subset_by="node_layer_names",
    )
    selected = list(sub.get_nodes())
    print(f"Selected node-layer pairs: {len(selected)}")
    network.monitor(f"Selected pairs: {selected}")
    return selected


def compute_layer_centrality(
    subnetwork: multinet.multi_layer_network,
) -> None:
    """Compute degree centrality on a single-layer subnetwork."""
    centralities = subnetwork.monoplex_nx_wrapper("degree_centrality")
    print(f"Computed centrality for {len(centralities)} nodes")
    print("\nTop 5 nodes by degree centrality in layer '1':")
    print("-" * 70)

    sorted_centralities = sorted(
        centralities.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    for rank, (node, cent) in enumerate(sorted_centralities, 1):
        print(f"  {rank}. Node {node}: {cent:.4f}")


def main() -> int:
    """Run multilayer functionality demonstration."""
    print("=" * 70)
    print("MULTILAYER NETWORK FUNCTIONALITY DEMONSTRATION")
    print("=" * 70)

    network = load_multilayer_network()
    if network is None:
        return 1

    print("=" * 70)
    print("BASIC NETWORK STATISTICS")
    print("=" * 70)
    network.basic_stats()

    preview_edges(network)
    preview_nodes(network)

    print("\n" + "=" * 70)
    print("EXAMPLE 3: EXTRACTING SUBNETWORK BY LAYER")
    print("=" * 70)
    print("Extracting all nodes in layer '1'...\n")
    layer_subnetwork = extract_layer_subnetwork(network, "1")

    print("\n" + "=" * 70)
    print("EXAMPLE 4: EXTRACTING SUBNETWORK BY NODE NAME")
    print("=" * 70)
    extract_node_subnetwork(network, "1")

    print("\n" + "=" * 70)
    print("EXAMPLE 5: EXTRACTING SPECIFIC NODE-LAYER PAIRS")
    print("=" * 70)
    extract_node_layer_pairs(network)

    print("\n" + "=" * 70)
    print("EXAMPLE 6: COMPUTING CENTRALITY ON SUBNETWORK")
    print("=" * 70)
    print("Computing degree centrality for layer '1'...\n")
    compute_layer_centrality(layer_subnetwork)

    print("\n" + "=" * 70)
    print("MULTILAYER FUNCTIONALITY DEMONSTRATION COMPLETE")
    print("=" * 70)

    print("\nKey operations demonstrated:")
    print("  [OK] Loading multilayer networks")
    print("  [OK] Accessing network statistics")
    print("  [OK] Iterating through edges and nodes")
    print("  [OK] Creating subnetworks by layers")
    print("  [OK] Creating subnetworks by node names")
    print("  [OK] Creating subnetworks by node-layer pairs")
    print("  [OK] Computing centrality measures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
