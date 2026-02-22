"""
Multilayer Example: Supra-Adjacency Matrix Operations

This example demonstrates how to:
1. Generate random multiplex networks
2. Compute supra-adjacency matrices
3. Load multiplex networks with layer mappings
4. Visualize matrix structure
5. Understand node ordering in matrices

The supra-adjacency matrix is a fundamental representation that:
- Combines all layers into a single block matrix
- Includes intra-layer connections (within layers)
- Includes inter-layer connections (between layers)
- Enables tensor-based multilayer network analysis

Use cases:
- Mathematical analysis of multilayer networks
- Spectral analysis and eigenvalue decomposition
- Matrix-based algorithms (diffusion, centrality)
- Understanding network structure at the matrix level

SKIP_CI: external_deps - Requires specific dataset files
"""

import os
from py3plex.core import multinet, random_generators
from py3plex.utils import get_dataset_path

print("=" * 70)
print("SUPRA-ADJACENCY MATRIX OPERATIONS")
print("=" * 70)

print("\nExample 1: Random Erdos-Renyi Multiplex Network")
print("-" * 70)

# Generate a random multiplex network
print("  Generating network...")
print("    Nodes: 500")
print("    Layers: 8")
print("    Edge probability: 0.05")

ER_multilayer = random_generators.random_multiplex_ER(
    500,     # Number of nodes
    8,       # Number of layers
    0.05,    # Edge probability
    directed=False
)

print("  [OK] Network generated")

# Compute the supra-adjacency matrix
print("\n  Computing supra-adjacency matrix...")
mtx = ER_multilayer.get_supra_adjacency_matrix()

print(f"  [OK] Matrix computed")
print(f"  Matrix shape: {mtx.shape}")
print(f"  Matrix type: {type(mtx)}")
print(f"  Non-zero entries: {mtx.nnz if hasattr(mtx, 'nnz') else 'N/A'}")

print("""
  Structure: The supra-adjacency matrix is block-structured:
  - Diagonal blocks: Intra-layer adjacency matrices
  - Off-diagonal blocks: Inter-layer coupling (if present)
  - For 8 layers with 500 nodes: 4000x4000 matrix
""")

print("\nExample 2: Multiplex Network with Layer Names")
print("-" * 70)

# Define file paths
edgelist_path = get_dataset_path('simple_multiplex.edgelist')
layer_names_path = get_dataset_path('simple_multiplex.txt')

# Check if files exist
if not os.path.exists(edgelist_path):
    print(f"  [X] Edgelist file not found: {edgelist_path}")
    print("  Skipping multiplex example...")
else:
    print("  Loading multiplex network...")

    # Create a multiplex network
    # Multiplex: same nodes across layers, only intra-layer edges
    comNet = multinet.multi_layer_network(
        network_type="multiplex",
        coupling_weight=1  # Weight for inter-layer connections
    ).load_network(
        edgelist_path,
        directed=False,
        input_type='multiplex_edges'
    )

    print("  [OK] Network loaded")

    # Display basic statistics
    print("\n  Network statistics:")
    comNet.basic_stats()

    # Load layer name mapping if available
    if os.path.exists(layer_names_path):
        print(f"\n  Loading layer names from: {layer_names_path}")
        comNet.load_layer_name_mapping(layer_names_path)
        print("  [OK] Layer names loaded")
    else:
        print(f"\n  [X] Layer names file not found: {layer_names_path}")

    # Compute supra-adjacency matrix
    print("\n  Computing supra-adjacency matrix...")
    mat = comNet.get_supra_adjacency_matrix()

    print(f"  [OK] Matrix computed")
    print(f"  Matrix shape: {mat.shape}")
    print(f"  Rows/Cols per layer: {mat.shape[0] // comNet.layer_count}")

    # Visualize the matrix structure
    print("\n  Visualizing matrix structure...")
    try:
        kwargs = {"display": True}
        comNet.visualize_matrix(kwargs)
        print("  [OK] Visualization complete (close window to continue)")
    except Exception as e:
        print(f"  [X] Visualization error: {e}")

    # Show node ordering in matrix
    print("\n  Node ordering in matrix:")
    print("  " + "-" * 66)

    # Display sample edges to show structure
    print("\n  Sample edges (showing internal representation):")
    edge_count = 0
    for edge in comNet.get_edges(data=True):
        if edge_count < 10:
            print(f"    {edge}")
            edge_count += 1
        else:
            break

    print(f"\n  ... ({len(list(comNet.get_edges()))} total edges)")

    # Show node order in matrix
    print("\n  Node order used in matrix construction:")
    if hasattr(comNet, 'node_order_in_matrix'):
        node_order = comNet.node_order_in_matrix
        print(f"    Total node-layer pairs: {len(node_order)}")
        print(f"    First 10 entries: {node_order[:10]}")
        print(f"    Last 10 entries: {node_order[-10:]}")
    else:
        print("    Node ordering not available in network object")

print("\n" + "=" * 70)
print("SUPRA-ADJACENCY MATRIX OPERATIONS COMPLETE")
print("=" * 70)

print("""
Key Concepts:

1. Supra-Adjacency Matrix Structure:
   - Block matrix combining all layers
   - Each block represents layer adjacency
   - Diagonal blocks = intra-layer edges
   - Off-diagonal blocks = inter-layer edges

2. Matrix Dimensions:
   - For N nodes and L layers: (NxL) x (NxL) matrix
   - Often sparse (many zero entries)
   - Can be very large for big networks

3. Applications:
   - Spectral analysis (eigenvalues, eigenvectors)
   - Random walks on multilayer networks
   - Diffusion processes
   - Centrality measures
   - Network comparison

4. Node Ordering:
   - Order matters for matrix interpretation
   - Typically: layer1_node1, layer1_node2, ..., layer2_node1, ...
   - Check node_order_in_matrix for exact ordering

Next Steps:
   - Perform eigenvalue decomposition
   - Compute matrix-based centralities
   - Analyze spectral properties
   - Compare with single-layer networks
""")

print("For more information, see the py3plex documentation on:")
print("  - Supra-adjacency matrices")
print("  - Tensor representations")
print("  - Matrix-based multilayer algorithms")
