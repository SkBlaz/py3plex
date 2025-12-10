"""
Community detection algorithms for multilayer networks.

This module provides algorithms for detecting communities in multilayer networks,
including multilayer modularity optimization, benchmark generation, and various
community detection methods.
"""

from typing import Any, Dict, Tuple, Union
import numpy as np

# Multilayer community detection
from .multilayer_benchmark import (
    generate_coupled_er_multilayer,
    generate_multilayer_lfr,
    generate_sbm_multilayer,
)
from .multilayer_modularity import (
    build_supra_modularity_matrix,
    louvain_multilayer,
    multilayer_modularity,
)
from .leiden_multilayer import (
    leiden_multilayer,
    LeidenResult,
)


def multilayer_louvain(
    network: Any,
    gamma: Union[float, Dict[Any, float]] = 1.0,
    omega: Union[float, np.ndarray] = 1.0,
    weight: str = "weight",
    max_iter: int = 100,
    random_state: int = None,
) -> Tuple[Dict[Tuple[Any, Any], int], float]:
    """
    Run multilayer Louvain community detection.

    This is a convenience wrapper around louvain_multilayer that returns
    both the partition and the modularity score, making it easier to use
    in typical workflows.

    Parameters
    ----------
    network : multi_layer_network
        The multilayer network to partition.
    gamma : float or dict, default=1.0
        Resolution parameter(s).
    omega : float or ndarray, default=1.0
        Inter-layer coupling strength.
    weight : str, default="weight"
        Edge weight attribute.
    max_iter : int, default=100
        Maximum number of iterations.
    random_state : int, optional
        Random seed for reproducibility.

    Returns
    -------
    tuple
        A tuple (partition, modularity) where:
        - partition: Dict mapping (node, layer) to community ID
        - modularity: float, the multilayer modularity score

    Examples
    --------
    >>> from py3plex.core import multinet
    >>> from py3plex.algorithms.community_detection import multilayer_louvain
    >>>
    >>> network = multinet.multi_layer_network(directed=False)
    >>> network.add_edges([
    ...     ['A', 'L1', 'B', 'L1', 1],
    ...     ['B', 'L1', 'C', 'L1', 1],
    ... ], input_type='list')
    >>>
    >>> partition, Q = multilayer_louvain(network, gamma=1.2)
    >>> print(f"Modularity: {Q:.3f}")
    >>> print(f"Communities: {len(set(partition.values()))}")
    """
    # Run the core Louvain algorithm
    partition = louvain_multilayer(
        network=network,
        gamma=gamma,
        omega=omega,
        weight=weight,
        max_iter=max_iter,
        random_state=random_state,
    )

    # Calculate the modularity
    Q = multilayer_modularity(
        network=network,
        communities=partition,
        gamma=gamma,
        omega=omega,
        weight=weight,
    )

    return partition, Q


__all__ = [
    "multilayer_modularity",
    "build_supra_modularity_matrix",
    "louvain_multilayer",
    "multilayer_louvain",
    "leiden_multilayer",
    "LeidenResult",
    "generate_multilayer_lfr",
    "generate_coupled_er_multilayer",
    "generate_sbm_multilayer",
]
