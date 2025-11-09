#!/usr/bin/env python3
"""
Simple benchmark to demonstrate configuration usage and measure basic operations.

This script demonstrates:
1. Using the centralized config module
2. Creating multilayer networks
3. Basic operations performance
4. Reproducibility with seeding
"""

import time
from typing import Dict, List

import networkx as nx

# Import py3plex
try:
    from py3plex import config
    from py3plex.core import multinet
    from py3plex.utils import get_rng
    
    print("SUCCESS: py3plex imports successful")
except ImportError as e:
    print(f"ERROR: Import failed: {e}")
    print("Make sure py3plex is installed: pip install -e .")
    exit(1)


def benchmark_network_creation(num_layers: int = 3, nodes_per_layer: int = 100) -> Dict[str, float]:
    """
    Benchmark network creation performance.
    
    Args:
        num_layers: Number of network layers
        nodes_per_layer: Number of nodes per layer
        
    Returns:
        Dictionary with timing results
    """
    results = {}
    
    # Create multilayer network
    start = time.time()
    
    mlnet = multinet.multi_layer_network(network_type="multiplex")
    
    # Add layers
    for layer_id in range(num_layers):
        G = nx.erdos_renyi_graph(nodes_per_layer, 0.1, seed=config.RANDOM_SEED)
        mlnet.add_layer(G, layer_id)
    
    results['creation_time'] = time.time() - start
    results['num_nodes'] = mlnet.get_number_of_nodes()
    results['num_edges'] = mlnet.get_number_of_edges()
    
    return results


def demonstrate_config_usage():
    """Demonstrate using the config module."""
    print("\n" + "="*60)
    print("Configuration Module Demonstration")
    print("="*60)
    
    # Show current settings
    print(f"\nStats: Current Settings:")
    print(f"  Default node size: {config.DEFAULT_NODE_SIZE}")
    print(f"  Default edge alpha: {config.DEFAULT_EDGE_ALPHA}")
    print(f"  Default color palette: {config.DEFAULT_COLOR_PALETTE}")
    print(f"  Random seed: {config.RANDOM_SEED}")
    print(f"  API version: {config.__api_version__}")
    
    # Show available color palettes
    print(f"\nPalettes: Available Color Palettes:")
    for name in config.COLOR_PALETTES.keys():
        num_colors = len(config.COLOR_PALETTES[name])
        print(f"  - {name:20s} ({num_colors} colors)")
    
    # Get a color palette
    print(f"\n🌈 Using '{config.DEFAULT_COLOR_PALETTE}' palette:")
    colors = config.get_color_palette()
    print(f"  First 3 colors: {colors[:3]}")
    
    # Show colorblind safe option
    cb_colors = config.get_color_palette("colorblind_safe")
    print(f"\n♿ Color-blind safe palette:")
    print(f"  First 3 colors: {cb_colors[:3]}")


def demonstrate_reproducibility():
    """Demonstrate reproducibility with seeding."""
    print("\n" + "="*60)
    print("Reproducibility Demonstration")
    print("="*60)
    
    # Use get_rng with seed
    rng1 = get_rng(42)
    values1 = [rng1.random() for _ in range(5)]
    
    rng2 = get_rng(42)
    values2 = [rng2.random() for _ in range(5)]
    
    print(f"\n🎲 Random values with seed=42 (first run):  {values1}")
    print(f"🎲 Random values with seed=42 (second run): {values2}")
    
    if values1 == values2:
        print("SUCCESS: Results are reproducible!")
    else:
        print("ERROR: Results differ (unexpected)")


def run_benchmarks():
    """Run performance benchmarks."""
    print("\n" + "="*60)
    print("Performance Benchmarks")
    print("="*60)
    
    test_configs = [
        (3, 50),    # Small: 3 layers, 50 nodes each
        (5, 100),   # Medium: 5 layers, 100 nodes each
        (10, 100),  # Large: 10 layers, 100 nodes each
    ]
    
    for num_layers, nodes_per_layer in test_configs:
        print(f"\nTesting: Testing {num_layers} layers × {nodes_per_layer} nodes:")
        
        try:
            results = benchmark_network_creation(num_layers, nodes_per_layer)
            
            print(f"  ⏱️  Creation time: {results['creation_time']:.3f}s")
            print(f"  Stats: Total nodes: {results['num_nodes']}")
            print(f"  Edges: Total edges: {results['num_edges']}")
            
        except Exception as e:
            print(f"  ERROR: Error: {e}")


def main():
    """Main benchmark script."""
    print("="*60)
    print("Py3plex Configuration and Performance Benchmark")
    print("="*60)
    
    # Check version
    import py3plex
    print(f"\nPackage: py3plex version: {py3plex.__version__}")
    print(f"Package: API version: {py3plex.__api_version__}")
    
    # Demonstrate config
    demonstrate_config_usage()
    
    # Demonstrate reproducibility
    demonstrate_reproducibility()
    
    # Run benchmarks
    run_benchmarks()
    
    print("\n" + "="*60)
    print("SUCCESS: Benchmark complete!")
    print("="*60)


if __name__ == "__main__":
    main()
