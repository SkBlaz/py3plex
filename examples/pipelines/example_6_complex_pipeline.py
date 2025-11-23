#!/usr/bin/env python3
"""
Example 6: Complex Pipeline - Multi-step Analysis

This example demonstrates a complex pipeline with multiple steps:
load -> filter -> aggregate -> community detection.

Runtime: FAST (< 5 seconds)
"""

import sys
sys.path.insert(0, '../..')

from py3plex.pipeline import (
    Pipeline,
    LoadStep,
    FilterNodes,
    AggregateLayers,
    LouvainCommunity,
)

print("=" * 70)
print("Example 6: Complex Multi-step Pipeline")
print("=" * 70)

# Complex pipeline with multiple transformations
pipe = Pipeline([
    ("load", LoadStep(generator='random_er', n=60, l=4, p=0.08)),
    ("filter", FilterNodes(min_degree=2)),
    ("aggregate", AggregateLayers(method='sum')),
    ("community", LouvainCommunity(resolution=1.0)),
])

print("\nPipeline structure:")
print(pipe)

print("\nPipeline steps:")
for i, (name, step) in enumerate(pipe.steps, 1):
    print(f"  {i}. {name}: {step.__class__.__name__}")

print("\nRunning complex pipeline...")
result = pipe.run()

print("\n" + "=" * 70)
print("Final Results:")
print("=" * 70)
print(f"Algorithm: {result['algorithm']}")
print(f"Number of communities: {result['num_communities']}")

# Community size distribution
community_sizes = {}
for node, comm in result['communities'].items():
    community_sizes[comm] = community_sizes.get(comm, 0) + 1

print("\nCommunity size distribution:")
for comm in sorted(community_sizes.keys()):
    print(f"  Community {comm}: {community_sizes[comm]} nodes")

# Show average community size
avg_size = sum(community_sizes.values()) / len(community_sizes)
print(f"\nAverage community size: {avg_size:.2f} nodes")

print("\n" + "=" * 70)
print("Example completed!")
print("=" * 70)
