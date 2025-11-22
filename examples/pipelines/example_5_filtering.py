#!/usr/bin/env python3
"""
Example 5: Filtering Pipeline - Load, Filter, and Analyze

This example demonstrates filtering nodes based on degree criteria
before further analysis.

Runtime: FAST (< 5 seconds)
"""

import sys
sys.path.insert(0, '../..')

from py3plex.pipeline import Pipeline, LoadStep, FilterNodes, ComputeStats

print("=" * 70)
print("Example 5: Node Filtering Pipeline")
print("=" * 70)

# First, let's create a baseline without filtering
print("\n### Baseline: Without filtering ###")
baseline_pipe = Pipeline([
    ("load", LoadStep(generator='random_er', n=50, l=2, p=0.1, directed=False)),
    ("stats", ComputeStats(include_layer_stats=False)),
])

baseline_result = baseline_pipe.run()
print(f"\nBaseline network:")
print(f"  Nodes: {baseline_result['nodes']}")
print(f"  Edges: {baseline_result['edges']}")

# Now with filtering to keep only well-connected nodes
print("\n### With filtering (min_degree=3) ###")
filtered_pipe = Pipeline([
    ("load", LoadStep(generator='random_er', n=50, l=2, p=0.1, directed=False)),
    ("filter", FilterNodes(min_degree=3)),
    ("stats", ComputeStats(include_layer_stats=False)),
])

filtered_result = filtered_pipe.run()
print(f"\nFiltered network (min_degree=3):")
print(f"  Nodes: {filtered_result['nodes']}")
print(f"  Edges: {filtered_result['edges']}")

print(f"\nNodes removed: {baseline_result['nodes'] - filtered_result['nodes']}")
print(f"Edges removed: {baseline_result['edges'] - filtered_result['edges']}")

print("\n" + "=" * 70)
print("Example completed!")
print("=" * 70)
