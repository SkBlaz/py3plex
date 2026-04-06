"""
Embeddings Example: Node2Vec Embedding Construction and Visualization

This example demonstrates how to:
1. Load a network from GML format
2. Generate node embeddings using Node2Vec
3. Visualize embeddings using t-SNE dimensionality reduction
4. Export embedding coordinates to JSON

Node embeddings represent nodes as vectors in a continuous space,
preserving network structure. They're useful for:
- Node classification
- Link prediction
- Community detection
- Network visualization

IMPORTANT: This example requires the Node2Vec binary or Python package.

Options:
1. Install Python package: pip install node2vec
2. Download C++ binary from: https://github.com/snap-stanford/snap
3. Use alternative embeddings: DeepWalk, LINE, etc.

SKIP_CI: external_deps - Requires specific dataset files (cora.gml)
"""

import os
import json
import tempfile
from py3plex.core import multinet
from py3plex.wrappers import train_node2vec_embedding
from py3plex.visualization.embedding_visualization import embedding_visualization
from py3plex.visualization.embedding_visualization import embedding_tools
from py3plex.exceptions import ExternalToolError
from py3plex.utils import get_dataset_path

print("=" * 70)
print("NODE2VEC EMBEDDING CONSTRUCTION AND VISUALIZATION")
print("=" * 70)

# Define file paths
input_network = get_dataset_path("imdb_gml.gml")
edgelist_file = get_dataset_path("test.edgelist")
embedding_file = get_dataset_path("test_embedding.emb")
cached_json_output = get_dataset_path("embedding_coordinates.json")
json_output = get_dataset_path("embedding_coordinates.json")

# Check if input file exists
if not os.path.exists(input_network):
    print(f"Error: Input file '{input_network}' not found.")
    print("This example requires the IMDB network dataset.")
    exit(1)

print(f"\nStep 1: Loading network from GML format")
print("-" * 70)
print(f"  Input file: {input_network}")

# Load network in GML format
multilayer_network = multinet.multi_layer_network().load_network(
    input_network,
    directed=True,
    input_type="gml"
)

print("  [OK] Network loaded successfully!")

print(f"\nStep 2: Saving network as edgelist for Node2Vec")
print("-" * 70)
print(f"  Output file: {edgelist_file}")

# Save network as edgelist format (required by Node2Vec binary)
# Format: source_node target_node (one edge per line)
multilayer_network.save_network(edgelist_file)

print("  [OK] Edgelist saved successfully!")

print(f"\nStep 3: Generating Node2Vec embeddings")
print("-" * 70)
print(f"  Embedding file: {embedding_file}")

print("""
IMPORTANT: Node2Vec binary requirements
---------------------------------------
This step requires a Node2Vec binary or Python package.

Installation options:
1. Python package (recommended):
   pip install node2vec

2. C++ binary (faster for large networks):
   Download from: https://github.com/snap-stanford/snap
   Place binary in current directory or add to PATH

3. Alternative embedding methods:
   - DeepWalk: pip install deepwalk
   - LINE: pip install line
   - Use py3plex's built-in methods

Attempting to call Node2Vec binary...
""")

try:
    # Call Node2Vec binary to generate embeddings
    # Parameters can be tuned based on your network:
    # - dimensions: embedding dimensionality (default: 128)
    # - walk-length: length of random walks (default: 80)
    # - num-walks: number of walks per node (default: 10)
    # - p, q: return and in-out parameters (default: 1, 1)

    train_node2vec_embedding.call_node2vec_binary(
        edgelist_file,
        embedding_file,
        binary="./node2vec",  # Assumes node2vec is in PATH or current dir
        weighted=False
    )

    print("  [OK] Node2Vec embeddings generated successfully!")

except (FileNotFoundError, ExternalToolError) as e:
    if os.path.exists(embedding_file):
        print(f"  [!] Node2Vec binary not found: {e}")
        print("  [OK] Falling back to existing embedding file already present in datasets/")
    else:
        print(f"  [!] Node2Vec binary not found: {e}")
        print("  Skipping the rest of the example because no embedding file is available.")
        raise SystemExit(1)
except Exception as e:
    print(f"  [X] Error generating embeddings: {e}")
    if os.path.exists(embedding_file):
        print("  [OK] Falling back to the existing embedding file.")
    else:
        print("  Skipping the rest of the example.")
        raise SystemExit(1)

print(f"\nStep 4: Loading embeddings into network object")
print("-" * 70)

# Load the generated embeddings into the network object
# This associates each node with its embedding vector
multilayer_network.load_embedding(embedding_file)

print("  [OK] Embeddings loaded successfully!")

print(f"\nStep 5: Visualizing embeddings using t-SNE")
print("-" * 70)
print("""
t-SNE (t-Distributed Stochastic Neighbor Embedding) reduces
high-dimensional embeddings to 2D for visualization.

For faster computation, consider:
  - Multicore t-SNE: pip install MulticoreTSNE
  - UMAP: pip install umap-learn (often faster than t-SNE)

Generating visualization...
""")

use_cached_projection = os.path.exists(cached_json_output)

if use_cached_projection:
    print("  [OK] Using cached 2D projection from datasets/ to keep the example fast.")
else:
    try:
        # Visualize the embeddings
        # This creates a 2D scatter plot of nodes based on their embeddings
        # Nodes that are structurally similar will be close together
        embedding_visualization.visualize_embedding(multilayer_network)

        print("  [OK] Visualization complete!")
        print("  (Close the window to continue)")

    except Exception as e:
        print(f"  [X] Visualization error: {e}")
        print("  Continuing with coordinate export...")

print(f"\nStep 6: Exporting embedding coordinates")
print("-" * 70)

# Get 2D coordinates using a cached projection when available.
if use_cached_projection:
    with open(cached_json_output) as infile:
        output_positions = json.load(infile)
else:
    output_positions = embedding_tools.get_2d_coordinates_tsne(
        multilayer_network,
        output_format="json"
    )

# Save coordinates to JSON file
with open(json_output, 'w') as outfile:
    json.dump(output_positions, outfile, indent=2)

print(f"  [OK] Coordinates exported to: {json_output}")

print("\n" + "=" * 70)
print("EMBEDDING CONSTRUCTION COMPLETE")
print("=" * 70)

print("\nGenerated files:")
print(f"  - Edgelist: {edgelist_file}")
print(f"  - Embeddings: {embedding_file}")
print(f"  - Coordinates (JSON): {json_output}")

print("\nNext steps:")
print("  - Use embeddings for node classification")
print("  - Use embeddings for link prediction")
print("  - Try different embedding parameters (p, q values)")
print("  - Compare with other embedding methods (DeepWalk, LINE)")
print("  - Use coordinates for custom visualizations")
