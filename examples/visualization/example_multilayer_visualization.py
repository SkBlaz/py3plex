"""
Visualization Example: Comprehensive Multilayer Network Visualization

This example demonstrates various visualization techniques for multilayer networks:
1. Basic multilayer network visualization (diagonal layout)
2. Hairball plots for dense networks
3. Community-colored visualizations
4. Custom multi-edge drawing with different styles
5. Layer-specific visualizations

Visualization styles:
- "diagonal": Multilayer diagonal layout (layers as parallel planes)
- "hairball": Force-directed single-layer projection
- "default": Standard NetworkX layout
- Custom: Fine-grained control over node and edge appearance

This example showcases the full flexibility of py3plex visualization,
from simple one-liners to complex custom multi-edge styling.
"""

import os
import random
import numpy as np
from collections import Counter

from py3plex.core import multinet
from py3plex.visualization.multilayer import (
    draw_multiedges,
    draw_multilayer_default,
    hairball_plot,
    plt
)
from py3plex.visualization.colors import colors_default
from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.utils import get_dataset_path

# Set random seeds for reproducible visualizations
random.seed(42)
np.random.seed(42)

print("=" * 70)
print("MULTILAYER NETWORK VISUALIZATION SHOWCASE")
print("=" * 70)

print("""
This example demonstrates multiple visualization approaches:
1. Simple multiedgelist visualization
2. Hairball plots for overview
3. Diagonal multilayer layout
4. Custom multi-edge styling
5. Biological network visualization

Each section can be run independently by loading the required datasets.
""")

##############################################################################
# EXAMPLE 1: Simple Multiedgelist Visualization
##############################################################################

print("\n" + "=" * 70)
print("EXAMPLE 1: Basic Multiedgelist Visualization")
print("=" * 70)

dataset1 = get_dataset_path("multinet_k100.txt")
if os.path.exists(dataset1):
    print(f"\nLoading: {dataset1}")
    
    multilayer_network = multinet.multi_layer_network().load_network(
        dataset1,
        directed=False,
        input_type="multiedgelist"
    )
    
    print("Network statistics:")
    multilayer_network.basic_stats()
    
    print("\nGenerating visualization (default style)...")
    print("(Close window to continue)")
    multilayer_network.visualize_network()
    plt.show()
else:
    print(f"\n✗ Dataset not found: {dataset1}")
    print("  Skipping Example 1")

##############################################################################
# EXAMPLE 2: Alternative Dataset Visualization
##############################################################################

print("\n" + "=" * 70)
print("EXAMPLE 2: Alternative Dataset")
print("=" * 70)

dataset2 = get_dataset_path("edgeList.txt")
if os.path.exists(dataset2):
    print(f"\nLoading: {dataset2}")
    
    multilayer_network = multinet.multi_layer_network().load_network(
        dataset2,
        directed=False,
        input_type="multiedgelist"
    )
    
    print("Network statistics:")
    multilayer_network.basic_stats()
    
    print("\nGenerating visualization...")
    print("(Close window to continue)")
    multilayer_network.visualize_network()
    plt.show()
else:
    print(f"\n✗ Dataset not found: {dataset2}")
    print("  Skipping Example 2")

##############################################################################
# EXAMPLE 3: IMDB Network - Diagonal and Hairball Plots
##############################################################################

print("\n" + "=" * 70)
print("EXAMPLE 3: IMDB Network Visualization")
print("=" * 70)

dataset3 = get_dataset_path("imdb.gpickle")
if os.path.exists(dataset3):
    print(f"\nLoading: {dataset3}")
    
    # Load heterogeneous information network
    multilayer_network = multinet.multi_layer_network().load_network(
        input_file=dataset3,
        directed=True,
        input_type=dataset3.split(".")[-1]
    )
    
    print("Network statistics:")
    multilayer_network.basic_stats()
    
    print("\n3a. Diagonal multilayer layout (100 iterations)...")
    print("    This shows layers as parallel planes")
    print("    (Close window to continue)")
    multilayer_network.visualize_network(style="diagonal")
    plt.show()
    
    print("\n3b. Hairball plot (5 iterations)...")
    print("    This projects all layers into a single view")
    print("    (Close window to continue)")
    hairball_plot(
        multilayer_network.core_network,
        layout_parameters={"iterations": 5},
        scale_by_size=True,
        legend=True,
        layout_algorithm="force"
    )
    plt.show()
else:
    print(f"\n✗ Dataset not found: {dataset3}")
    print("  Skipping Example 3")

##############################################################################
# EXAMPLE 4: Biological Network - Hairball Visualization
##############################################################################

print("\n" + "=" * 70)
print("EXAMPLE 4: Biological Network (miRNA)")
print("=" * 70)

dataset4 = get_dataset_path("goslim_mirna.gpickle")
if os.path.exists(dataset4):
    print(f"\nLoading: {dataset4}")
    
    multilayer_network = multinet.multi_layer_network().load_network(
        dataset4,
        directed=False,
        input_type="gpickle_biomine"
    )
    
    print("Network statistics:")
    multilayer_network.basic_stats()
    
    print("\nGenerating hairball visualization...")
    print("(Close window to continue)")
    multilayer_network.visualize_network(style="hairball")
    plt.show()
else:
    print(f"\n✗ Dataset not found: {dataset4}")
    print("  Skipping Example 4")

##############################################################################
# EXAMPLE 5: Diagonal Layout for Directed Network
##############################################################################

print("\n" + "=" * 70)
print("EXAMPLE 5: Directed Network Diagonal Layout")
print("=" * 70)

dataset5 = get_dataset_path("multiL.txt")
if os.path.exists(dataset5):
    print(f"\nLoading: {dataset5}")
    
    multilayer_network = multinet.multi_layer_network().load_network(
        dataset5,
        directed=True,
        input_type="multiedgelist"
    )
    
    print("Network statistics:")
    multilayer_network.basic_stats()
    
    print("\nGenerating diagonal layout...")
    print("(Close window to continue)")
    multilayer_network.visualize_network(style="diagonal")
    plt.show()
else:
    print(f"\n✗ Dataset not found: {dataset5}")
    print("  Skipping Example 5")

##############################################################################
# EXAMPLE 6: Custom Multi-Edge Styling (Advanced)
##############################################################################

print("\n" + "=" * 70)
print("EXAMPLE 6: Custom Multi-Edge Styling (Advanced)")
print("=" * 70)

dataset6 = get_dataset_path("epigenetics.gpickle")
if os.path.exists(dataset6):
    print(f"\nLoading: {dataset6}")
    
    multilayer_network = multinet.multi_layer_network().load_network(
        dataset6,
        directed=True,
        input_type="gpickle_biomine"
    )
    
    print("Network statistics:")
    multilayer_network.basic_stats()
    
    print("\nCreating custom visualization with styled multi-edges...")
    print("This demonstrates fine-grained control over edge appearance")
    
    # Get layers for custom visualization
    network_labels, graphs, multilinks = multilayer_network.get_layers()
    
    # Draw base multilayer network
    draw_multilayer_default(
        graphs,
        display=False,
        background_shape="circle",
        labels=network_labels
    )
    
    # Style different edge types with different visual properties
    color_mappings = dict(enumerate(colors_default))
    
    print(f"\nFound {len(multilinks)} edge types:")
    for edge_type in multilinks.keys():
        print(f"  - {edge_type}")
    
    print("\nApplying custom styling to each edge type...")
    
    for edge_type, edges in multilinks.items():
        # Customize appearance based on edge type
        if edge_type == "refers_to":
            draw_multiedges(
                graphs,
                edges,
                alphachannel=0.05,
                linepoints="--",
                linecolor="lightblue",
                curve_height=5,
                linmod="upper",
                linewidth=0.4
            )
            print(f"  ✓ Styled '{edge_type}' edges (lightblue, dashed)")
            
        elif edge_type == "belongs_to":
            draw_multiedges(
                graphs,
                edges,
                alphachannel=0.2,
                linepoints=":",
                linecolor="red",
                curve_height=5,
                linmod="upper",
                linewidth=0.4
            )
            print(f"  ✓ Styled '{edge_type}' edges (red, dotted)")
            
        elif edge_type == "codes_for":
            draw_multiedges(
                graphs,
                edges,
                alphachannel=0.2,
                linepoints=":",
                linecolor="orange",
                curve_height=5,
                linmod="upper",
                linewidth=0.4
            )
            print(f"  ✓ Styled '{edge_type}' edges (orange, dotted)")
            
        else:
            # Default style for other edge types
            draw_multiedges(
                graphs,
                edges,
                alphachannel=0.2,
                linepoints="-.",
                linecolor="black",
                curve_height=5,
                linmod="both",
                linewidth=0.4
            )
            print(f"  ✓ Styled '{edge_type}' edges (default: black, dash-dot)")
    
    print("\n(Close window to exit)")
    plt.show()
    plt.clf()
    
else:
    print(f"\n✗ Dataset not found: {dataset6}")
    print("  Skipping Example 6")

print("\n" + "=" * 70)
print("VISUALIZATION SHOWCASE COMPLETE")
print("=" * 70)

print("""
Visualization Summary:

1. Simple Visualization:
   - network.visualize_network()
   - Quick, automatic layout selection
   
2. Hairball Plots:
   - hairball_plot()
   - Good for dense networks
   - Shows overall structure
   
3. Diagonal Layout:
   - style="diagonal"
   - Best for multilayer visualization
   - Shows inter-layer connections
   
4. Custom Styling:
   - draw_multilayer_default() + draw_multiedges()
   - Full control over appearance
   - Good for publication-quality figures
   
Tips:
- Start with simple visualizations for exploration
- Use hairball for overview of large networks
- Use diagonal for multilayer-specific insights
- Use custom styling for publication figures
- Adjust iterations parameter for layout quality vs speed

For more information, see the py3plex documentation on:
  - Visualization styles
  - Layout algorithms
  - Color schemes
  - Custom plotting
""")

# monotone coloring
draw_multilayer_default(graphs,
                        display=False,
                        background_shape="rectangle",
                        labels=network_labels,
                        networks_color="black",
                        rectanglex=2,
                        rectangley=2,
                        background_color="default")

enum = 1
for edge_type, edges in multilinks.items():
    draw_multiedges(graphs,
                    edges,
                    alphachannel=0.2,
                    linepoints="--",
                    linecolor="black",
                    curve_height=2,
                    linmod="upper",
                    linewidth=0.4)
    enum += 1
plt.show()

# basic string layout ----------------------------------
multilayer_network = multinet.multi_layer_network().load_network(
    get_dataset_path("epigenetics.gpickle"),
    directed=False,
    label_delimiter="---",
    input_type="gpickle_biomine")
network_colors, graph = multilayer_network.get_layers(style="hairball")

parser = argparse.ArgumentParser()
parser.add_argument("--input_network", default=get_dataset_path("cora.mat"))
parser.add_argument("--input_type", default="sparse_network")
args = parser.parse_args()

network = multinet.multi_layer_network().load_network(
    input_file=args.input_network, directed=False, input_type=args.input_type
)  # network and group objects must be present within the .mat object

network.basic_stats()  # check core imports

partition = cw.louvain_communities(network.core_network)

# select top n communities by size
top_n = 10
partition_counts = dict(Counter(partition.values()))
top_n_communities = list(partition_counts.keys())[0:top_n]

# assign node colors
color_mappings = dict(zip(top_n_communities, colors_default[0:top_n]))

network_colors = [
    "green"
    if partition[x] in top_n_communities else "black"
    for x in network.get_nodes()
]

# visualize the network's communities!
hairball_plot(network.core_network,
              color_list=network_colors,
              layout_parameters={"iterations": 50},
              scale_by_size=True,
              layout_algorithm="force",
              legend=False)
plt.show()

# string layout for larger network -----------------------------------
multilayer_network = multinet.multi_layer_network().load_network(
    get_dataset_path("soc-Epinions1.edgelist"),
    label_delimiter="---",
    input_type="edgelist",
    directed=True)
hairball_plot(multilayer_network.core_network,
              layout_parameters={"iterations": 300})
plt.show()

# embedding-based layout (custom coordinates) -----------------------------------

multilayer_network = multinet.multi_layer_network().load_network(
    get_dataset_path("goslim_mirna.gpickle"),
    directed=False,
    input_type="gpickle_biomine")

multilayer_network.save_network(get_dataset_path("test.edgelist"))

# call a specific n2v compiled binary
train_node2vec_embedding.call_node2vec_binary(get_dataset_path("test.edgelist"),
                                              get_dataset_path("test_embedding.emb"),
                                              binary="./node2vec",  # Note: binary no longer bundled
                                              weighted=False)

# preprocess and check embedding
multilayer_network.load_embedding(get_dataset_path("test_embedding.emb"))
output_positions = embedding_tools.get_2d_coordinates_tsne(
    multilayer_network, output_format="pos_dict")

# custom layouts are part of the custom coordinate option
layout_parameters = {}
layout_parameters['pos'] = output_positions  # assign parameters
network_colors, graph = multilayer_network.get_layers(style="hairball")
hairball_plot(graph,
              network_colors,
              layout_algorithm="custom_coordinates",
              layout_parameters=layout_parameters)
plt.show()
