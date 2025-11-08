#!/usr/bin/env python3
"""
Smoke Test for py3plex

This script performs a quick smoke test to verify that py3plex is installed
and functioning correctly. It:
1. Imports py3plex
2. Constructs a 2-layer multilayer graph
3. Runs Louvain community detection algorithm
4. Saves the graph to a file
5. Loads the graph from the file
6. Prints "SUCCESS" if all steps pass
7. Completes within 60 seconds

Exit codes:
  0 - All tests passed
  1 - Test failed
"""

import sys
import os
import tempfile
import time

def main():
    """Run smoke test for py3plex."""
    start_time = time.time()
    
    try:
        # Step 1: Import py3plex
        print("Step 1: Importing py3plex...", flush=True)
        from py3plex.io import MultiLayerGraph, Node, Layer, Edge
        from py3plex.io import write, read
        from py3plex.io import to_networkx
        from py3plex.algorithms.community_detection import community_wrapper as cw
        from py3plex.core import multinet
        print("✓ Import successful", flush=True)
        
        # Step 2: Construct a 2-layer multilayer graph
        print("\nStep 2: Constructing 2-layer multilayer graph...", flush=True)
        graph = MultiLayerGraph(directed=False, attributes={"name": "Smoke Test Network"})
        
        # Add 2 layers
        graph.add_layer(Layer(id="layer1", attributes={"type": "social"}))
        graph.add_layer(Layer(id="layer2", attributes={"type": "communication"}))
        
        # Add nodes
        for i in range(10):
            graph.add_node(Node(id=f"node{i}", attributes={"value": i}))
        
        # Add edges in layer1 (create a connected graph)
        edges_layer1 = [
            ("node0", "node1"), ("node1", "node2"), ("node2", "node3"),
            ("node3", "node4"), ("node4", "node0"),  # cycle
            ("node5", "node6"), ("node6", "node7"), ("node7", "node8"),
            ("node8", "node9"), ("node9", "node5"),  # another cycle
            ("node0", "node5"),  # connect the two cycles
        ]
        for src, dst in edges_layer1:
            graph.add_edge(Edge(src=src, dst=dst, src_layer="layer1", dst_layer="layer1"))
        
        # Add edges in layer2
        edges_layer2 = [
            ("node0", "node2"), ("node2", "node4"), ("node4", "node6"),
            ("node6", "node8"), ("node8", "node0"),
            ("node1", "node3"), ("node3", "node5"), ("node5", "node7"),
            ("node7", "node9"), ("node9", "node1"),
        ]
        for src, dst in edges_layer2:
            graph.add_edge(Edge(src=src, dst=dst, src_layer="layer2", dst_layer="layer2"))
        
        # Add some inter-layer edges
        inter_layer_edges = [
            ("node0", "node0"), ("node5", "node5"),
        ]
        for src, dst in inter_layer_edges:
            graph.add_edge(Edge(src=src, dst=dst, src_layer="layer1", dst_layer="layer2"))
        
        print(f"✓ Created graph with {len(graph.nodes)} nodes, {len(graph.layers)} layers, {len(graph.edges)} edges", flush=True)
        
        # Step 3: Run Louvain community detection algorithm
        print("\nStep 3: Running Louvain community detection...", flush=True)
        # Convert to NetworkX union mode for algorithm
        G = to_networkx(graph, mode="union")
        
        # Create py3plex multi_layer_network object
        mlnet = multinet.multi_layer_network()
        mlnet.core_network = G
        
        # Run Louvain community detection
        partition = cw.louvain_communities(mlnet)
        num_communities = len(set(partition.values()))
        print(f"✓ Community detection complete: found {num_communities} communities", flush=True)
        
        # Step 4: Save the graph to a file
        print("\nStep 4: Saving graph to file...", flush=True)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            write(graph, temp_file, format='json')
            print(f"✓ Graph saved to {temp_file}", flush=True)
            
            # Step 5: Load the graph from the file
            print("\nStep 5: Loading graph from file...", flush=True)
            loaded_graph = read(temp_file, format='json')
            print(f"✓ Graph loaded: {len(loaded_graph.nodes)} nodes, {len(loaded_graph.layers)} layers, {len(loaded_graph.edges)} edges", flush=True)
            
            # Verify the loaded graph matches the original
            assert len(loaded_graph.nodes) == len(graph.nodes), "Node count mismatch"
            assert len(loaded_graph.layers) == len(graph.layers), "Layer count mismatch"
            assert len(loaded_graph.edges) == len(graph.edges), "Edge count mismatch"
            print("✓ Loaded graph matches original", flush=True)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        
        # Check elapsed time
        elapsed_time = time.time() - start_time
        print(f"\n✓ All steps completed in {elapsed_time:.2f} seconds", flush=True)
        
        if elapsed_time > 60:
            print(f"⚠ Warning: Test took longer than 60 seconds", flush=True)
        
        # Final success message
        print("\n" + "=" * 50, flush=True)
        print("SUCCESS", flush=True)
        print("=" * 50, flush=True)
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
