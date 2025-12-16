"""
Interactive diagonal multilayer visualization with Plotly.

Builds a toy social/professional/hobby multiplex, renders it with the
interactive diagonal layout, and saves an HTML file for local viewing.

Requirements: pip install plotly
Runtime: FAST (<10s)
"""

from __future__ import annotations

import os
import random
from typing import Dict, List, Sequence, Tuple

import numpy as np
from py3plex.core import multinet
from py3plex.visualization.multilayer import interactive_diagonal_plot

OUTPUT_DIR = "output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "interactive_diagonal_multilayer.html")


def ensure_plotly_available() -> bool:
    """Return True if plotly is installed, otherwise print a hint and return False."""
    try:
        import plotly.graph_objects as go  # noqa: F401
    except ImportError:
        print("✗ Plotly not found. Install with: pip install plotly")
        return False
    else:
        return True


def create_nodes_per_layer() -> Dict[str, Sequence[str]]:
    """Return synthetic membership lists per layer."""
    return {
        "social": [
            "Alice",
            "Bob",
            "Charlie",
            "David",
            "Eve",
            "Frank",
            "George",
            "Hannah",
            "Ian",
            "Julia",
            "Kevin",
            "Laura",
            "Mike",
            "Nancy",
            "Oscar",
            "Paula",
        ],
        "professional": [
            "Alice",
            "Bob",
            "Frank",
            "Grace",
            "Henry",
            "Ivan",
            "Julia",
            "Kevin",
            "Mike",
            "Nancy",
            "Quinn",
            "Rachel",
            "Steve",
            "Tina",
            "Uma",
            "Victor",
        ],
        "hobby": [
            "Bob",
            "Charlie",
            "David",
            "Eve",
            "Grace",
            "Hannah",
            "Ian",
            "Jane",
            "Laura",
            "Oscar",
            "Paula",
            "Quinn",
            "Rachel",
            "Sam",
            "Tina",
            "Wendy",
        ],
    }


def create_edges_per_layer() -> Dict[str, List[Tuple[str, str]]]:
    """Return intra-layer edges for each synthetic layer."""
    return {
        "social": [
            ("Alice", "Bob"),
            ("Bob", "Charlie"),
            ("Charlie", "David"),
            ("David", "Eve"),
            ("Eve", "Frank"),
            ("Frank", "Alice"),
            ("Alice", "Charlie"),
            ("Bob", "David"),
            ("Charlie", "Eve"),
            ("David", "Frank"),
            ("Eve", "Alice"),
            ("Frank", "Bob"),
            ("George", "Hannah"),
            ("Hannah", "Ian"),
            ("Ian", "Julia"),
            ("Julia", "Kevin"),
            ("Kevin", "Laura"),
            ("Laura", "George"),
            ("Mike", "Nancy"),
            ("Nancy", "Oscar"),
            ("Oscar", "Paula"),
            ("Paula", "Mike"),
            ("Alice", "George"),
            ("Bob", "Hannah"),
            ("Charlie", "Ian"),
            ("David", "Julia"),
            ("Eve", "Kevin"),
            ("Frank", "Laura"),
            ("George", "Mike"),
            ("Hannah", "Nancy"),
            ("Ian", "Oscar"),
            ("Julia", "Paula"),
            ("Kevin", "Mike"),
            ("Laura", "Nancy"),
        ],
        "professional": [
            ("Alice", "Bob"),
            ("Bob", "Frank"),
            ("Frank", "Grace"),
            ("Grace", "Henry"),
            ("Henry", "Ivan"),
            ("Ivan", "Alice"),
            ("Alice", "Grace"),
            ("Bob", "Henry"),
            ("Frank", "Ivan"),
            ("Julia", "Kevin"),
            ("Kevin", "Mike"),
            ("Mike", "Nancy"),
            ("Nancy", "Quinn"),
            ("Quinn", "Rachel"),
            ("Rachel", "Julia"),
            ("Julia", "Mike"),
            ("Kevin", "Nancy"),
            ("Mike", "Quinn"),
            ("Steve", "Tina"),
            ("Tina", "Uma"),
            ("Uma", "Victor"),
            ("Victor", "Steve"),
            ("Alice", "Julia"),
            ("Bob", "Kevin"),
            ("Frank", "Mike"),
            ("Grace", "Nancy"),
            ("Henry", "Quinn"),
            ("Ivan", "Rachel"),
            ("Julia", "Steve"),
            ("Kevin", "Tina"),
            ("Mike", "Uma"),
            ("Nancy", "Victor"),
        ],
        "hobby": [
            ("Bob", "Charlie"),
            ("Charlie", "David"),
            ("David", "Eve"),
            ("Eve", "Grace"),
            ("Grace", "Hannah"),
            ("Hannah", "Bob"),
            ("Bob", "David"),
            ("Charlie", "Eve"),
            ("David", "Grace"),
            ("Ian", "Jane"),
            ("Jane", "Laura"),
            ("Laura", "Oscar"),
            ("Oscar", "Paula"),
            ("Paula", "Quinn"),
            ("Quinn", "Ian"),
            ("Ian", "Laura"),
            ("Jane", "Oscar"),
            ("Laura", "Paula"),
            ("Rachel", "Sam"),
            ("Sam", "Tina"),
            ("Tina", "Wendy"),
            ("Wendy", "Rachel"),
            ("Bob", "Ian"),
            ("Charlie", "Jane"),
            ("David", "Laura"),
            ("Eve", "Oscar"),
            ("Grace", "Paula"),
            ("Hannah", "Quinn"),
            ("Ian", "Rachel"),
            ("Jane", "Sam"),
            ("Oscar", "Tina"),
            ("Paula", "Wendy"),
        ],
    }


def create_interlayer_edges() -> List[Tuple[str, str, str, str]]:
    """Return edges linking the same person across layers."""
    return [
        ("Alice", "Alice", "social", "professional"),
        ("Bob", "Bob", "social", "professional"),
        ("Frank", "Frank", "social", "professional"),
        ("Julia", "Julia", "social", "professional"),
        ("Kevin", "Kevin", "social", "professional"),
        ("Mike", "Mike", "social", "professional"),
        ("Nancy", "Nancy", "social", "professional"),
        ("Bob", "Bob", "social", "hobby"),
        ("Charlie", "Charlie", "social", "hobby"),
        ("David", "David", "social", "hobby"),
        ("Eve", "Eve", "social", "hobby"),
        ("Hannah", "Hannah", "social", "hobby"),
        ("Ian", "Ian", "social", "hobby"),
        ("Laura", "Laura", "social", "hobby"),
        ("Oscar", "Oscar", "social", "hobby"),
        ("Paula", "Paula", "social", "hobby"),
        ("Bob", "Bob", "professional", "hobby"),
        ("Grace", "Grace", "professional", "hobby"),
        ("Julia", "Julia", "professional", "hobby"),
        ("Kevin", "Kevin", "professional", "hobby"),
        ("Mike", "Mike", "professional", "hobby"),
        ("Nancy", "Nancy", "professional", "hobby"),
        ("Quinn", "Quinn", "professional", "hobby"),
        ("Rachel", "Rachel", "professional", "hobby"),
        ("Tina", "Tina", "professional", "hobby"),
    ]


def build_multilayer_network() -> Tuple[multinet.multi_layer_network, Dict[str, Sequence[str]], Dict[str, List[Tuple[str, str]]], List[Tuple[str, str, str, str]], List[Tuple[str, str]]]:
    """Create the synthetic network and return construction artifacts."""
    network = multinet.multi_layer_network()
    nodes_per_layer = create_nodes_per_layer()
    edges_by_layer = create_edges_per_layer()
    inter_layer_connections = create_interlayer_edges()

    for layer_name, nodes in nodes_per_layer.items():
        for node in nodes:
            network.add_nodes([{"source": node, "type": layer_name}])

    intra_edges_added = 0
    for layer_name, edges in edges_by_layer.items():
        for src, tgt in edges:
            network.add_edges(
                [
                    {
                        "source": src,
                        "target": tgt,
                        "source_type": layer_name,
                        "target_type": layer_name,
                    }
                ]
            )
            intra_edges_added += 1

    interlayer_edges_for_plot: List[Tuple[str, str]] = []
    for src, tgt, layer1, layer2 in inter_layer_connections:
        network.add_edges(
            [
                {
                    "source": src,
                    "target": tgt,
                    "source_type": layer1,
                    "target_type": layer2,
                }
            ]
        )
        interlayer_edges_for_plot.append((src, tgt))

    print(f"  Added {intra_edges_added} intra-layer edges")
    print(f"  Added {len(inter_layer_connections)} inter-layer edges")
    return network, nodes_per_layer, edges_by_layer, inter_layer_connections, interlayer_edges_for_plot


def describe_cross_layer_participation(nodes_per_layer: Dict[str, Sequence[str]]) -> None:
    """Print a short summary of which people appear in multiple layers."""
    cross_layer_nodes: Dict[str, List[str]] = {}
    all_nodes = {n for layer_nodes in nodes_per_layer.values() for n in layer_nodes}
    for node in sorted(all_nodes):
        appearances = [layer for layer, nodes in nodes_per_layer.items() if node in nodes]
        if len(appearances) > 1:
            cross_layer_nodes[node] = appearances

    sample_size = min(10, len(cross_layer_nodes))
    for node, node_layers in list(sorted(cross_layer_nodes.items()))[:sample_size]:
        print(f"  • {node}: {', '.join(node_layers)}")
    remaining = len(cross_layer_nodes) - sample_size
    if remaining > 0:
        print(f"  ... and {remaining} more individuals active across layers")


def main() -> int:
    random.seed(42)
    np.random.seed(42)

    print("=" * 70)
    print("Interactive Diagonal Multilayer Network Visualization")
    print("=" * 70)

    if not ensure_plotly_available():
        return 0

    print("\nStep 1: Creating multilayer network...")
    network, nodes_per_layer, edges_by_layer, inter_layer_connections, interlayer_edges_for_plot = build_multilayer_network()
    network.basic_stats()

    print("\nStep 2: Preparing layers for visualization...")
    labels_list, graphs, _ = network.get_layers("diagonal")
    for label, graph in zip(labels_list, graphs):
        print(f"  - {label}: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    print("\nStep 3: Creating interactive 3D diagonal visualization...")
    fig = interactive_diagonal_plot(
        graphs,
        layer_labels=labels_list,
        layout_algorithm="force",
        layer_gap=4.0,
        node_size_base=10,
        show_interlayer_edges=True,
        interlayer_edges=interlayer_edges_for_plot,
    )

    if fig is None:
        print("\n✗ Failed to create visualization (unexpected None figure)")
        return 1

    fig.update_layout(
        title={
            "text": "Interactive Multilayer Network<br><sub>Hover over nodes for details, drag to rotate</sub>",
            "x": 0.5,
            "xanchor": "center",
        },
        showlegend=True,
        hovermode="closest",
        plot_bgcolor="rgba(240, 240, 240, 0.9)",
    )

    print("✓ Interactive visualization created")
    print("  • Layers arranged diagonally in 3D space")
    print("  • Node size represents degree centrality")
    print("  • Inter-layer edges shown as dashed lines")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        fig.write_html(OUTPUT_FILE)
    except Exception as exc:  # pragma: no cover - logging only
        print(f"\nNote: Could not save file: {exc}")
    else:
        print(f"\n✓ Saved to: {OUTPUT_FILE}")
        print("  Open in your browser to explore interactively.")

    print("\n" + "=" * 70)
    print("Network Statistics:")
    print(f"  • Total unique individuals: {len({n for nodes in nodes_per_layer.values() for n in nodes})}")
    print(f"  • Total nodes (across all layers): {sum(len(nodes) for nodes in nodes_per_layer.values())}")
    print(f"  • Total intra-layer edges: {sum(len(edges) for edges in edges_by_layer.values())}")
    print(f"  • Total inter-layer edges: {len(inter_layer_connections)}")
    print("\nCross-layer nodes (active in multiple contexts):")
    describe_cross_layer_participation(nodes_per_layer)

    print("=" * 70)
    print("Try: hover nodes, rotate, and toggle layer visibility in the legend.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
