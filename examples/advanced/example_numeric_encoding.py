"""Example: Numeric Encoding (Supra-Adjacency Matrix)

This example demonstrates how to:
- Generate random Erdős-Rényi multilayer networks
- Extract the supra-adjacency matrix representation
- Load a multiplex network from edgelist format
- Convert network to numeric encoding (node-to-index mapping)
- Access the numeric adjacency matrix and node ordering

Numeric encoding is essential for:
- Matrix-based computations (spectral analysis, centrality)
- Machine learning algorithms requiring numeric input
- Efficient storage and manipulation of large networks

The supra-adjacency matrix represents the entire multilayer network
as a single block matrix where blocks correspond to layers.
"""
# SKIP_CI: external_deps - Requires specific dataset files

from py3plex.core import multinet
from py3plex.core import random_generators
from py3plex.utils import get_dataset_path

# initiate an instance of a random graph
ER_multilayer = random_generators.random_multilayer_ER(500,
                                                       8,
                                                       0.05,
                                                       directed=False)
mtx = ER_multilayer.get_supra_adjacency_matrix()

comNet = multinet.multi_layer_network(
    network_type="multiplex",
    coupling_weight=1).load_network(get_dataset_path('simple_multiplex.edgelist'),
                                    directed=False,
                                    input_type='multiplex_edges')
comNet.basic_stats()
comNet._encode_to_numeric()
vectors = comNet.numeric_core_network
node_list = comNet.node_order_in_matrix
print(vectors.shape)
