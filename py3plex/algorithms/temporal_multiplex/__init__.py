"""Temporal multiplex network analysis algorithms.

This module provides tools for analyzing temporal dynamics in multiplex networks,
including methods for slicing networks by time and studying temporal patterns.
"""

import numpy as np
from tqdm import tqdm

from py3plex.core import multinet


def split_to_temporal_slices(network, slices=100, verbose=True):
    """Split a temporal network into time slices for dynamic analysis.

    Divides a temporal network into sequential time windows, creating a snapshot
    network for each time slice. Useful for studying network evolution, temporal
    patterns, and dynamic community structure.

    Args:
        network: multi_layer_network object with temporal_edges attribute
                Must have been loaded with temporal edge information
        slices: Number of temporal slices to create (default: 100)
               Edges are split evenly across time slices
        verbose: Print progress information (default: True)

    Returns:
        dict: {slice_index: multi_layer_network}
            Dictionary mapping time slice index (0 to slices-1) to network snapshot
            Each snapshot contains only edges active in that time window

    Notes:
        - Requires network.temporal_edges to be populated (DataFrame with temporal info)
        - Edges are split evenly: slice_i contains edges[i*E/S : (i+1)*E/S]
          where E=total edges, S=number of slices
        - Each snapshot is a full multi_layer_network object
        - Nodes present in later slices but not in earlier ones are still included
        - Uses tqdm for progress bar if available

    Examples:
        >>> # Load temporal network
        >>> net = multi_layer_network()
        >>> net.load_network('temporal_edges.csv', input_type='temporal')
        >>>
        >>> # Split into 50 time windows
        >>> time_slices = split_to_temporal_slices(net, slices=50)
        >>>
        >>> # Analyze each time slice
        >>> for t, snapshot in time_slices.items():
        ...     print(f"Time {t}: {snapshot.core_network.number_of_edges()} edges")
        >>>
        >>> # Compare community structure over time
        >>> communities_over_time = {}
        >>> for t, snapshot in time_slices.items():
        ...     communities_over_time[t] = snapshot.get_communities()

    Performance:
        - Time complexity: O(S * E) where S=slices, E=edges
        - Memory: O(S * (N + E)) for storing all snapshots
        - For large networks (>1M edges), consider using fewer slices

    See Also:
        load_network: Load temporal edge data
        edges_from_temporal_table: Convert temporal DataFrame to edges

    Raises:
        AttributeError: If network.temporal_edges is None (not a temporal network)
    """

    _edge_slices = np.array_split(network.temporal_edges, slices)

    ts_net = {}
    all_edges = set(network.core_network.edges())

    if verbose:
        network.monitor("Slicing the network")

    for en, eslice in tqdm(enumerate(_edge_slices), total=slices):
        edges_to_keep = {
            (x["node_first"], x["node_second"]) for x in eslice.to_dict("records")
        }
        edges_to_remove = all_edges - edges_to_keep
        edges_to_remove = [(a, b, "default") for a, b in edges_to_remove]
        G = network.core_network.copy()
        G.remove_edges_from(edges_to_remove)
        ts_net[en] = multinet.multi_layer_network(
            network_type="multiplex"
        ).load_network(G, directed=True, input_type="nx")

    return ts_net
