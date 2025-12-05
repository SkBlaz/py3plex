#!/usr/bin/env python
"""
Example: CLI Piping and DSL Queries
====================================

This example demonstrates how to use py3plex's CLI with Unix piping
for streamlined network analysis from the command line.

Usage Examples:
--------------

1. Basic Query (from file):
   $ py3plex query network.edgelist "nodes"

2. Query with filtering and JSON output:
   $ py3plex query network.edgelist "nodes where degree > 5" --output-format json

3. Query with degree computation:
   $ py3plex query network.edgelist "nodes compute degree limit 10" --output-format json

4. Reading from stdin (Unix piping):
   $ cat edges.txt | py3plex query - "nodes compute degree"

5. Chaining with other Unix tools:
   $ py3plex query network.edgelist "nodes" --output-format json | jq '.count'

6. Load network from stdin:
   $ cat edges.txt | py3plex load - --info

7. Query explain mode (show execution plan):
   $ py3plex query network.edgelist "nodes compute betweenness" --explain

DSL Query Syntax:
----------------
The simplified DSL supports:
  - nodes / edges: Select nodes or edges
  - from layer('name'): Filter by layer
  - where <attr> <op> <value>: Filter by condition (op: >, <, >=, <=, =, !=)
  - compute <measure>: Compute a measure (degree, betweenness, etc.)
  - limit N: Limit results to N items

Examples:
  nodes                                    # All nodes
  nodes from layer('social')               # Nodes in social layer
  nodes where degree > 5                   # High-degree nodes
  nodes compute degree limit 10            # Top 10 nodes by degree
  edges where intralayer                   # Edges within same layer
"""

import subprocess
import tempfile
import os


def run_example():
    """Run example CLI piping commands."""
    
    # Create a sample network file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        # Write sample multilayer network data
        f.write("Alice social Bob social\n")
        f.write("Bob social Carol social\n")
        f.write("Carol social Dave social\n")
        f.write("Alice work Bob work\n")
        f.write("Bob work Eve work\n")
        f.write("Eve work Frank work\n")
        network_file = f.name
    
    try:
        print("=" * 60)
        print("py3plex CLI Piping Examples")
        print("=" * 60)
        
        # Example 1: Basic query
        print("\n1. Basic query - list all nodes:")
        print("-" * 40)
        result = subprocess.run(
            ["py3plex", "query", network_file, "nodes"],
            capture_output=True, text=True
        )
        print(result.stdout)
        
        # Example 2: JSON output
        print("\n2. Query with JSON output:")
        print("-" * 40)
        result = subprocess.run(
            ["py3plex", "query", network_file, "nodes", "--output-format", "json"],
            capture_output=True, text=True
        )
        print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        
        # Example 3: Compute degree
        print("\n3. Compute degree centrality:")
        print("-" * 40)
        result = subprocess.run(
            ["py3plex", "query", network_file, "nodes compute degree", "--output-format", "json"],
            capture_output=True, text=True
        )
        print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        
        # Example 4: Filter with limit
        print("\n4. Filter high-degree nodes with limit:")
        print("-" * 40)
        result = subprocess.run(
            ["py3plex", "query", network_file, "nodes where degree > 1 limit 5", "--output-format", "text"],
            capture_output=True, text=True
        )
        print(result.stdout)
        
        # Example 5: Explain mode
        print("\n5. Explain query execution plan:")
        print("-" * 40)
        result = subprocess.run(
            ["py3plex", "query", network_file, "nodes compute degree", "--explain"],
            capture_output=True, text=True
        )
        print(result.stdout)
        
        # Example 6: Stdin piping
        print("\n6. Reading from stdin (piping):")
        print("-" * 40)
        input_data = "A layer1 B layer1\nB layer1 C layer1\n"
        result = subprocess.run(
            ["py3plex", "query", "-", "nodes", "--output-format", "text"],
            input=input_data, capture_output=True, text=True
        )
        print(f"Input:\n{input_data}")
        print(f"Output:\n{result.stdout}")
        
        print("\n" + "=" * 60)
        print("Examples completed successfully!")
        print("=" * 60)
        
    finally:
        # Clean up
        os.unlink(network_file)


if __name__ == "__main__":
    run_example()
