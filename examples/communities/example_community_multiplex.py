# multiplex community detection!
# SKIP_CI: external_deps - Requires specific dataset files (multiplex_example.edgelist)

try:
    import louvain
    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False
    print("Warning: louvain not installed. Install with: pip install python-louvain")
    print("This example requires python-louvain for multiplex community detection.")
    exit(0)

try:
    import igraph as ig
    IGRAPH_AVAILABLE = True
except ImportError:
    IGRAPH_AVAILABLE = False
    print("Warning: igraph not installed. Install with: pip install python-igraph")
    print("This example requires igraph for multiplex community detection.")
    exit(0)

from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.core import multinet
from py3plex.utils import get_dataset_path

# Using network_type="multiplex" for networks where:
# - The same nodes (entities) appear across all layers
# - Different layers represent different relationship types
# - We want automatic coupling edges between node copies
# For heterogeneous networks with different node types per layer,
# use network_type="multilayer" instead
network = multinet.multi_layer_network(network_type="multiplex").load_network(
    input_file=get_dataset_path("multiplex_example.edgelist"),
    directed=True,
    input_type="multiplex_edges")

# Note: Infomap requires a binary that is no longer bundled with py3plex.
# Install from https://www.mapequation.org/infomap/ if needed
try:
    partition = cw.infomap_communities(network,
                                       binary="./infomap",  # Assumes infomap is in PATH
                                       multiplex=True,
                                       verbose=True)
    print(partition)
except FileNotFoundError as e:
    print(f"Skipping Infomap: {e}")
    print("Continuing with multiplex Louvain instead...")

# get communities with multiplex louvain

#optimiser = louvain.Optimiser()
network.split_to_layers(style="none")
network_list = []

# cast this to igraph
unique_node_id_counter = 0
node_hash = {}
for layer in network.separate_layers:
    g = ig.Graph()
    edges_all = []
    for edge in layer.edges():
        first_node = int(edge[0][0])
        second_node = int(edge[1][0])
        g.add_vertex(first_node)
        g.add_vertex(second_node)
        edges_all.append((first_node, second_node))
    print(edges_all)
    g.add_edges(edges_all)
    network_list.append(g)

membership, improv = louvain.find_partition_multiplex(
    network_list, louvain.ModularityVertexPartition)

# for each node we get community assignment.
network.monitor(membership)
network.monitor(improv)
