"""
Dataset loaders for py3plex built-in datasets.

This module provides functions to load bundled datasets that come
with py3plex, similar to scikit-learn's dataset loading functions.
"""

import os
from typing import List, Tuple

from py3plex.core.multinet import multi_layer_network


def get_data_dir() -> str:
    """
    Get the path to the bundled data directory.

    Returns
    -------
    str
        Absolute path to the py3plex/datasets/_data directory.

    Examples
    --------
    >>> from py3plex.datasets import get_data_dir
    >>> data_dir = get_data_dir()
    >>> print(data_dir)  # /path/to/py3plex/datasets/_data
    """
    return os.path.join(os.path.dirname(__file__), "_data")


def list_datasets() -> List[Tuple[str, str]]:
    """
    List all available built-in datasets.

    Returns
    -------
    list of tuple
        List of (name, description) tuples for each available dataset.

    Examples
    --------
    >>> from py3plex.datasets import list_datasets
    >>> for name, desc in list_datasets():
    ...     print(f"{name}: {desc}")
    aarhus_cs: Social network of Aarhus CS department (61 nodes, 5 layers)
    synthetic_multilayer: Synthetic multilayer network (50 nodes, 3 layers)
    """
    datasets = [
        ("aarhus_cs", "Social network of Aarhus CS department (61 nodes, 5 layers)"),
        ("synthetic_multilayer", "Synthetic multilayer network (50 nodes, 3 layers)"),
    ]
    return datasets


def load_aarhus_cs(directed: bool = False) -> multi_layer_network:
    """
    Load the Aarhus CS department social network.

    This is a well-known multiplex social network representing relationships
    among employees of the Computer Science department at Aarhus University.

    Dataset details: 61 employees, 5 layers (lunch, facebook, coauthor,
    leisure, work), approximately 600 relationships across layers,
    undirected multiplex network.

    The layers represent different types of social interactions:
    lunch (who has lunch together), facebook (Facebook friendships),
    coauthor (co-authorship relations), leisure (leisure activities together),
    and work (work-related interactions).

    Parameters
    ----------
    directed : bool, default=False
        If True, load as directed network (though the original data
        represents undirected relationships).

    Returns
    -------
    multi_layer_network
        The Aarhus CS social network.

    References
    ----------
    Magnani, M., & Rossi, L. (2011). The ML-model for multi-layer social
    networks. In Proc. ASONAM.

    Examples
    --------
    >>> from py3plex.datasets import load_aarhus_cs
    >>> network = load_aarhus_cs()
    >>> print(f"Nodes: {len(list(network.get_nodes()))}")
    >>> print(f"Layers: {network.get_layers()}")
    >>> network.basic_stats()
    """
    data_dir = get_data_dir()
    edges_file = os.path.join(data_dir, "aarhus_cs.edges")

    if not os.path.exists(edges_file):
        raise FileNotFoundError(
            f"Dataset file not found: {edges_file}. "
            "The bundled dataset may not have been installed correctly."
        )

    network = multi_layer_network(network_type="multiplex").load_network(
        edges_file,
        input_type="multiedgelist",
        directed=directed
    )

    return network


def load_synthetic_multilayer(directed: bool = False) -> multi_layer_network:
    """
    Load a synthetic multilayer network.

    This is a pre-generated synthetic network useful for testing,
    tutorials, and examples. It provides a consistent reference
    network for reproducible demonstrations.

    Dataset details: 50 nodes, 3 layers (layer1, layer2, layer3),
    approximately 200 edges across layers, undirected multilayer network.

    Parameters
    ----------
    directed : bool, default=False
        If True, load as directed network.

    Returns
    -------
    multi_layer_network
        A synthetic multilayer network.

    Examples
    --------
    >>> from py3plex.datasets import load_synthetic_multilayer
    >>> network = load_synthetic_multilayer()
    >>> print(f"Nodes: {len(list(network.get_nodes()))}")
    >>> print(f"Layers: {network.get_layers()}")
    """
    data_dir = get_data_dir()
    edges_file = os.path.join(data_dir, "synthetic_multilayer.edges")

    if not os.path.exists(edges_file):
        raise FileNotFoundError(
            f"Dataset file not found: {edges_file}. "
            "The bundled dataset may not have been installed correctly."
        )

    network = multi_layer_network(network_type="multilayer").load_network(
        edges_file,
        input_type="multiedgelist",
        directed=directed
    )

    return network
