## temporal multiplex analysis algorithms

import numpy as np
from tqdm import tqdm
from ...core import multinet


def split_to_temporal_slices(network, slices=100, verbose=True):

    _edge_slices = np.array_split(network.temporal_edges, slices)

    ts_net = {}
    all_edges = set(network.core_network.edges())

    if verbose:
        network.monitor("Slicing the network")

    for en, eslice in tqdm(enumerate(_edge_slices), total=slices):
        edges_to_keep = set([(x['node_first'], x['node_second'])
                             for x in eslice.to_dict('records')])
        edges_to_remove = all_edges - edges_to_keep
        edges_to_remove = [(a, b, "default") for a, b in edges_to_remove]
        G = network.core_network.copy()
        G.remove_edges_from(edges_to_remove)
        ts_net[en] = multinet.multi_layer_network(
            network_type="multiplex").load_network(G,
                                                   directed=True,
                                                   input_type="nx")

    return ts_net
