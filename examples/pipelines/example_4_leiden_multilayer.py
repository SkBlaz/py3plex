#!/usr/bin/env python3
"""
Example 4: Leiden Multilayer Pipeline - Advanced Community Detection

This example demonstrates using the Leiden algorithm for multilayer
community detection. Note: This requires the leidenalg package.

Runtime: FAST (< 5 seconds)
SKIP_CI: external_deps - Requires leidenalg package
"""

import sys
sys.path.insert(0, '../..')

from py3plex.pipeline import Pipeline, LoadStep, LeidenMultilayer

print("=" * 70)
print("Example 4: Leiden Multilayer Community Detection Pipeline")
print("=" * 70)

try:
    # Pipeline: Generate multilayer network -> Leiden community detection
    pipe = Pipeline([
        ("load", LoadStep(generator='random_er', n=25, l=3, p=0.2)),
        ("community", LeidenMultilayer(
            interlayer_coupling=1.0,
            resolution=1.0,
            seed=42,
            max_iter=100
        )),
    ])
    
    print("\nPipeline structure:")
    print(pipe)
    
    print("\nRunning pipeline...")
    result = pipe.run()
    
    print("\n" + "=" * 70)
    print("Leiden Multilayer Results:")
    print("=" * 70)
    print(result.summary())
    
    # Show some community assignments
    print("\nSample community assignments:")
    for i, ((node, layer), community) in enumerate(sorted(result.communities.items())[:10]):
        print(f"  Node {node} in layer {layer}: Community {community}")
    
    if len(result.communities) > 10:
        print(f"  ... and {len(result.communities) - 10} more node-layer pairs")
    
    print("\n" + "=" * 70)
    print("Example completed!")
    print("=" * 70)

except ImportError as e:
    print("\n" + "=" * 70)
    print("ERROR: leidenalg package not installed")
    print("=" * 70)
    print("\nTo run this example, install leidenalg:")
    print("  pip install leidenalg")
    print("\nSkipping example.")
    print("=" * 70)
