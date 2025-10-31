"""Shared utilities for clustering and hierarchical operations."""

from typing import Any, Dict, List

import numpy as np
from scipy.cluster.hierarchy import linkage


def create_tree(centers: np.ndarray) -> Dict[int, Dict[str, List]]:
    """
    Create a hierarchical tree from cluster centers using single linkage.

    Args:
        centers: Array of cluster centers

    Returns:
        Dictionary mapping cluster IDs to their hierarchical structure
    """
    clusters: Dict[int, Any] = {}
    to_merge = linkage(centers, method="single")
    for i, merge in enumerate(to_merge):
        a: Any
        b: Any
        if merge[0] <= len(to_merge):
            # if it is an original point read it from the centers array
            a = centers[int(merge[0]) - 1]
        else:
            # other wise read the cluster that has been created
            a = clusters[int(merge[0])]

        if merge[1] <= len(to_merge):
            b = centers[int(merge[1]) - 1]
        else:
            b = clusters[int(merge[1])]
        # the clusters are 1-indexed by scipy
        clusters[1 + i + len(to_merge)] = {"children": [a, b]}
        # ^ you could optionally store other info here (e.g distances)
    return clusters
