"""
Example demonstrating the improved import experience after DX improvements.

This example shows how the new top-level imports make py3plex more accessible
to beginners and align with NetworkX conventions.
"""

# ============================================================================
# BEFORE (Old way - still works)
# ============================================================================
# from py3plex.core.multinet import multi_layer_network
# from py3plex.core import random_generators

# ============================================================================
# AFTER (New way - simpler and more intuitive)
# ============================================================================
from py3plex import multi_layer_network, random_generators

# ============================================================================
# Example 1: Create a simple network manually
# ============================================================================
print("Example 1: Manual network creation")
print("-" * 50)

network = multi_layer_network()

# Add nodes
network.add_nodes_from([
    ("Alice", "friends"),
    ("Bob", "friends"),
    ("Carol", "friends"),
    ("Alice", "coworkers"),
    ("Bob", "coworkers"),
])

# Add edges
network.add_edges_from([
    ("Alice", "Bob", "friends"),
    ("Bob", "Carol", "friends"),
    ("Alice", "Bob", "coworkers"),
])

print(f"✓ Created network with {network.number_of_nodes()} nodes")
print(f"✓ Network has {network.number_of_edges()} edges")
print(f"✓ Layers: {network.get_layers()}")

# ============================================================================
# Example 2: Generate a random multilayer network
# ============================================================================
print("\nExample 2: Random network generation")
print("-" * 50)

# Generate a random multilayer Erdős-Rényi network
random_network = random_generators.random_multilayer_ER(
    n=30,        # 30 nodes
    layers=3,    # 3 layers
    p=0.1,       # Edge probability
    directed=False
)

print(f"✓ Generated random network with {random_network.number_of_nodes()} nodes")
print(f"✓ Network has {random_network.number_of_edges()} edges")
print(f"✓ Layers: {random_network.get_layers()}")

# ============================================================================
# Example 3: Query the network
# ============================================================================
print("\nExample 3: Network queries")
print("-" * 50)

# Get all nodes
nodes = list(network.get_nodes())
print(f"✓ Total nodes: {len(nodes)}")
print(f"  First 3 nodes: {nodes[:3]}")

# Get all edges
edges = list(network.get_edges())
print(f"✓ Total edges: {len(edges)}")
print(f"  First 3 edges: {edges[:3]}")

# Get layers
layers = network.get_layers()
print(f"✓ Layers: {layers}")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 50)
print("✅ DX Improvement Summary:")
print("=" * 50)
print("✓ Simpler imports: from py3plex import multi_layer_network")
print("✓ More intuitive for beginners")
print("✓ Aligns with NetworkX conventions")
print("✓ Reduces cognitive load")
print("=" * 50)
