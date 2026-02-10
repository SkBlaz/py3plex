#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Start with Ergonomic Helpers
===================================

This example demonstrates how the py3plex ergonomic helpers make common
tasks fast and friction-free. Perfect for first-time users who want to
get started quickly!

This is executable documentation - run it to see ergonomics in action.
No markdown files needed!
"""

import sys
from pathlib import Path

# Add parent to path for running as script
if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))

from py3plex.ergonomics import (
    quick_network,
    quick_analysis,
    quick_communities,
    show_network_summary
)


def demo_quick_network():
    """Demonstrate quick_network helper."""
    print("\n" + "=" * 70)
    print("DEMO 1: Quick Network Creation")
    print("=" * 70)
    
    print("\nTask: Create a social-work network with connections")
    print("\n✓ Using ergonomic helper:")
    print("  net = quick_network(")
    print("      people=['Alice', 'Bob', 'Carol'],")
    print("      layers=['social', 'work'],")
    print("      connections=[")
    print("          ('Alice', 'Bob', 'social'),")
    print("          ('Bob', 'Carol', 'work'),")
    print("      ]")
    print("  )")
    
    net = quick_network(
        people=['Alice', 'Bob', 'Carol', 'Diana'],
        layers=['social', 'work'],
        connections=[
            ('Alice', 'Bob', 'social'),
            ('Bob', 'Carol', 'social'),
            ('Carol', 'Diana', 'social'),
            ('Alice', 'Carol', 'work'),
            ('Bob', 'Diana', 'work'),
        ]
    )
    
    print(f"\n✓ Network created: {net}")
    print("\n  Ergonomic win: 5 lines of clean code vs 15+ with manual setup!")
    
    return net


def demo_quick_analysis(net):
    """Demonstrate quick_analysis helper."""
    print("\n" + "=" * 70)
    print("DEMO 2: Quick Analysis")
    print("=" * 70)
    
    print("\nTask: Find top hubs with multiple metrics")
    print("\n✓ Using ergonomic helper:")
    print("  results = quick_analysis(")
    print("      net,")
    print("      metrics=['degree', 'betweenness_centrality'],")
    print("      top_k=5")
    print("  )")
    
    results = quick_analysis(
        net,
        metrics=['degree', 'betweenness_centrality'],
        top_k=5
    )
    
    print(f"\n✓ Analysis complete: {results['count']} nodes analyzed")
    print(f"  Network: {results['network_stats']['nodes']} nodes, "
          f"{results['network_stats']['edges']} edges, "
          f"{results['network_stats']['layers']} layers")
    
    print("\n  Top 5 results:")
    df = results['dataframe']
    print(df[['id', 'layer', 'degree', 'betweenness_centrality']].to_string(index=False))
    
    print("\n  Ergonomic win: One function call vs building complex DSL query!")
    
    return results


def demo_quick_communities(net):
    """Demonstrate quick_communities helper."""
    print("\n" + "=" * 70)
    print("DEMO 3: Quick Community Detection")
    print("=" * 70)
    
    print("\nTask: Detect communities in multilayer network")
    print("\n✓ Using ergonomic helper:")
    print("  results = quick_communities(net, algorithm='louvain', seed=42)")
    
    results = quick_communities(net, algorithm='louvain', seed=42)
    
    print(f"\n✓ Found {results['n_communities']} communities")
    print("  Community sizes:")
    for comm_id, size in sorted(results['sizes'].items()):
        print(f"    Community {comm_id}: {size} nodes")
    
    print("\n  Ergonomic win: No imports needed, sensible defaults!")
    
    return results


def demo_network_summary(net):
    """Demonstrate show_network_summary helper."""
    print("\n" + "=" * 70)
    print("DEMO 4: Network Summary")
    print("=" * 70)
    
    print("\nTask: Get a clear overview of network structure")
    print("\n✓ Using ergonomic helper:")
    print("  show_network_summary(net)")
    
    print()
    show_network_summary(net)
    
    print("\n  Ergonomic win: Formatted summary vs manual inspection!")


def demo_comparison():
    """Show before/after comparison."""
    print("\n" + "=" * 70)
    print("BEFORE & AFTER COMPARISON")
    print("=" * 70)
    
    print("\n📝 BEFORE (Traditional approach):")
    print("=" * 40)
    print("""
from py3plex.core import multinet
from py3plex.dsl import Q

# Create network (verbose)
net = multinet.multi_layer_network(directed=False)
nodes = [{'source': person, 'type': layer} 
         for person in ['Alice', 'Bob', 'Carol']
         for layer in ['work', 'social']]
net.add_nodes(nodes)
edges = [
    {'source': 'Alice', 'target': 'Bob',
     'source_type': 'work', 'target_type': 'work'},
    # ... more edges ...
]
net.add_edges(edges)

# Analyze (complex query)
result = (Q.nodes()
          .compute('degree', 'betweenness_centrality')
          .order_by('degree', desc=True)
          .limit(5)
          .execute(net))
df = result.to_pandas()

# Detect communities (manual import)
from py3plex.algorithms.community_detection import louvain_multilayer
communities = louvain_multilayer(net, random_state=42)
from collections import Counter
sizes = Counter(communities.values())

# Total: ~30 lines of code
""")
    
    print("\n✅ AFTER (Ergonomic helpers):")
    print("=" * 40)
    print("""
from py3plex.ergonomics import (
    quick_network, quick_analysis, quick_communities
)

# Create network (clean)
net = quick_network(
    people=['Alice', 'Bob', 'Carol'],
    layers=['work', 'social'],
    connections=[('Alice', 'Bob', 'work')]
)

# Analyze (simple)
results = quick_analysis(
    net,
    metrics=['degree', 'betweenness_centrality'],
    top_k=5
)
df = results['dataframe']

# Detect communities (easy)
comm = quick_communities(net, seed=42)
sizes = comm['sizes']

# Total: ~15 lines of code, 50% reduction!
""")
    
    print("\n🎯 KEY IMPROVEMENTS:")
    print("  ✓ 50% less code")
    print("  ✓ No complex dict structures")
    print("  ✓ No manual imports for algorithms")
    print("  ✓ Sensible defaults (seed, algorithms)")
    print("  ✓ Clear, readable API")


def main():
    """Run all ergonomic demos."""
    print("\n" + "=" * 70)
    print("PY3PLEX ERGONOMIC HELPERS DEMONSTRATION")
    print("=" * 70)
    print("\nThis script shows how ergonomic helpers make py3plex fast & easy!")
    print("Perfect for first-time users and quick prototyping.")
    print("\nNo markdown documentation - this IS the documentation!")
    
    # Run demos
    net = demo_quick_network()
    demo_quick_analysis(net)
    demo_quick_communities(net)
    demo_network_summary(net)
    demo_comparison()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: Ergonomic Helpers Make py3plex Easy")
    print("=" * 70)
    print("\n✓ quick_network() - Create networks with minimal code")
    print("✓ quick_analysis() - Analyze with one function call")
    print("✓ quick_communities() - Detect communities easily")
    print("✓ show_network_summary() - Get clear overviews")
    print("\nNext steps:")
    print("  • Try these helpers in your own code")
    print("  • See user_journey_simulation.py for complete workflows")
    print("  • Explore examples/ for advanced features")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
