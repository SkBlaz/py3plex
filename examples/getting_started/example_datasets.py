"""
Example: Using Built-in Datasets

This example demonstrates how to use py3plex's built-in datasets,
which work similarly to scikit-learn's datasets module.

py3plex provides:
- **Bundled real-world datasets**: `load_aarhus_cs()`, `load_synthetic_multilayer()`
- **Synthetic generators**: `make_random_multilayer()`, `make_random_multiplex()`,
  `make_clique_multiplex()`, `make_social_network()`
- **Utility functions**: `list_datasets()`, `get_data_dir()`

Runtime: FAST (< 5 seconds) - Standalone example suitable for CI
"""

import py3plex as p3

# List all available built-in datasets
print("=" * 60)
print("Available Built-in Datasets")
print("=" * 60)
for name, description in p3.list_datasets():
    print(f"  • {name}: {description}")
print()


# Load a real-world dataset: Aarhus CS department social network
print("=" * 60)
print("Loading Aarhus CS Dataset")
print("=" * 60)
net = p3.load_aarhus_cs()
print(f"Network: {net}")
print(f"Nodes: {len(list(net.get_nodes()))}")
print(f"Edges: {len(list(net.get_edges()))}")
layers = net.get_layers()
layer_names = layers[0] if isinstance(layers, tuple) else layers
print(f"Layers ({len(layer_names)}): {layer_names}")
print()


# Load a synthetic multilayer dataset
print("=" * 60)
print("Loading Synthetic Multilayer Dataset")
print("=" * 60)
net = p3.load_synthetic_multilayer()
print(f"Network: {net}")
print(f"Nodes: {len(list(net.get_nodes()))}")
print(f"Edges: {len(list(net.get_edges()))}")
layers = net.get_layers()
layer_names = layers[0] if isinstance(layers, tuple) else layers
print(f"Layers ({len(layer_names)}): {layer_names}")
print()


# Generate a random multilayer network
print("=" * 60)
print("Generating Random Multilayer Network")
print("=" * 60)
net = p3.make_random_multilayer(
    n_nodes=30,
    n_layers=3,
    p=0.1,
    random_state=42  # For reproducibility
)
print(f"Network: {net}")
print(f"Nodes: {len(list(net.get_nodes()))}")
print(f"Edges: {len(list(net.get_edges()))}")
print()


# Generate a random multiplex network
print("=" * 60)
print("Generating Random Multiplex Network")
print("=" * 60)
net = p3.make_random_multiplex(
    n_nodes=25,
    n_layers=4,
    p=0.15,
    random_state=42
)
print(f"Network: {net}")
print(f"Nodes: {len(list(net.get_nodes()))}")
print(f"Edges: {len(list(net.get_edges()))}")
layers = net.get_layers()
layer_names = layers[0] if isinstance(layers, tuple) else layers
print(f"Layers ({len(layer_names)}): {layer_names}")
print()


# Generate a social network with named layers
print("=" * 60)
print("Generating Synthetic Social Network")
print("=" * 60)
net = p3.make_social_network(
    n_people=20,
    random_state=42
)
print(f"Network: {net}")
print(f"Nodes: {len(list(net.get_nodes()))}")
print(f"Edges: {len(list(net.get_edges()))}")
layers = net.get_layers()
layer_names = layers[0] if isinstance(layers, tuple) else layers
print(f"Layers ({len(layer_names)}): {layer_names}")
print("Layer types: friendship (dense), work (clustered), family (small cliques)")
print()


# Generate a clique multiplex network (good for community detection testing)
print("=" * 60)
print("Generating Clique Multiplex Network")
print("=" * 60)
net = p3.make_clique_multiplex(
    n_nodes=15,
    n_layers=2,
    clique_size=4,
    n_cliques=3,
    random_state=42
)
print(f"Network: {net}")
print(f"Nodes: {len(list(net.get_nodes()))}")
print(f"Edges: {len(list(net.get_edges()))}")
print("Structure: Multiple overlapping cliques in each layer")
print()


# Using datasets with DSL queries
print("=" * 60)
print("Using Datasets with DSL Queries")
print("=" * 60)
net = p3.load_aarhus_cs()
result = p3.execute_query(net, "SELECT nodes WHERE degree > 10")
print(f"Query: SELECT nodes WHERE degree > 10")
print(f"Result: {result['count']} nodes with degree > 10")
print()


print("=" * 60)
print("Example completed successfully!")
print("=" * 60)
