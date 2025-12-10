"""
py3plex built-in datasets module.

This module provides easy access to built-in datasets for multilayer network
analysis, similar to scikit-learn's datasets module.

Available datasets: load_aarhus_cs (Aarhus CS department social network),
load_synthetic_multilayer (synthetic multilayer network).

Synthetic generators: make_random_multilayer (random multilayer Erdos-Renyi),
make_random_multiplex (random multiplex Erdos-Renyi), make_clique_multiplex
(multiplex with clique structure), make_social_network (synthetic social network).

Utility functions: list_datasets (list all available datasets),
get_data_dir (get path to data directory).

Example usage::

    from py3plex.datasets import load_aarhus_cs, list_datasets
    network = load_aarhus_cs()
    print(network)

    # List available datasets
    for name, desc in list_datasets():
        print(f"{name}: {desc}")

    # Generate synthetic network
    from py3plex.datasets import make_random_multilayer
    net = make_random_multilayer(n_nodes=50, n_layers=3, p=0.1)
"""

from py3plex.datasets._loaders import (
    get_data_dir,
    list_datasets,
    load_aarhus_cs,
    load_synthetic_multilayer,
    fetch_multilayer,
    list_multilayer,
)
from py3plex.datasets._generators import (
    make_clique_multiplex,
    make_random_multilayer,
    make_random_multiplex,
    make_social_network,
)

__all__ = [
    # Loaders for bundled datasets
    "load_aarhus_cs",
    "load_synthetic_multilayer",
    "fetch_multilayer",
    "list_multilayer",
    # Synthetic generators
    "make_random_multilayer",
    "make_random_multiplex",
    "make_clique_multiplex",
    "make_social_network",
    # Utility functions
    "list_datasets",
    "get_data_dir",
]
