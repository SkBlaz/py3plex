# compute and visualize powerlaw distributions (and other alternatives)
# SKIP_CI: external_deps - Requires specific dataset files

import networkx as nx

try:
    import mpmath
    MPMATH_AVAILABLE = True
except ImportError:
    MPMATH_AVAILABLE = False
    print("Warning: mpmath not installed. Install with: pip install mpmath")
    print("This example requires mpmath for power law fitting.")
    exit(0)

from py3plex.algorithms.statistics.topology import plot_power_law
from py3plex.core import multinet
from py3plex.utils import get_dataset_path

# examples use the node degrees, note that any node property applies.

# on a simple network
G = nx.powerlaw_cluster_graph(1000, 3, 0.5, 1573)
val_vect = sorted(dict(nx.degree(G)).values(), reverse=True)
plot_power_law(val_vect, "", "Node degree", "individual node")

# on py3plex objects -- consider all edges and nodes
multilayer_network = multinet.multi_layer_network().load_network(
    get_dataset_path("epigenetics.gpickle"),
    directed=False,
    input_type="gpickle_biomine")
val_vect = sorted(dict(nx.degree(multilayer_network.core_network)).values(),
                  reverse=True)
plot_power_law(val_vect, "", "Node degree", "individual node")

print(multilayer_network.test_scale_free())
