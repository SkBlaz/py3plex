"""
Network Embedding with Node2Vec

Teaches:
- Generate node embeddings using Node2Vec algorithm
- Visualize embeddings using t-SNE dimensionality reduction
- Export embedding coordinates to JSON format
- Use external embedding tools with py3plex networks

Background:
Node2Vec learns low-dimensional representations of nodes by simulating
random walks on the network. These embeddings can be used for downstream
tasks like classification, clustering, and visualization.

Prerequisites:
- Dataset: imdb_gml.gml (IMDB collaboration network)
- Node2Vec binary (not bundled): https://github.com/snap-stanford/snap
- Alternative: pip install node2vec (pure Python implementation)

SKIP_CI: external_deps - Requires node2vec binary
"""

from py3plex.core import multinet
from py3plex.wrappers import train_node2vec_embedding
from py3plex.visualization.embedding_visualization import embedding_visualization, embedding_tools
import json
import os
from py3plex.utils import get_dataset_path, get_data_path

print("=" * 70)
print("NETWORK EMBEDDING WITH NODE2VEC")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════════
# Step 1: Load network and prepare for embedding
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[1] Loading IMDB collaboration network...")
print("-" * 70)
multilayer_network = multinet.multi_layer_network().load_network(
    get_dataset_path("imdb_gml.gml"), directed=True, input_type="gml")
print("Network loaded successfully!")

# Get the datasets directory for output files
datasets_dir = get_data_path("datasets")

# ═══════════════════════════════════════════════════════════════════════════════
# Step 2: Export network to edgelist format for Node2Vec
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[2] Exporting network to edgelist format...")
print("-" * 70)
edgelist_path = os.path.join(datasets_dir, "test.edgelist")
multilayer_network.save_network(edgelist_path)
print(f"Edgelist saved to: {edgelist_path}")

# ═══════════════════════════════════════════════════════════════════════════════
# Step 3: Run Node2Vec embedding (requires binary or pure Python alternative)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[3] Running Node2Vec embedding...")
print("-" * 70)
print("Note: Node2Vec binary is no longer bundled with py3plex.")
print("Install options:")
print("  1. SNAP Node2Vec: https://github.com/snap-stanford/snap")
print("  2. Pure Python: pip install node2vec")
print("  3. Fast Python: pip install pecanpy")
print()
try:
    # Define embedding output path
    embedding_path = os.path.join(datasets_dir, "test_embedding.emb")

    # Call Node2Vec binary (assumes binary is in PATH or current directory)
    print(f"Calling Node2Vec binary...")
    train_node2vec_embedding.call_node2vec_binary(edgelist_path,
                                                  embedding_path,
                                                  binary="./node2vec",  # Assumes in PATH
                                                  weighted=False)
    print(f"Embedding saved to: {embedding_path}")

    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 4: Load and visualize embedding
    # ═══════════════════════════════════════════════════════════════════════════════

    print("\n[4] Loading and visualizing embedding...")
    print("-" * 70)
    
    # Preprocess and check embedding
    multilayer_network.load_embedding(embedding_path)
    print("Embedding loaded successfully!")

    # Visualize embedding using t-SNE
    print("Generating visualization (using t-SNE)...")
    embedding_visualization.visualize_embedding(multilayer_network)
    print("Visualization complete!")

    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 5: Export embedding coordinates to JSON
    # ═══════════════════════════════════════════════════════════════════════════════

    print("\n[5] Exporting 2D coordinates to JSON...")
    print("-" * 70)
    
    # Output embedded coordinates as JSON
    output_json = embedding_tools.get_2d_coordinates_tsne(multilayer_network,
                                                          output_format="json")

    json_output_path = os.path.join(datasets_dir, 'embedding_coordinates.json')
    with open(json_output_path, 'w') as outfile:
        json.dump(output_json, outfile)
    print(f"Coordinates saved to: {json_output_path}")
    
    print("\n" + "=" * 70)
    print("NODE2VEC EMBEDDING COMPLETE")
    print("=" * 70)
    print("\nKey takeaways:")
    print("  [OK] Node2Vec learns low-dimensional node representations")
    print("  [OK] Embeddings preserve network structural properties")
    print("  [OK] t-SNE reduces embeddings to 2D for visualization")
    print("  [OK] Embeddings can be exported for downstream tasks")
    
except FileNotFoundError as e:
    print(f"[ERROR] Node2Vec binary not found: {e}")
    print("\nAlternative approaches:")
    print("  1. Install pure Python Node2Vec:")
    print("     pip install node2vec")
    print("\n  2. Install fast Python alternative:")
    print("     pip install pecanpy")
    print("\n  3. Use py3plex built-in embedding methods")
    print("\nFor this example to work, you need the Node2Vec binary")
    print("or modify the code to use one of the Python alternatives.")

