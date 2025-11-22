#!/usr/bin/env python3
"""
Example 7: Save and Load Pipeline - Persisting Results

This example demonstrates saving network data during pipeline execution
and loading it in a subsequent pipeline.

Runtime: FAST (< 5 seconds)
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, '../..')

from py3plex.pipeline import (
    Pipeline,
    LoadStep,
    AggregateLayers,
    SaveNetwork,
    ComputeStats,
)

print("=" * 70)
print("Example 7: Save and Load Pipeline")
print("=" * 70)

# Create a temporary directory for output
temp_dir = tempfile.mkdtemp()
network_path = os.path.join(temp_dir, 'aggregated_network.graphml')

print(f"\nTemporary directory: {temp_dir}")

# Pipeline 1: Generate, aggregate, save, and compute stats
print("\n### Pipeline 1: Generate and Save ###")
pipe1 = Pipeline([
    ("load", LoadStep(generator='random_er', n=30, l=3, p=0.15)),
    ("aggregate", AggregateLayers(method='sum')),
    ("save", SaveNetwork(path=network_path, format='graphml')),
    ("stats", ComputeStats(include_layer_stats=False)),
])

result1 = pipe1.run()
print(f"\nGenerated network saved to: {network_path}")
print(f"  Nodes: {result1['nodes']}")
print(f"  Edges: {result1['edges']}")

# Pipeline 2: Load the saved network and compute stats again
print("\n### Pipeline 2: Load and Analyze ###")
pipe2 = Pipeline([
    ("load", LoadStep(path=network_path, input_type='graphml')),
    ("stats", ComputeStats(include_layer_stats=False)),
])

result2 = pipe2.run()
print(f"\nLoaded network from: {network_path}")
print(f"  Nodes: {result2['nodes']}")
print(f"  Edges: {result2['edges']}")

# Verify consistency
print("\n### Verification ###")
if result1['nodes'] == result2['nodes'] and result1['edges'] == result2['edges']:
    print("✓ Network successfully saved and loaded!")
else:
    print("✗ Mismatch in saved/loaded network")

# Cleanup
try:
    Path(network_path).unlink()
    os.rmdir(temp_dir)
    print(f"\nCleaned up temporary files")
except Exception as e:
    print(f"\nNote: Could not clean up temporary files: {e}")

print("\n" + "=" * 70)
print("Example completed!")
print("=" * 70)
