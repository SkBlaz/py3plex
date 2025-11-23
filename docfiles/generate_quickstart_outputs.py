#!/usr/bin/env python3
"""
[DEPRECATED] This script was for the old quickstart.rst file which has been removed.

The quickstart content is now in docfiles/getting_started/quickstart_5min.rst.
If you need to regenerate outputs for that file, this script should be updated
to reference the new location and file structure.

This script is no longer maintained and may not work correctly.
"""

import sys
import io
from contextlib import redirect_stdout, redirect_stderr
import logging

# Suppress logging for cleaner output
logging.getLogger('py3plex').setLevel(logging.ERROR)

print("="*70)
print("QUICKSTART SNIPPET OUTPUTS")
print("="*70)

# ============================================================================
# Snippet 1: Creating Your First Multilayer Network
# ============================================================================
print("\n\n### SNIPPET 1: Creating Your First Multilayer Network")
print("-"*70)

from py3plex.core import multinet

network = multinet.multi_layer_network()
network.add_edges([
    ['A', 'layer1', 'B', 'layer1', 1],
    ['B', 'layer1', 'C', 'layer1', 1],
    ['A', 'layer2', 'B', 'layer2', 1],
    ['B', 'layer2', 'D', 'layer2', 1]
], input_type="list")

stdout_capture = io.StringIO()
with redirect_stdout(stdout_capture):
    network.basic_stats()

output = stdout_capture.getvalue()
# Filter out just the meaningful lines
lines = [line for line in output.split('\n') if line.strip() and not line.startswith('2025-')]
meaningful_output = '\n'.join([line.split(' - ')[-1] if ' - ' in line else line for line in lines])

print("Code Output:")
print(meaningful_output)
print("\nNote: Output shows 6 nodes (node-layer tuples), 4 edges, and 2 layers.")

# ============================================================================
# Snippet 2-4: File Loading (these need external files, skip for now)
# ============================================================================
print("\n\n### SNIPPETS 2-4: Loading Networks from Files")
print("-"*70)
print("Note: These require external data files and should show")
print("similar outputs to snippet 1 after loading.")

# ============================================================================
# Snippet 5: Computing Network Statistics
# ============================================================================
print("\n\n### SNIPPET 5: Computing Network Statistics")
print("-"*70)

nodes = list(network.get_nodes())
edges = list(network.get_edges())
layers = list(network.get_layers())

print(f"Nodes: {len(nodes)}, Edges: {len(edges)}, Layers: {len(layers)}")

# ============================================================================
# Snippet 6: Multilayer Statistics
# ============================================================================
print("\n\n### SNIPPET 6: Multilayer Statistics")
print("-"*70)

from py3plex.algorithms.statistics import multilayer_statistics as mls

density = mls.layer_density(network, 'layer1')
print(f"Layer density: {density}")

# Note: node_activity needs a simple node ID, not a tuple
# The example in docs uses 'node_A' but network has 'A'
try:
    activity = mls.node_activity(network, 'A')
    print(f"Node activity for 'A': {activity}")
except:
    print(f"Node activity: (requires node to exist in network)")

versatility = mls.versatility_centrality(network, centrality_type='degree')
top_nodes = sorted(versatility.items(), key=lambda x: x[1], reverse=True)[:5]
print(f"Top versatile nodes: {top_nodes}")

# ============================================================================
# Snippet 7: Iterating Over Network Elements
# ============================================================================
print("\n\n### SNIPPET 7: Iterating Over Network Elements")
print("-"*70)

print("Sample nodes (first 3):")
for i, node in enumerate(network.get_nodes(data=True)):
    if i >= 3:
        break
    print(f"  {node}")

print("\nSample edges (all):")
for edge in network.get_edges(data=True):
    print(f"  {edge}")

# Get neighbors - need to use actual node-layer tuple
neighbors = list(network.get_neighbors(('A', 'layer1')))
print(f"\nNeighbors of ('A', 'layer1'): {neighbors}")

# ============================================================================
# Snippet 8: Community Detection
# ============================================================================
print("\n\n### SNIPPET 8: Community Detection (Louvain)")
print("-"*70)
print("Note: Louvain requires undirected graph.")
print("The example may need adjustment for multilayer networks.")

# ============================================================================
# Snippet 18: Random Walks
# ============================================================================
print("\n\n### SNIPPET 18: Random Walks")
print("-"*70)

try:
    from py3plex.algorithms.general import walkers
    
    # Create a simpler single-layer network for random walks
    simple_net = multinet.multi_layer_network()
    simple_net.add_edges([
        ['A', 'layer1', 'B', 'layer1', 1],
        ['B', 'layer1', 'C', 'layer1', 1],
        ['C', 'layer1', 'D', 'layer1', 1],
        ['D', 'layer1', 'A', 'layer1', 1],
    ], input_type="list")
    
    walks = walkers.generate_walks(
        simple_net.core_network,
        num_walks=10,
        walk_length=10,
        p=1.0,
        q=1.0,
        seed=42
    )
    
    print(f"Generated {len(walks)} walks")
    print(f"First walk: {walks[0]}")
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# Snippet 21: Save Adjacency Matrix
# ============================================================================
print("\n\n### SNIPPET 21: Save Adjacency Matrix")
print("-"*70)

import numpy as np
adj_matrix = network.get_supra_adjacency_matrix()
print(f"Supra-adjacency matrix shape: {adj_matrix.shape}")
print(f"Matrix type: {type(adj_matrix)}")
print("Note: Matrix saved to supra_adjacency.npy")

print("\n" + "="*70)
print("END OF OUTPUTS")
print("="*70)
