#!/usr/bin/env python3
"""
Example 2: Aggregation Pipeline - Load, Aggregate, and Analyze

This example demonstrates aggregating multiple layers into a single
network and then computing statistics.

Runtime: FAST (< 5 seconds)
"""

import sys
sys.path.insert(0, '../..')

from py3plex.pipeline import Pipeline, LoadStep, AggregateLayers, ComputeStats

print("=" * 70)
print("Example 2: Layer Aggregation Pipeline")
print("=" * 70)

# Pipeline: Generate random multilayer network -> Aggregate layers -> Stats
pipe = Pipeline([
    ("load", LoadStep(generator='random_er', n=40, l=4, p=0.12)),
    ("aggregate", AggregateLayers(method='sum')),
    ("stats", ComputeStats(include_layer_stats=False)),
])

print("\nPipeline structure:")
print(pipe)

print("\nRunning pipeline...")
result = pipe.run()

print("\n" + "=" * 70)
print("Aggregated Network Statistics:")
print("=" * 70)
print(f"Nodes: {result['nodes']}")
print(f"Edges: {result['edges']}")
print(f"Density: {result['density']:.4f}")

print("\n" + "=" * 70)
print("Example completed!")
print("=" * 70)
