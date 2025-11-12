#!/usr/bin/env python3
"""
Tensor-based operations example (headless version).

This is a headless version of example_tensorial_manipulation.py that can be run
in CI without requiring display/visualization dependencies.

Runtime: FAST (< 10 seconds)
"""

from py3plex.core import random_generators

# initiate an instance of a random graph
ER_multilayer = random_generators.random_multilayer_ER(
    50,  # Smaller network for faster execution
    3,   # Number of layers
    0.05,
    directed=False
)

print("[OK] Generated multilayer network with 50 nodes and 3 layers")

# Test the supra-adjacency matrix (this was previously broken)
# The fix allows get_supra_adjacency_matrix to work with dense format
sparse_matrix = ER_multilayer.get_supra_adjacency_matrix(mtype="sparse")
print(f"[OK] Sparse supra-adjacency matrix shape: {sparse_matrix.shape}")

# Test with dense format (this exercises the fixed code path)
dense_matrix = ER_multilayer.get_supra_adjacency_matrix(mtype="dense")
print(f"[OK] Dense supra-adjacency matrix shape: {dense_matrix.shape}")

# Get some nodes and edges (these work with generators)
some_nodes = list(ER_multilayer.get_nodes())[0:5]
some_edges = list(ER_multilayer.get_edges())[0:5]

print(f"[OK] Retrieved {len(some_nodes)} nodes and {len(some_edges)} edges")

# random node is accessed as follows
if some_nodes:
    print(f"[OK] Sample node: {ER_multilayer[some_nodes[0]]}")

# and random edge as
if some_edges:
    print(f"Sample edge: {ER_multilayer[some_edges[0][0]][some_edges[0][1]]}")

print("\nAll tensorial operations completed successfully!")
