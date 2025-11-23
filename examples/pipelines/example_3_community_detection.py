#!/usr/bin/env python3
"""
Example 3: Community Detection Pipeline - Load and Detect Communities

This example demonstrates using the Louvain algorithm for community
detection in a pipeline.

Runtime: FAST (< 5 seconds)
"""

import sys
sys.path.insert(0, '../..')

from py3plex.pipeline import Pipeline, LoadStep, LouvainCommunity

print("=" * 70)
print("Example 3: Community Detection Pipeline")
print("=" * 70)

# Pipeline: Generate network -> Detect communities with Louvain
pipe = Pipeline([
    ("load", LoadStep(generator='random_er', n=30, l=2, p=0.15)),
    ("community", LouvainCommunity(resolution=1.0)),
])

print("\nPipeline structure:")
print(pipe)

print("\nRunning pipeline...")
result = pipe.run()

print("\n" + "=" * 70)
print("Community Detection Results:")
print("=" * 70)
print(f"Algorithm: {result['algorithm']}")
print(f"Number of communities: {result['num_communities']}")

# Show community size distribution
community_sizes = {}
for node, comm in result['communities'].items():
    community_sizes[comm] = community_sizes.get(comm, 0) + 1

print("\nCommunity size distribution:")
for comm in sorted(community_sizes.keys()):
    print(f"  Community {comm}: {community_sizes[comm]} nodes")

print("\n" + "=" * 70)
print("Example completed!")
print("=" * 70)
