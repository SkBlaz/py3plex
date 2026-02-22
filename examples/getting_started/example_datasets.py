"""
Using built-in datasets and generators.

Shows how to list bundled datasets, load real and synthetic multilayer networks,
and spin up random generators. Prerequisites: py3plex installed (no optional
dependencies required).
"""

from __future__ import annotations

import py3plex as p3

DEFAULT_SEED = 42


def list_available_datasets() -> None:
    """Print bundled dataset names and descriptions."""
    print("=" * 60)
    print("Available Built-in Datasets")
    print("=" * 60)
    for name, description in p3.list_datasets():
        print(f"  - {name}: {description}")
    print()


def load_real_world() -> None:
    """Load a bundled real-world dataset."""
    print("=" * 60)
    print("Loading Aarhus CS Dataset")
    print("=" * 60)
    net = p3.load_aarhus_cs()
    print(f"Network: {net}")
    print(f"Nodes: {len(list(net.get_nodes()))}")
    print(f"Edges: {len(list(net.get_edges()))}")
    layer_names = net.get_layers()
    layers = layer_names[0] if isinstance(layer_names, tuple) else layer_names
    print(f"Layers ({len(layers)}): {layers}")
    print()


def load_synthetic() -> None:
    """Load the bundled synthetic multilayer dataset."""
    print("=" * 60)
    print("Loading Synthetic Multilayer Dataset")
    print("=" * 60)
    net = p3.load_synthetic_multilayer()
    print(f"Network: {net}")
    print(f"Nodes: {len(list(net.get_nodes()))}")
    print(f"Edges: {len(list(net.get_edges()))}")
    layer_names = net.get_layers()
    layers = layer_names[0] if isinstance(layer_names, tuple) else layer_names
    print(f"Layers ({len(layers)}): {layers}")
    print()


def generate_random_examples() -> None:
    """Generate several random multilayer/multiplex networks."""
    print("=" * 60)
    print("Generating Random Multilayer Network")
    print("=" * 60)
    net = p3.make_random_multilayer(
        n_nodes=30,
        n_layers=3,
        p=0.1,
        random_state=DEFAULT_SEED,
    )
    print(f"Network: {net}")
    print(f"Nodes: {len(list(net.get_nodes()))}")
    print(f"Edges: {len(list(net.get_edges()))}")
    print()

    print("=" * 60)
    print("Generating Random Multiplex Network")
    print("=" * 60)
    net = p3.make_random_multiplex(
        n_nodes=25,
        n_layers=4,
        p=0.15,
        random_state=DEFAULT_SEED,
    )
    print(f"Network: {net}")
    print(f"Nodes: {len(list(net.get_nodes()))}")
    print(f"Edges: {len(list(net.get_edges()))}")
    layer_names = net.get_layers()
    layers = layer_names[0] if isinstance(layer_names, tuple) else layer_names
    print(f"Layers ({len(layers)}): {layers}")
    print()

    print("=" * 60)
    print("Generating Synthetic Social Network")
    print("=" * 60)
    net = p3.make_social_network(n_people=20, random_state=DEFAULT_SEED)
    print(f"Network: {net}")
    print(f"Nodes: {len(list(net.get_nodes()))}")
    print(f"Edges: {len(list(net.get_edges()))}")
    layer_names = net.get_layers()
    layers = layer_names[0] if isinstance(layer_names, tuple) else layer_names
    print(f"Layers ({len(layers)}): {layers}")
    print("Layer types: friendship (dense), work (clustered), family (small cliques)")
    print()

    print("=" * 60)
    print("Generating Clique Multiplex Network")
    print("=" * 60)
    net = p3.make_clique_multiplex(
        n_nodes=15,
        n_layers=2,
        clique_size=4,
        n_cliques=3,
        random_state=DEFAULT_SEED,
    )
    print(f"Network: {net}")
    print(f"Nodes: {len(list(net.get_nodes()))}")
    print(f"Edges: {len(list(net.get_edges()))}")
    print("Structure: Multiple overlapping cliques in each layer")
    print()


def run_dsl_demo() -> None:
    """Run a small DSL query on a bundled dataset."""
    print("=" * 60)
    print("Using Datasets with DSL Queries")
    print("=" * 60)
    net = p3.load_aarhus_cs()
    query = "SELECT nodes WHERE degree > 10"
    result = p3.execute_query(net, query)
    print(f"Query: {query}")
    print(f"Result: {result['count']} nodes with degree > 10")
    print()


def main() -> int:
    """Run all dataset demonstrations."""
    list_available_datasets()
    load_real_world()
    load_synthetic()
    generate_random_examples()
    run_dsl_demo()

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
