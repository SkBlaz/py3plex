"""
Example R script demonstrating py3plex R interoperability.

This Python script shows the expected usage patterns when called from R
via the reticulate package. It serves as both documentation and a
reference implementation.

Save this as r_interop_example.py and use from R as shown below.
"""

import sys
from pathlib import Path

# Ensure py3plex is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import py3plex as p3
from py3plex.wrappers import r_interop


def create_sample_multilayer_network():
    """
    Create a sample multilayer social network for demonstration.
    
    This creates a network with two layers (Facebook and Twitter)
    representing different social media platforms.
    """
    # Create multilayer network
    net = p3.multi_layer_network()
    
    # Add nodes across different layers
    nodes = [
        {"source": "Alice", "type": "facebook"},
        {"source": "Bob", "type": "facebook"},
        {"source": "Charlie", "type": "facebook"},
        {"source": "Alice", "type": "twitter"},
        {"source": "Bob", "type": "twitter"},
        {"source": "Diana", "type": "twitter"},
    ]
    net.add_nodes(nodes)
    
    # Add intra-layer edges (connections within same platform)
    edges = [
        {"source": "Alice", "target": "Bob", "source_type": "facebook", "target_type": "facebook", "weight": 0.8},
        {"source": "Bob", "target": "Charlie", "source_type": "facebook", "target_type": "facebook", "weight": 0.6},
        {"source": "Alice", "target": "Bob", "source_type": "twitter", "target_type": "twitter", "weight": 0.9},
        {"source": "Bob", "target": "Diana", "source_type": "twitter", "target_type": "twitter", "weight": 0.7},
    ]
    net.add_edges(edges)
    
    return net


def example_basic_conversion():
    """
    Example 1: Basic conversion to igraph for R.
    
    R equivalent:
    ```R
    library(reticulate)
    library(igraph)
    
    # Source this Python script
    source_python("r_interop_example.py")
    
    # Create network
    net <- create_sample_multilayer_network()
    
    # Convert to igraph (union mode merges all layers)
    g <- r_interop$to_igraph_for_r(net, mode='union')
    
    # Use R's igraph functions
    print(vcount(g))  # Number of vertices
    print(ecount(g))  # Number of edges
    plot(g)           # Visualize
    ```
    """
    print("=== Example 1: Basic Conversion ===")
    
    net = create_sample_multilayer_network()
    
    # Convert to igraph (union mode - simplest for R)
    g = r_interop.to_igraph_for_r(net, mode='union')
    
    print(f"Network converted to igraph:")
    print(f"  Vertices: {g.vcount()}")
    print(f"  Edges: {g.ecount()}")
    print(f"  Directed: {g.is_directed()}")
    
    return g


def example_export_dataframes():
    """
    Example 2: Export as data frames for R analysis.
    
    R equivalent:
    ```R
    library(reticulate)
    
    source_python("r_interop_example.py")
    
    # Create network
    net <- create_sample_multilayer_network()
    
    # Export edge list as data frame
    edges <- r_interop$export_edgelist(net, include_attributes=TRUE)
    edges_df <- as.data.frame(do.call(rbind, lapply(edges, as.data.frame)))
    
    # Export node list as data frame
    nodes <- r_interop$export_nodelist(net, include_attributes=TRUE)
    nodes_df <- as.data.frame(do.call(rbind, lapply(nodes, as.data.frame)))
    
    # Analyze with R
    summary(edges_df)
    head(nodes_df)
    ```
    """
    print("\n=== Example 2: Export Data Frames ===")
    
    net = create_sample_multilayer_network()
    
    # Export edge list
    edges = r_interop.export_edgelist(net, include_attributes=True)
    print(f"\nEdge list ({len(edges)} edges):")
    for edge in edges[:3]:  # Show first 3
        print(f"  {edge}")
    
    # Export node list
    nodes = r_interop.export_nodelist(net, include_attributes=True)
    print(f"\nNode list ({len(nodes)} nodes):")
    for node in nodes[:3]:  # Show first 3
        print(f"  {node}")
    
    return edges, nodes


def example_graph_statistics():
    """
    Example 3: Get network statistics for R.
    
    R equivalent:
    ```R
    library(reticulate)
    
    source_python("r_interop_example.py")
    
    # Create network
    net <- create_sample_multilayer_network()
    
    # Get statistics
    stats <- r_interop$get_network_stats(net)
    
    print(paste("Nodes:", stats$num_nodes))
    print(paste("Edges:", stats$num_edges))
    print(paste("Layers:", stats$num_layers))
    print(paste("Directed:", stats$directed))
    ```
    """
    print("\n=== Example 3: Network Statistics ===")
    
    net = create_sample_multilayer_network()
    
    # Get statistics
    stats = r_interop.get_network_stats(net)
    
    print(f"Network statistics:")
    print(f"  Nodes: {stats['num_nodes']}")
    print(f"  Edges: {stats['num_edges']}")
    print(f"  Layers: {stats['num_layers']}")
    print(f"  Directed: {stats['directed']}")
    
    if stats['layer_stats']:
        print(f"  Per-layer stats:")
        for layer, layer_stats in stats['layer_stats'].items():
            print(f"    {layer}: {layer_stats}")
    
    return stats


def example_adjacency_matrix():
    """
    Example 4: Export adjacency matrix for R.
    
    R equivalent:
    ```R
    library(reticulate)
    
    source_python("r_interop_example.py")
    
    # Create network
    net <- create_sample_multilayer_network()
    
    # Get adjacency matrix
    adj_list <- r_interop$export_adjacency(net, mode='union')
    
    # Convert to R matrix
    n <- length(adj_list)
    adj_matrix <- matrix(unlist(adj_list), nrow=n, byrow=TRUE)
    
    # Matrix operations in R
    print(adj_matrix)
    eigen_result <- eigen(adj_matrix)
    print(eigen_result$values)
    ```
    """
    print("\n=== Example 4: Adjacency Matrix ===")
    
    net = create_sample_multilayer_network()
    
    # Get adjacency matrix
    adj = r_interop.export_adjacency(net, mode='union')
    
    print(f"Adjacency matrix ({len(adj)}x{len(adj[0]) if adj else 0}):")
    for i, row in enumerate(adj[:5]):  # Show first 5 rows
        print(f"  Row {i}: {row[:5]}")  # Show first 5 columns
    
    return adj


def example_complete_workflow():
    """
    Example 5: Complete workflow - create, analyze, export.
    
    R equivalent:
    ```R
    library(reticulate)
    library(igraph)
    
    # Import py3plex modules
    py3plex <- import("py3plex")
    r_interop <- import("py3plex.wrappers.r_interop")
    
    # Create multilayer network
    net <- py3plex$multi_layer_network()
    
    # Add nodes
    net$add_nodes(list(
      list(source='A', type='layer1'),
      list(source='B', type='layer1'),
      list(source='C', type='layer2')
    ))
    
    # Add edges
    net$add_edges(list(
      list(source='A', target='B', source_type='layer1', target_type='layer1')
    ))
    
    # Get comprehensive data
    graph_data <- r_interop$export_graph_data(net)
    
    # Convert to igraph for analysis
    g <- r_interop$to_igraph_for_r(net, mode='union')
    
    # Perform R analysis
    deg <- degree(g)
    between <- betweenness(g)
    close <- closeness(g)
    
    # Create results data frame
    results <- data.frame(
      node = V(g)$name,
      degree = deg,
      betweenness = between,
      closeness = close
    )
    
    print(results)
    ```
    """
    print("\n=== Example 5: Complete Workflow ===")
    
    net = create_sample_multilayer_network()
    
    # Get comprehensive graph data
    graph_data = r_interop.export_graph_data(net)
    
    print(f"Complete graph data structure:")
    print(f"  Keys: {list(graph_data.keys())}")
    print(f"  Nodes: {len(graph_data['nodes'])}")
    print(f"  Edges: {len(graph_data['edges'])}")
    print(f"  Layers: {graph_data['layers']}")
    
    # Convert for analysis
    g = r_interop.to_igraph_for_r(net, mode='union')
    
    print(f"\nConverted to igraph for analysis:")
    print(f"  Ready for R igraph functions")
    
    return graph_data, g


def main():
    """Run all examples."""
    print("=" * 60)
    print("py3plex R Interoperability Examples")
    print("=" * 60)
    
    example_basic_conversion()
    example_export_dataframes()
    example_graph_statistics()
    example_adjacency_matrix()
    example_complete_workflow()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
    print("\nTo use these from R, install reticulate and run:")
    print("  library(reticulate)")
    print("  source_python('r_interop_example.py')")


if __name__ == "__main__":
    main()
