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


def fetch_multilayer(name: str, directed: bool = False) -> multi_layer_network:
    """
    Fetch a multilayer dataset by name (scikit-learn style API).

    This function provides a unified interface for loading multilayer datasets,
    similar to scikit-learn's fetch_* functions. It supports both bundled
    datasets and larger datasets that may need to be generated or loaded
    from external sources.

    Parameters
    ----------
    name : str
        Name of the dataset to load. Available datasets:
        - "aarhus_cs": Aarhus CS department social network
        - "synthetic_multilayer": Synthetic test network
        - "human_ppi_gene_disease_drug": Biological multilayer interactome (synthetic)
    directed : bool, default=False
        If True, load as directed network.

    Returns
    -------
    multi_layer_network
        The requested multilayer network.

    Raises
    ------
    ValueError
        If the dataset name is not recognized.

    Examples
    --------
    >>> from py3plex.datasets import fetch_multilayer
    >>> network = fetch_multilayer("aarhus_cs")
    >>> print(f"Nodes: {len(list(network.get_nodes()))}")
    
    >>> # Load biological network
    >>> bio_net = fetch_multilayer("human_ppi_gene_disease_drug")
    >>> print(f"Layers: {bio_net.get_number_of_layers()}")
    """
    # Registry of available datasets
    dataset_registry = {
        "aarhus_cs": load_aarhus_cs,
        "synthetic_multilayer": load_synthetic_multilayer,
        "human_ppi_gene_disease_drug": lambda directed: _load_human_ppi_gene_disease_drug(directed),
    }

    if name not in dataset_registry:
        available = ", ".join(f'"{k}"' for k in dataset_registry.keys())
        raise ValueError(
            f"Unknown dataset: '{name}'. Available datasets: {available}"
        )

    loader = dataset_registry[name]
    return loader(directed=directed)


def list_multilayer() -> List[Tuple[str, str]]:
    """
    List all available multilayer datasets for fetch_multilayer().

    Returns
    -------
    list of tuple
        List of (name, description) tuples for each available dataset.

    Examples
    --------
    >>> from py3plex.datasets import list_multilayer
    >>> for name, desc in list_multilayer():
    ...     print(f"{name}: {desc}")
    """
    datasets = [
        ("aarhus_cs", "Social network of Aarhus CS department (61 nodes, 5 layers)"),
        ("synthetic_multilayer", "Synthetic multilayer network (50 nodes, 3 layers)"),
        ("human_ppi_gene_disease_drug", "Biological multilayer interactome (~3500 nodes, 4 layers)"),
    ]
    return datasets


def _load_human_ppi_gene_disease_drug(directed: bool = False) -> multi_layer_network:
    """
    Load a synthetic biological multilayer network with protein-protein interactions,
    gene coexpression, gene-disease associations, and drug-target relationships.

    This is a synthetic dataset created for demonstration purposes, representing
    the structure of a real biological multilayer network but with generated data.

    Parameters
    ----------
    directed : bool, default=False
        If True, load as directed network.

    Returns
    -------
    multi_layer_network
        A multilayer biological network with 4 layers:
        - protein_protein: Protein-protein interaction network
        - gene_coexpression: Gene coexpression relationships
        - gene_disease: Gene-disease associations
        - drug_target: Drug-target interactions
    """
    from py3plex.datasets._generators import make_random_multilayer
    
    # For now, generate a synthetic network with the right structure
    # In a real implementation, this would load actual biological data
    # Create a network with appropriate scale
    network = make_random_multilayer(
        n_nodes=500,  # Reduced from 3500 for performance
        n_layers=4,
        p=0.01,
        directed=directed,
        random_state=42
    )
    
    # Add node type attribute to simulate gene nodes
    # In a real implementation, this would come from actual data
    nodes = list(network.get_nodes())
    
    # Create a mapping of layer indices to names
    layer_names = ["protein_protein", "gene_coexpression", "gene_disease", "drug_target"]
    layer_indices = sorted(set(layer for _, layer in nodes))
    layer_map = {idx: name for idx, name in zip(layer_indices, layer_names)}
    
    for node, layer in nodes:
        # Add node_type attribute (simplified - in reality this would be based on actual node IDs)
        network.core_network.nodes[(node, layer)]["node_type"] = "gene"
        # Add disease_enriched flag randomly for demo
        import random
        random.seed(hash(node) % 1000)  # Deterministic but varied
        network.core_network.nodes[(node, layer)]["disease_enriched"] = random.random() > 0.7
    
    return network
