"""
Interactive hairball visualization with Plotly.

Generates a random multilayer Erdős–Rényi network, projects it to a
hairball view, and writes an interactive HTML plot.

Requirements: pip install plotly
Runtime: FAST (<5s)
"""

from __future__ import annotations

import os
import random
from typing import Dict, Tuple

import networkx as nx
import numpy as np
from py3plex.core import random_generators
from py3plex.visualization.multilayer import interactive_hairball_plot

OUTPUT_DIR = "output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "interactive_hairball.html")
N_NODES = 50
N_LAYERS = 3
EDGE_PROBABILITY = 0.15


def ensure_plotly_available() -> bool:
    """Return True if plotly is installed, otherwise print a hint and return False."""
    try:
        import plotly  # noqa: F401
    except ImportError:
        print(" Plotly not found. Install with: pip install plotly")
        print("  Or install py3plex with visualization extras: pip install py3plex[viz]")
        return False
    return True


def generate_network() -> multinet.multi_layer_network:
    """Create a reproducible random multilayer network."""
    return random_generators.random_multilayer_ER(
        N_NODES,
        N_LAYERS,
        EDGE_PROBABILITY,
        directed=False,
    )


def compute_layout(graph: nx.Graph) -> Dict[Tuple[str, str], np.ndarray]:
    """Compute a reproducible spring layout."""
    return nx.spring_layout(graph, iterations=50, seed=42)


def main() -> int:
    random.seed(42)
    np.random.seed(42)

    print("=" * 60)
    print("Interactive Hairball Visualization Example")
    print("=" * 60)

    if not ensure_plotly_available():
        return 0

    print("\nStep 1: Generating random multilayer network...")
    print(f"  - Nodes: {N_NODES}")
    print(f"  - Layers: {N_LAYERS}")
    print(f"  - Edge probability: {EDGE_PROBABILITY}")
    multilayer_net = generate_network()
    multilayer_net.basic_stats()

    print("\nStep 2: Converting to NetworkX graph...")
    _, graph, _ = multilayer_net.get_layers(style="hairball")

    print("\nStep 3: Computing layout with spring algorithm...")
    pos = compute_layout(graph)
    for node in graph.nodes():
        graph.nodes[node]["pos"] = pos[node]

    print("\nStep 4: Computing node sizes based on degree...")
    degrees = dict(graph.degree())
    max_degree = max(degrees.values()) if degrees else 1
    node_sizes = [10 + 40 * (degrees[node] / max_degree) for node in graph.nodes()]

    print(f"  - Nodes: {graph.number_of_nodes()}")
    print(f"  - Edges: {graph.number_of_edges()}")
    print(f"  - Avg degree: {sum(degrees.values()) / len(degrees):.2f}")

    print("\nStep 5: Creating node color mapping...")
    color_mapping = {node: node_sizes[i] for i, node in enumerate(graph.nodes())}

    print("\nStep 6: Generating interactive visualization...")
    fig = interactive_hairball_plot(
        graph,
        nsizes=node_sizes,
        final_color_mapping=color_mapping,
        pos=pos,
        colorscale="Viridis",
    )

    if fig is None:
        print(" Failed to create visualization. Check that plotly is installed.")
        return 1

    print(" Interactive visualization created successfully!")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        fig.write_html(OUTPUT_FILE)
    except Exception as exc:  # pragma: no cover - logging only
        print(f"\nNote: Could not save HTML file: {exc}")
    else:
        print(f"\n Visualization saved to: {OUTPUT_FILE}")
        print("  Open this file in your web browser to explore the network.")

    print("\n" + "=" * 60)
    print("Visualization complete! Close the browser window when done exploring.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
