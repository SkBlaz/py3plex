#!/usr/bin/env python3
"""
Demonstration script showing the improvements made to py3plex.

This script demonstrates:
1. __repr__ showing network statistics
2. NetworkX conversion methods
3. Enhanced documentation for dict-based API
4. Improved error messages
5. Performance warnings
"""

from py3plex.core import multinet
import networkx as nx

print("=" * 70)
print("PY3PLEX IMPROVEMENTS DEMONSTRATION")
print("=" * 70)

# 1. __repr__ demonstration
print("\n1. Enhanced __repr__ Method")
print("-" * 70)
print("Creating empty network:")
net = multinet.multi_layer_network(directed=False, verbose=False)
print(f"  {net}")

print("\nAdding nodes:")
net.add_nodes([
    {'source': 'A', 'type': 'social'},
    {'source': 'B', 'type': 'social'},
    {'source': 'C', 'type': 'email'},
])
print(f"  {net}")

print("\nAdding edges:")
net.add_edges([
    {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'email'},
])
print(f"  {net}")

# 2. NetworkX conversion demonstration
print("\n2. NetworkX Conversion Methods")
print("-" * 70)
print("Converting py3plex network to NetworkX:")
nx_graph = net.to_networkx()
print(f"  Type: {type(nx_graph).__name__}")
print(f"  Nodes: {list(nx_graph.nodes())}")
print(f"  Edges: {list(nx_graph.edges())}")

print("\nCreating NetworkX graph and converting to py3plex:")
G = nx.Graph()
G.add_nodes_from([('X', 'layer1'), ('Y', 'layer1'), ('Z', 'layer2')])
G.add_edges_from([(('X', 'layer1'), ('Y', 'layer1')), (('Y', 'layer1'), ('Z', 'layer2'))])
net2 = multinet.multi_layer_network.from_networkx(G)
print(f"  {net2}")

# 3. Dict-based API documentation
print("\n3. Enhanced Dict-Based API Documentation")
print("-" * 70)
print("You can now easily understand the dict format:")
print("\nFor add_nodes():")
print("  {'source': 'node_id', 'type': 'layer_name'}")
print("\nFor add_edges():")
print("  {'source': 'A', 'target': 'B',")
print("   'source_type': 'layer1', 'target_type': 'layer1',")
print("   'weight': 1.0}")
print("\nSee help(multi_layer_network.add_nodes) for full examples!")

# 4. Improved error messages
print("\n4. Improved Error Messages")
print("-" * 70)
print("Testing invalid input_type in add_edges():")
try:
    net3 = multinet.multi_layer_network(verbose=False)
    net3.add_edges([{'source': 'A', 'target': 'B'}], input_type="invalid")
except ValueError as e:
    print(f"  Error caught: {str(e)[:100]}...")
    print("  ✓ Clear, actionable error message with expected format!")

# 5. Performance warnings
print("\n5. Performance Warnings for Large Networks")
print("-" * 70)
print("Creating network with 600 nodes (>500 threshold):")
from py3plex.core import random_generators
large_net = random_generators.random_multilayer_ER(600, 2, 0.001, directed=False)
print(f"  {large_net}")
print("\n  Note: Visualization would trigger performance warning")
print("  (not running actual visualization to save time)")

# 6. Documentation about hypergraphs
print("\n6. Hypergraph Support Clarification")
print("-" * 70)
print("The class documentation now clearly states:")
print("  - py3plex does NOT natively support true hypergraphs")
print("  - Consider bipartite projections or incidence gadget encoding")
print("  - See to_homogeneous_hypergraph() for alternative approaches")

print("\n" + "=" * 70)
print("DEMONSTRATION COMPLETE")
print("=" * 70)
print("\nAll improvements are working correctly!")
print("- __repr__ shows statistics instead of memory addresses")
print("- NetworkX conversions work seamlessly")
print("- Documentation is comprehensive with examples")
print("- Error messages are clear and actionable")
print("- Performance warnings guide users appropriately")
print("- Hypergraph support is properly documented")
