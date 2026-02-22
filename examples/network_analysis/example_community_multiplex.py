"""
Multiplex community detection walkthrough.

Teaches:
- Load a multiplex edgelist, run Infomap (if available), and multiplex Louvain.

Prerequisites:
- python-louvain and python-igraph
- Dataset: `multiplex_example.edgelist` and accompanying layer mapping file

SKIP_CI: external_deps - Requires specific dataset files (multiplex_example.edgelist)
"""

from __future__ import annotations

import os
from typing import List

import numpy as np

try:
    import igraph as ig
    import louvain
except ImportError as exc:  # pragma: no cover - surfaced to user
    ig = None
    louvain = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

try:
    from py3plex.algorithms.community_detection import community_wrapper as cw
    from py3plex.core import multinet
    from py3plex.utils import get_dataset_path
except ImportError as exc:  # pragma: no cover - surfaced to user
    cw = None
    multinet = None
    get_dataset_path = None
    IMPORT_ERROR = exc if IMPORT_ERROR is None else IMPORT_ERROR

DEFAULT_SEED = 42


def _print_header(title: str) -> None:
    """Pretty-print a section header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def load_multiplex_network():
    """Load the multiplex example network with layer names."""
    edge_path = get_dataset_path("multiplex_example.edgelist")

    if not os.path.exists(edge_path):
        print("Required multiplex dataset file is missing; skipping run.")
        return None

    network = multinet.multi_layer_network(network_type="multiplex").load_network(
        input_file=edge_path, directed=True, input_type="multiplex_edges"
    )
    return network


def try_infomap(network) -> None:
    """Run Infomap on the multiplex network if the binary is available."""
    _print_header("Infomap (optional)")
    try:
        partition = cw.infomap_communities(
            network,
            binary="./infomap",
            multiplex=True,
            verbose=True,
        )
        print(partition)
    except FileNotFoundError as exc:
        print(f"Skipping Infomap: {exc}")
        print("Continuing with multiplex Louvain instead...")
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Infomap error: {exc}")
        print("Continuing with multiplex Louvain instead...")


def run_multiplex_louvain(network) -> None:
    """Compute multiplex Louvain communities via python-louvain + igraph."""
    _print_header("Multiplex Louvain")
    network.split_to_layers(style="none")
    network_list: List[ig.Graph] = []

    for layer in network.separate_layers:
        g = ig.Graph()
        edges_all = []
        for edge in layer.edges():
            first_node = int(edge[0][0])
            second_node = int(edge[1][0])
            g.add_vertex(first_node)
            g.add_vertex(second_node)
            edges_all.append((first_node, second_node))
        g.add_edges(edges_all)
        network_list.append(g)

    membership, improv = louvain.find_partition_multiplex(
        network_list, louvain.ModularityVertexPartition
    )
    network.monitor(membership)
    network.monitor(improv)
    print("Louvain membership per layer computed.")


def main() -> int:
    """Drive multiplex community detection example."""
    if IMPORT_ERROR:
        print(f"Missing dependency: {IMPORT_ERROR}")
        print("Install python-louvain, python-igraph, and py3plex to run this example.")
        return 1

    np.random.seed(DEFAULT_SEED)
    _print_header("Multiplex community detection")
    network = load_multiplex_network()
    if network is None:
        return 1

    try_infomap(network)
    run_multiplex_louvain(network)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
