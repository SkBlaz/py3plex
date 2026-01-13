"""
Simple visualization of a multiplex Twitter network.

Loads example multiplex edges, maps layer ids to names, and renders a
basic circular layout. Uses network_type="multiplex" so same users are
connected across layers automatically.

SKIP_CI: slow - Takes more than 10 seconds to complete
"""

from __future__ import annotations

import os
from typing import Dict, List

from py3plex.core import multinet
from py3plex.utils import get_dataset_path
from py3plex.visualization.multilayer import draw_multilayer_default, plt


def load_layer_map(path: str) -> Dict[str, str]:
    """Load the mapping between numeric layer ids and readable names."""
    layer_map: Dict[str, str] = {}
    with open(path, encoding="utf-8") as twl:
        for line in twl:
            idx, lname = line.strip().split()
            layer_map[idx] = lname
    return layer_map


def main() -> int:
    layers_file = get_dataset_path("twitterlayers.txt")
    edges_file = get_dataset_path("test13.edges")

    if not (os.path.exists(layers_file) and os.path.exists(edges_file)):
        print("Twitter multiplex datasets not found; skipping example.")
        print(f"Expected: {layers_file}")
        print(f"Expected: {edges_file}")
        return 0

    layer_map = load_layer_map(layers_file)
    network = multinet.multi_layer_network(network_type="multiplex").load_network(
        edges_file,
        directed=False,
        input_type="multiplex_edges",
    )

    labels, graphs, _ = network.get_layers()
    readable_labels: List[str] = [layer_map.get(layer, layer) for layer in labels]

    draw_multilayer_default(
        graphs,
        display=False,
        background_shape="circle",
        labels=readable_labels,
        node_size=1,
    )
    plt.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
