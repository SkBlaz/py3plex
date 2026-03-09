"""Example: Visualizing Large Networks with Node2Vec Embeddings

This example demonstrates how to:
- Load a large network (IntAct protein-protein interactions)
- Generate node2vec embeddings for layout initialization
- Reduce embeddings to 2D using t-SNE
- Detect communities using Louvain algorithm
- Create hairball visualization with community colors
- Export high-resolution images (PNG and PDF)

The workflow combines:
1. **node2vec**: Generates structural embeddings via random walks
2. **t-SNE**: Projects embeddings to 2D for visualization
3. **Louvain**: Identifies network communities
4. **Hairball plot**: Visualizes network with custom layout

This approach is effective for large networks (>1000 nodes) where
force-directed layouts are too slow. The embedding-based layout
preserves network structure while being computationally tractable.

Note: Requires node2vec binary (not bundled) and IntAct dataset files.
For faster t-SNE, install Multicore-TSNE: 
pip install git+https://github.com/DmitryUlyanov/Multicore-TSNE
"""
# SKIP_CI: external_deps - Requires specific dataset files (intact02.gpickle)

from collections import Counter
import json
from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.visualization.embedding_visualization import embedding_tools
from py3plex.wrappers import train_node2vec_embedding
from py3plex.visualization.multilayer import hairball_plot, plt
from py3plex.visualization.colors import colors_default
from py3plex.core import multinet
from py3plex.exceptions import ExternalToolError, Py3plexIOError
from py3plex.utils import get_dataset_path


def _load_cached_positions(path: str):
    with open(path, "r") as infile:
        raw = json.load(infile)
    if isinstance(raw, dict):
        return raw
    return {
        tuple(entry["node_names"]): (entry["dim1"], entry["dim2"])
        for entry in raw
        if "node_names" in entry and "dim1" in entry and "dim2" in entry
    }

try:
    # string layout for larger network -----------------------------------
    multilayer_network = multinet.multi_layer_network().load_network(
        get_dataset_path("intact02.gpickle"), input_type="gpickle",
        directed=False).add_dummy_layers()
    multilayer_network.basic_stats()

    if multilayer_network.core_network.number_of_nodes() > 20000:
        print("Skipping the full IntAct rendering path on this very large graph.")
        raise SystemExit(0)

    try:
        train_node2vec_embedding.call_node2vec_binary(
            get_dataset_path("IntactEdgelistedges.txt"),
            get_dataset_path("test_embedding.emb"),
            binary="./node2vec",
            weighted=False,
        )
    except (ExternalToolError, FileNotFoundError, Py3plexIOError) as exc:
        print(f"Skipping Node2Vec regeneration: {exc}")
        print("Using the pre-computed embedding if available.")

    multilayer_network.load_embedding(get_dataset_path("test_embedding.emb"))
    try:
        output_positions = _load_cached_positions(
            get_dataset_path("embedding_coordinates.json")
        )
        print("Loaded cached 2D embedding coordinates.")
    except Py3plexIOError:
        output_positions = embedding_tools.get_2d_coordinates_tsne(
            multilayer_network, output_format="pos_dict")

    layout_parameters = {"iterations": 200}
    layout_parameters['pos'] = output_positions
    network_colors, graph = multilayer_network.get_layers(style="hairball")

    partition = cw.louvain_communities(multilayer_network)

    top_n = 10
    partition_counts = dict(Counter(partition.values()))
    top_n_communities = list(partition_counts.keys())[0:top_n]

    color_mappings = dict(
        zip(top_n_communities,
            [x for x in colors_default if x != "black"][0:top_n]))

    network_colors = [
        color_mappings[partition[x]]
        if partition[x] in top_n_communities else "black"
        for x in multilayer_network.get_nodes()
    ]

    f = plt.figure()
    hairball_plot(graph,
                  network_colors,
                  layout_algorithm="custom_coordinates",
                  layout_parameters=layout_parameters,
                  node_size=0.02,
                  alpha_channel=0.30,
                  edge_width=0.001,
                  scale_by_size=False)

    f.savefig(get_dataset_path("intact.png"), bbox_inches='tight', dpi=300)
    f.savefig(get_dataset_path("intact.pdf"), bbox_inches='tight')
except Py3plexIOError as exc:
    print(f"Skipping example because required IntAct data is unavailable: {exc}")
    raise SystemExit(0)
