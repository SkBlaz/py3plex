"""Feature extraction for multilayer network alignment.

This module provides functions to compute per-node feature vectors from
multilayer networks for use in network alignment.
"""

from typing import Dict, Hashable, Iterable, List, Optional

import numpy as np

from py3plex.core import multinet


def multilayer_node_features(
    network: "multinet.multi_layer_network",
    layers: Optional[Iterable[str]] = None,
    include_total_degree: bool = True,
    include_per_layer_degree: bool = True,
    include_layer_entropy: bool = True,
) -> Dict[Hashable, np.ndarray]:
    """
    Compute a feature vector for each node in a multilayer network.

    Features (MVP scheme)
    ---------------------
    Let there be L layers (either provided via `layers` or obtained from the network).
    For each node u:

    1. total_degree:
       Sum of degrees over all layers (if include_total_degree).

    2. per_layer_degree:
       Degree of u restricted to each layer (if include_per_layer_degree).
       This yields a vector of length L.

    3. layer_participation_entropy:
       Entropy of the distribution of u's degree over layers (if include_layer_entropy):
           p_l = degree_l(u) / total_degree(u)   (for layers where total_degree > 0)
           H(u) = - sum_l p_l * log(p_l)
       If total_degree(u) == 0, define entropy = 0.

    The final feature vector is the concatenation of all selected parts in this order:
        [total_degree] + [deg_layer_0, deg_layer_1, ..., deg_layer_{L-1}] + [entropy]

    Layer ordering:
        - If `layers` is None, get all layers from the network and sort them by name.
        - If `layers` is provided, convert to list and use that order.

    Parameters
    ----------
    network : multinet.multi_layer_network
        The multilayer network to extract features from.
    layers : Optional[Iterable[str]]
        The list of layer names to consider. If None, uses all layers from the network
        sorted alphabetically.
    include_total_degree : bool
        Whether to include total degree in the feature vector. Default: True.
    include_per_layer_degree : bool
        Whether to include per-layer degree in the feature vector. Default: True.
    include_layer_entropy : bool
        Whether to include layer participation entropy in the feature vector. Default: True.

    Returns
    -------
    features : Dict[Hashable, np.ndarray]
        Dictionary mapping node IDs to 1D numpy arrays of equal length.

    Examples
    --------
    >>> from py3plex.core import multinet
    >>> net = multinet.multi_layer_network(directed=False)
    >>> net.add_edges([
    ...     {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
    ...     {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
    ... ])
    <multi_layer_network: type=multilayer, directed=False, nodes=3, edges=2, layers=1>
    >>> feats = multilayer_node_features(net)
    >>> len(feats)
    3
    >>> all(isinstance(v, np.ndarray) for v in feats.values())
    True
    """
    # py3plex.core.multinet.multi_layer_network may keep `core_network=None` until the
    # first nodes/edges are added. Treat this as an empty network.
    if getattr(network, "core_network", None) is None:
        return {}

    # Get layers
    if layers is None:
        layer_list = sorted(network.layers)
    else:
        layer_list = list(layers)

    num_layers = len(layer_list)
    layer_idx = {layer: i for i, layer in enumerate(layer_list)}

    # Initialize degree per layer for each node
    # Nodes in multilayer networks are (node_id, layer) tuples
    # We want to group by node_id and compute degrees per layer
    node_ids = set()
    for node in network.get_nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            node_ids.add(node[0])
        else:
            node_ids.add(node)

    # Initialize degree arrays
    node_degrees: Dict[Hashable, np.ndarray] = {
        node_id: np.zeros(num_layers, dtype=np.float64) for node_id in node_ids
    }

    # Count degrees per layer
    for edge in network.get_edges():
        source_node, target_node = edge[0], edge[1]

        # Extract node_id and layer from tuples
        if isinstance(source_node, tuple) and len(source_node) >= 2:
            src_id, src_layer = source_node[0], source_node[1]
        else:
            src_id, src_layer = source_node, layer_list[0] if layer_list else "default"

        if isinstance(target_node, tuple) and len(target_node) >= 2:
            tgt_id, tgt_layer = target_node[0], target_node[1]
        else:
            tgt_id, tgt_layer = target_node, layer_list[0] if layer_list else "default"

        # Increment degrees for edges within the specified layers
        if src_layer in layer_idx:
            node_degrees[src_id][layer_idx[src_layer]] += 1
        if tgt_layer in layer_idx:
            node_degrees[tgt_id][layer_idx[tgt_layer]] += 1

    # Build feature vectors
    features: Dict[Hashable, np.ndarray] = {}

    for node_id, layer_degrees in node_degrees.items():
        feature_parts: List[np.ndarray] = []

        total_degree = layer_degrees.sum()

        if include_total_degree:
            feature_parts.append(np.array([total_degree]))

        if include_per_layer_degree:
            feature_parts.append(layer_degrees)

        if include_layer_entropy:
            if total_degree > 0:
                # Compute entropy of degree distribution over layers
                p = layer_degrees / total_degree
                # Avoid log(0) by filtering out zero probabilities
                nonzero_mask = p > 0
                entropy = -np.sum(p[nonzero_mask] * np.log(p[nonzero_mask]))
            else:
                entropy = 0.0
            feature_parts.append(np.array([entropy]))

        if feature_parts:
            features[node_id] = np.concatenate(feature_parts)
        else:
            # If no features are selected, return empty array
            features[node_id] = np.array([])

    return features
