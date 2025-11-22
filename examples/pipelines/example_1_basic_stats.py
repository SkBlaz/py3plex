#!/usr/bin/env python3
"""
Example 1: Basic Pipeline - Load and Compute Statistics

This example demonstrates the simplest pipeline: loading a network
and computing basic statistics.

Runtime: FAST (< 5 seconds)
"""

import sys
sys.path.insert(0, '../..')

from py3plex.pipeline import Pipeline, LoadStep, ComputeStats

print("=" * 70)
print("Example 1: Basic Statistics Pipeline")
print("=" * 70)

# Create a simple pipeline to load a random network and compute statistics
pipe = Pipeline([
    ("load", LoadStep(generator='random_er', n=50, l=3, p=0.1)),
    ("stats", ComputeStats(include_layer_stats=True)),
])

print("\nPipeline structure:")
print(pipe)

print("\nRunning pipeline...")
result = pipe.run()

print("\n" + "=" * 70)
print("Results:")
print("=" * 70)
print(f"Nodes: {result['nodes']}")
print(f"Edges: {result['edges']}")
print(f"Density: {result['density']:.4f}")

if 'layers' in result:
    print(f"Layers: {result['layers']}")
    if 'layer_densities' in result:
        print("\nLayer densities:")
        for layer, density in result['layer_densities'].items():
            print(f"  {layer}: {density:.4f}")

print("\n" + "=" * 70)
print("Example completed!")
print("=" * 70)
