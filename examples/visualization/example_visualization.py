"""
Advanced Network Visualization with Embeddings and Communities

Teaches:
- Use Node2Vec embeddings to initialize node positions
- Detect communities and color nodes accordingly
- Create hairball plots for large networks
- Combine embedding-based layouts with force-directed refinement

Prerequisites:
- Dataset: intact02.gpickle (protein interaction network)
- Dataset: IntactEdgelistedges.txt (edgelist format)
- Dataset: test_embedding.emb (pre-computed Node2Vec embeddings)
- Node2Vec binary (optional): https://github.com/snap-stanford/snap

SKIP_CI: external_deps - Requires specific dataset files (intact02.gpickle, test_embedding.emb)
"""

from py3plex.visualization.multilayer import hairball_plot, plt
from py3plex.visualization.colors import colors_default
from py3plex.core import multinet
from py3plex.wrappers import train_node2vec_embedding
from py3plex.visualization.embedding_visualization import embedding_tools
from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.utils import get_dataset_path, get_example_image_path
from collections import Counter


def plot_intact_embedding(num_it):
    """
    Visualize a large protein interaction network using embedding-based layout.
    
    Args:
        num_it (int): Number of force-directed layout iterations for refinement
    """
    print("=" * 70)
    print("ADVANCED NETWORK VISUALIZATION")
    print("=" * 70)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 1: Load protein interaction network
    # ═══════════════════════════════════════════════════════════════════════════════
    
    print("\n[1] Loading protein interaction network...")
    print("-" * 70)
    multilayer_network = multinet.multi_layer_network().load_network(
        get_dataset_path("intact02.gpickle"), input_type="gpickle",
        directed=False).add_dummy_layers()
    multilayer_network.basic_stats()
    print(f"Network loaded with {len(list(multilayer_network.get_nodes()))} nodes")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 2: Generate/load Node2Vec embeddings
    # ═══════════════════════════════════════════════════════════════════════════════
    
    print("\n[2] Generating Node2Vec embeddings...")
    print("-" * 70)
    print("Note: This requires Node2Vec binary (or pre-computed embeddings)")
    
    try:
        # Call Node2Vec binary to generate embeddings
        train_node2vec_embedding.call_node2vec_binary(
            get_dataset_path("IntactEdgelistedges.txt"),
            get_dataset_path("test_embedding.emb"),
            binary="./node2vec",  # Note: binary no longer bundled
            weighted=False)
        print("Embeddings generated successfully!")
    except FileNotFoundError:
        print("Node2Vec binary not found, attempting to load pre-computed embeddings...")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 3: Load embeddings and project to 2D using t-SNE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    print("\n[3] Loading embeddings and projecting to 2D...")
    print("-" * 70)
    print("Tip: For faster t-SNE, install: pip install MulticoreTSNE")
    
    multilayer_network.load_embedding(get_dataset_path("test_embedding.emb"))

    # Load the positions and select the projection algorithm (t-SNE)
    output_positions = embedding_tools.get_2d_coordinates_tsne(
        multilayer_network, output_format="pos_dict")
    print("2D projection complete!")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 4: Detect communities for coloring
    # ═══════════════════════════════════════════════════════════════════════════════
    
    print("\n[4] Detecting communities...")
    print("-" * 70)
    
    # Custom layouts use embedding positions with force-directed refinement
    layout_parameters = {"iterations": num_it}
    layout_parameters['pos'] = output_positions  # Assign embedding positions
    network_colors, graph = multilayer_network.get_layers(style="hairball")
    partition = cw.louvain_communities(multilayer_network)
    print(f"Found {len(set(partition.values()))} communities")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 5: Assign colors to top communities
    # ═══════════════════════════════════════════════════════════════════════════════
    
    print("\n[5] Assigning colors to top communities...")
    print("-" * 70)

    # Select top n communities by size
    top_n = 10
    partition_counts = dict(Counter(partition.values()))
    top_n_communities = list(partition_counts.keys())[0:top_n]
    print(f"Coloring top {top_n} communities (others will be black)")

    # Assign node colors based on community membership
    color_mappings = dict(
        zip(top_n_communities,
            [x for x in colors_default if x != "black"][0:top_n]))

    network_colors = [
        color_mappings[partition[x]]
        if partition[x] in top_n_communities else "black"
        for x in multilayer_network.get_nodes()
    ]
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 6: Create hairball plot with custom layout
    # ═══════════════════════════════════════════════════════════════════════════════
    
    print("\n[6] Generating hairball plot...")
    print("-" * 70)
    print(f"Using embedding-based layout with {num_it} force-directed iterations")

    f = plt.figure()
    # Parameters: gravity=0.2, strongGravityMode=False, barnesHutTheta=1.2,
    # edgeWeightInfluence=1, scalingRatio=2.0
    hairball_plot(graph,
                  network_colors,
                  layout_algorithm="custom_coordinates_initial_force",
                  layout_parameters=layout_parameters,
                  nodesize=0.02,
                  alpha_channel=0.30,
                  edge_width=0.001,
                  scale_by_size=False)

    output_path = get_dataset_path(str(num_it) + "intact.png")
    f.savefig(output_path, bbox_inches='tight', dpi=300)
    print(f"Plot saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("VISUALIZATION COMPLETE")
    print("=" * 70)
    print("\nKey takeaways:")
    print("  [OK] Embedding-based layouts provide good initial positions")
    print("  [OK] Force-directed refinement improves visual quality")
    print("  [OK] Community coloring reveals network structure")
    print("  [OK] Hairball plots work well for large, complex networks")


def plot_intact_basic(num_it=10):
    """
    Create a basic visualization of the protein interaction network.
    
    Uses pure force-directed layout without embeddings for simplicity.
    
    Args:
        num_it (int): Number of force-directed layout iterations
    """
    print("\n" + "=" * 70)
    print("BASIC NETWORK VISUALIZATION (no embeddings)")
    print("=" * 70)

    print("Plotting intact")
    multilayer_network = multinet.multi_layer_network().load_network(
        get_dataset_path("intact02.gpickle"), input_type="gpickle",
        directed=False).add_dummy_layers()
    network_colors, graph = multilayer_network.get_layers(style="hairball")
    partition = cw.louvain_communities(multilayer_network)

    # select top n communities by size
    top_n = 3
    partition_counts = dict(Counter(partition.values()))
    top_n_communities = list(partition_counts.keys())[0:top_n]

    # assign node colors
    color_mappings = dict(
        zip(top_n_communities,
            [x for x in colors_default if x != "black"][0:top_n]))

    network_colors = [
        color_mappings[partition[x]]
        if partition[x] in top_n_communities else "black"
        for x in multilayer_network.get_nodes()
    ]

    layout_parameters = {"iterations": num_it, "forceImport": True}
    f = plt.figure()
    hairball_plot(graph,
                  network_colors,
                  legend=False,
                  layout_parameters=layout_parameters)
    f.savefig(get_example_image_path("intact_" + str(num_it) + "_BH_basic.png"),
              bbox_inches='tight',
              dpi=300)


def plot_intact_BH(num_it=10):

    print("Plotting intact")
    multilayer_network = multinet.multi_layer_network().load_network(
        get_dataset_path("intact02.gpickle"), input_type="gpickle",
        directed=False).add_dummy_layers()
    network_colors, graph = multilayer_network.get_layers(style="hairball")
    partition = cw.louvain_communities(multilayer_network)

    # select top n communities by size
    top_n = 3
    partition_counts = dict(Counter(partition.values()))
    top_n_communities = list(partition_counts.keys())[0:top_n]

    # assign node colors
    color_mappings = dict(
        zip(top_n_communities,
            [x for x in colors_default if x != "black"][0:top_n]))

    network_colors = [
        color_mappings[partition[x]]
        if partition[x] in top_n_communities else "black"
        for x in multilayer_network.get_nodes()
    ]

    layout_parameters = {"iterations": num_it}
    f = plt.figure()
    hairball_plot(graph,
                  network_colors,
                  legend=False,
                  layout_parameters=layout_parameters)
    f.savefig(get_example_image_path("intact_" + str(num_it) + "_BH.png"),
              bbox_inches='tight',
              dpi=300)


if __name__ == "__main__":
    import time
    import numpy as np
    iteration_range = [0, 10, 100]
    for iterations in iteration_range:
        mean_times = []
        for j in range(2):
            start = time.time()
            # plot_intact_BH(iterations)
            plot_intact_embedding(iterations)
            end = (time.time() - start) / 60
            mean_times.append(end)
        print(f"Mean time for BK {np.mean(mean_times)}, iterations: {iterations}")

    # mean_times = []
    # for j in range(iterations):
    #     start = time.time()
    #     plot_intact_embedding()
    #     end = (time.time() - start)/60
    #     mean_times.append(end)
    # print("Mean time for Py3 {}".format(np.mean(mean_times)))
