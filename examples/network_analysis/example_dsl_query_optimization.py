"""Demonstration of DSL query optimization.

This script shows the performance improvement from automatic query optimization
when using ORDER BY with LIMIT on existing attributes.
"""

import time
from py3plex.core import multinet
from py3plex.dsl import Q, L


def create_test_network(n_nodes=100, n_layers=3):
    """Create a test multilayer network."""
    network = multinet.multi_layer_network(directed=False)
    
    layers = [f"layer{i}" for i in range(n_layers)]
    
    # Add nodes
    nodes = []
    for layer in layers:
        for i in range(n_nodes):
            nodes.append({'source': f'Node{i}', 'type': layer})
    network.add_nodes(nodes)
    
    # Add edges to create degree distribution
    edges = []
    for layer in layers:
        # Ring structure
        for i in range(n_nodes - 1):
            edges.append({
                'source': f'Node{i}',
                'target': f'Node{i+1}',
                'source_type': layer,
                'target_type': layer,
            })
        edges.append({
            'source': f'Node{n_nodes-1}',
            'target': 'Node0',
            'source_type': layer,
            'target_type': layer,
        })
        
        # Add some high-degree hubs
        for i in range(0, n_nodes, 10):
            for j in range(i + 1, min(i + 5, n_nodes)):
                edges.append({
                    'source': f'Node{i}',
                    'target': f'Node{j}',
                    'source_type': layer,
                    'target_type': layer,
                })
    
    network.add_edges(edges)
    return network


def benchmark_query(network, query_desc, query_func):
    """Run a query and measure execution time."""
    print(f"\n{query_desc}")
    print("=" * 60)
    
    start = time.time()
    result = query_func(network)
    elapsed = time.time() - start
    
    print(f"Execution time: {elapsed:.3f}s")
    print(f"Results: {len(result.items)} items")
    if hasattr(result, 'attributes') and result.attributes:
        first_attr = list(result.attributes.keys())[0]
        print(f"Computed on: {len(result.attributes[first_attr])} items")
    
    return elapsed, result


def main():
    print("DSL Query Optimization Demonstration")
    print("=" * 60)
    
    # Create test network
    print("\nCreating test network...")
    network = create_test_network(n_nodes=200, n_layers=3)
    print(f"Network: {len(list(network.get_nodes()))} nodes, "
          f"{len(list(network.get_edges()))} edges")
    
    # Test 1: Optimized query (ORDER BY existing attribute)
    def optimized_query(net):
        return (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("betweenness_centrality")
             .order_by("-degree")  # Degree already exists!
             .limit(10)
             .execute(net)
        )
    
    time1, result1 = benchmark_query(
        network,
        "Test 1: OPTIMIZED - Order by degree (existing), limit 10, then compute betweenness",
        optimized_query
    )
    
    # Test 2: Non-optimized query (ORDER BY computed attribute)
    def non_optimized_query(net):
        return (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("betweenness_centrality")
             .order_by("-betweenness_centrality")  # Must compute on all!
             .limit(10)
             .execute(net)
        )
    
    time2, result2 = benchmark_query(
        network,
        "Test 2: NOT OPTIMIZED - Order by betweenness (computed), limit 10",
        non_optimized_query
    )
    
    # Test 3: Without limit (baseline)
    def baseline_query(net):
        return (
            Q.nodes()
             .from_layers(L["layer0"])
             .compute("betweenness_centrality")
             .execute(net)
        )
    
    time3, result3 = benchmark_query(
        network,
        "Test 3: BASELINE - Compute betweenness on all nodes (no limit)",
        baseline_query
    )
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Optimized query (Test 1):     {time1:.3f}s")
    print(f"Non-optimized query (Test 2): {time2:.3f}s")
    print(f"Baseline (no limit, Test 3):  {time3:.3f}s")
    print()
    
    if time2 > 0:
        speedup = time2 / time1
        print(f"Speedup from optimization: {speedup:.1f}x")
        print(f"  → Test 1 computed on {len(result1.attributes['betweenness_centrality'])} nodes")
        print(f"  → Test 2 computed on {len(result2.attributes['betweenness_centrality'])} nodes")
    
    print("\nKEY INSIGHT:")
    print("When ordering by an existing attribute (degree), the DSL applies")
    print("LIMIT early, reducing the number of expensive computations.")
    print("This provides significant speedup for queries with expensive measures.")


if __name__ == "__main__":
    main()
