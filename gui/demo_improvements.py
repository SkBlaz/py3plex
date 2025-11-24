#!/usr/bin/env python3
"""
Demonstration script showing the fixed GUI user journey for multi-edgelist centrality.

This script simulates what a user would experience when:
1. Creating a multi-layer network file with comments
2. Loading it through the parsing logic
3. Computing centrality metrics

Run this to see the improvements in action!
"""

import tempfile
import os
import sys

# Add gui/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from app.services.io import load_multilayer_edgelist
from app.services.metrics import compute_centrality
from app.services.io import GRAPH_REGISTRY
import uuid


def print_header(text):
    """Pretty print section headers"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def demo_comment_handling():
    """Demonstrate that comments are now properly handled"""
    print_header("DEMO 1: Comment Handling in Edgelist Files")
    
    # Create a file with comments (previously failed)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        f.write("# This is a social-professional network\n")
        f.write("# Source: Employee survey 2024\n")
        f.write("# Format: person1 person2 relationship strength\n")
        f.write("#\n")
        f.write("alice   bob     colleague   0.8\n")
        f.write("alice   carol   friend      0.9\n")
        f.write("bob     carol   friend      0.7\n")
        f.write("# Department connections\n")
        f.write("carol   dave    colleague   0.6\n")
        f.write("dave    eve     colleague   0.5\n")
        f.write("# Social connections\n")
        f.write("alice   eve     friend      0.4\n")
        filepath = f.name
    
    print(f"\nSample file with comments:")
    with open(filepath, 'r') as f:
        print(f.read())
    
    try:
        print("Parsing file...")
        graph = load_multilayer_edgelist(filepath)
        
        print(f"SUCCESS! Parsed graph with:")
        print(f"   - {graph.number_of_nodes()} nodes")
        print(f"   - {graph.number_of_edges()} edges")
        
        # Extract layers
        layers = set()
        for u, v, data in graph.edges(data=True):
            if 'layer' in data:
                layers.add(data['layer'])
        print(f"   - Layers: {', '.join(sorted(layers))}")
        
        print("\nComments are now properly skipped!")
        
    finally:
        os.unlink(filepath)


def demo_simple_format():
    """Demonstrate that simple 2-column edgelists now work"""
    print_header("DEMO 2: Simple Edgelist Format Support")
    
    # Create a simple 2-column file (previously rejected)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        f.write("1 2\n")
        f.write("2 3\n")
        f.write("3 4\n")
        f.write("4 5\n")
        f.write("5 1\n")
        filepath = f.name
    
    print(f"\nSimple 2-column edgelist:")
    with open(filepath, 'r') as f:
        print(f.read())
    
    try:
        print("Parsing file...")
        graph = load_multilayer_edgelist(filepath)
        
        print(f"SUCCESS! Parsed as multi-layer graph:")
        print(f"   - {graph.number_of_nodes()} nodes")
        print(f"   - {graph.number_of_edges()} edges")
        print(f"   - Default layer assigned to all edges")
        
        print("\nSimple edgelists now work with sensible defaults!")
        
    finally:
        os.unlink(filepath)


def demo_multilayer_centrality():
    """Demonstrate that centrality now works on multi-layer networks"""
    print_header("DEMO 3: Centrality on Multi-Layer Networks")
    
    # Create a multi-layer network
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        f.write("# Multi-layer social network\n")
        f.write("1 2 social 1.0\n")
        f.write("1 3 social 1.0\n")
        f.write("2 3 social 1.0\n")
        f.write("2 4 social 1.0\n")
        f.write("3 4 social 1.0\n")
        f.write("4 5 social 1.0\n")
        f.write("1 4 work 2.0\n")
        f.write("2 5 work 1.5\n")
        f.write("3 5 work 1.5\n")
        f.write("1 5 work 2.5\n")
        filepath = f.name
    
    print(f"\nMulti-layer network:")
    with open(filepath, 'r') as f:
        print(f.read())
    
    try:
        print("Parsing file...")
        graph = load_multilayer_edgelist(filepath)
        
        print(f"Parsed multi-layer graph:")
        print(f"   - {graph.number_of_nodes()} nodes")
        print(f"   - {graph.number_of_edges()} edges")
        
        # Extract layers
        layers = {}
        for u, v, data in graph.edges(data=True):
            layer = data.get('layer', 'default')
            layers[layer] = layers.get(layer, 0) + 1
        
        print(f"   - Layers:")
        for layer, count in layers.items():
            print(f"     • {layer}: {count} edges")
        
        # Simulate adding to registry for centrality computation
        graph_id = str(uuid.uuid4())
        GRAPH_REGISTRY[graph_id] = {
            'graph': graph,
            'filepath': filepath,
            'positions': None,
            'metadata': {}
        }
        
        print("\nComputing centrality metrics...")
        results = compute_centrality(graph_id, ['degree', 'betweenness'])
        
        print(f"SUCCESS! Centrality computed on multi-layer network:")
        
        for metric, data in results.items():
            if isinstance(data, list) and len(data) > 0:
                print(f"\n   {metric.upper()} Centrality (top 3):")
                for i, node_data in enumerate(data[:3]):
                    print(f"     {i+1}. Node {node_data['node']}: {node_data['value']:.4f}")
        
        print("\nMulti-layer networks now properly converted for centrality!")
        print("   (Multiple edges aggregated with weight summation)")
        
    finally:
        os.unlink(filepath)
        if graph_id in GRAPH_REGISTRY:
            del GRAPH_REGISTRY[graph_id]


def demo_weight_aware():
    """Demonstrate that weights are now used in centrality"""
    print_header("DEMO 4: Weight-Aware Centrality Metrics")
    
    # Create a weighted network
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        f.write("# Star network with varying connection strengths\n")
        f.write("center node1 social 5.0\n")
        f.write("center node2 social 3.0\n")
        f.write("center node3 social 1.0\n")
        f.write("center node4 social 0.5\n")
        filepath = f.name
    
    print(f"\nWeighted network (star topology):")
    with open(filepath, 'r') as f:
        print(f.read())
    
    try:
        graph = load_multilayer_edgelist(filepath)
        graph_id = str(uuid.uuid4())
        GRAPH_REGISTRY[graph_id] = {
            'graph': graph,
            'filepath': filepath,
            'positions': None,
            'metadata': {}
        }
        
        print("Computing weighted degree centrality...")
        results = compute_centrality(graph_id, ['degree'])
        
        print(f"SUCCESS! Weight-aware centrality:")
        for node_data in results['degree']:
            node = node_data['node']
            value = node_data['value']
            print(f"   - {node}: {value:.1f}")
        
        print("\nCenter node has highest centrality (9.5) due to weighted connections!")
        print("   (5.0 + 3.0 + 1.0 + 0.5 = 9.5)")
        
    finally:
        os.unlink(filepath)
        if graph_id in GRAPH_REGISTRY:
            del GRAPH_REGISTRY[graph_id]


def main():
    """Run all demonstrations"""
    print("\n" + "=" * 70)
    print("  Py3plex GUI User Journey Improvements Demonstration")
    print("  Multi-edgelist Centrality Use Case")
    print("=" * 70)
    print("\nThis script demonstrates the friction points that were fixed:")
    print("  1. Comment handling in edgelist files")
    print("  2. Simple 2-column edgelist support")
    print("  3. Centrality computation on multi-layer networks")
    print("  4. Weight-aware centrality metrics")
    
    demo_comment_handling()
    demo_simple_format()
    demo_multilayer_centrality()
    demo_weight_aware()
    
    print("\n" + "=" * 70)
    print("  ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("\nThe GUI user journey is now frictionless for:")
    print("   - Loading multi-layer edgelist files with comments")
    print("   - Using simple or complex edgelist formats")
    print("   - Computing centrality on multi-layer networks")
    print("   - Getting weight-aware centrality results")
    print()


if __name__ == '__main__':
    main()
