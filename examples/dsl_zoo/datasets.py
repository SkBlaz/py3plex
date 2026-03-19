"""Toy datasets for DSL query zoo examples."""

from __future__ import annotations

import random
from typing import Dict, Iterable, List, Tuple

from py3plex.core import multinet

EdgeSpec = Tuple[str, str, float]


def _build_network(
    layers_to_edges: Dict[str, Iterable[EdgeSpec]],
    interlayer_nodes: Iterable[str],
) -> multinet.multi_layer_network:
    net = multinet.multi_layer_network(directed=False)
    edges: List[dict] = []

    for layer, layer_edges in layers_to_edges.items():
        for source, target, weight in layer_edges:
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "source_type": layer,
                    "target_type": layer,
                    "weight": float(weight),
                }
            )

    ordered_layers = list(layers_to_edges.keys())
    for node in interlayer_nodes:
        for idx, source_layer in enumerate(ordered_layers):
            for target_layer in ordered_layers[idx + 1 :]:
                edges.append(
                    {
                        "source": node,
                        "target": node,
                        "source_type": source_layer,
                        "target_type": target_layer,
                        "weight": 1.0,
                    }
                )

    net.add_edges(edges)
    return net


def create_social_work_network(seed: int = 42):
    rng = random.Random(seed)
    return _build_network(
        {
            "social": [
                ("Alice", "Bob", 1.0 + rng.random()),
                ("Alice", "Carol", 1.0 + rng.random()),
                ("Bob", "Dave", 1.0 + rng.random()),
                ("Carol", "Eve", 1.0 + rng.random()),
                ("Dave", "Eve", 1.0 + rng.random()),
            ],
            "work": [
                ("Alice", "Dave", 1.0 + rng.random()),
                ("Alice", "Eve", 1.0 + rng.random()),
                ("Bob", "Carol", 1.0 + rng.random()),
                ("Carol", "Frank", 1.0 + rng.random()),
                ("Eve", "Frank", 1.0 + rng.random()),
            ],
            "family": [
                ("Alice", "Frank", 1.0 + rng.random()),
                ("Bob", "Eve", 1.0 + rng.random()),
                ("Carol", "Dave", 1.0 + rng.random()),
                ("Dave", "Frank", 1.0 + rng.random()),
            ],
        },
        interlayer_nodes=["Alice", "Bob", "Carol", "Dave"],
    )


def create_communication_network(seed: int = 42):
    rng = random.Random(seed + 1)
    return _build_network(
        {
            "email": [
                ("Ana", "Ben", 1.0 + rng.random()),
                ("Ana", "Cyd", 1.0 + rng.random()),
                ("Ben", "Dia", 1.0 + rng.random()),
                ("Cyd", "Eli", 1.0 + rng.random()),
            ],
            "chat": [
                ("Ana", "Ben", 1.0 + rng.random()),
                ("Ben", "Cyd", 1.0 + rng.random()),
                ("Ben", "Eli", 1.0 + rng.random()),
                ("Dia", "Eli", 1.0 + rng.random()),
            ],
            "phone": [
                ("Ana", "Dia", 1.0 + rng.random()),
                ("Ben", "Eli", 1.0 + rng.random()),
                ("Cyd", "Dia", 1.0 + rng.random()),
                ("Cyd", "Eli", 1.0 + rng.random()),
            ],
        },
        interlayer_nodes=["Ana", "Ben", "Cyd", "Dia"],
    )


def create_transport_network(seed: int = 42):
    rng = random.Random(seed + 2)
    return _build_network(
        {
            "bus": [
                ("S1", "S2", 1.0 + rng.random()),
                ("S2", "S3", 1.0 + rng.random()),
                ("S3", "S4", 1.0 + rng.random()),
                ("S2", "S5", 1.0 + rng.random()),
            ],
            "metro": [
                ("S1", "S3", 1.0 + rng.random()),
                ("S3", "S5", 1.0 + rng.random()),
                ("S5", "S6", 1.0 + rng.random()),
                ("S2", "S6", 1.0 + rng.random()),
            ],
            "walking": [
                ("S1", "S2", 1.0 + rng.random()),
                ("S2", "S4", 1.0 + rng.random()),
                ("S4", "S5", 1.0 + rng.random()),
                ("S5", "S6", 1.0 + rng.random()),
            ],
        },
        interlayer_nodes=["S1", "S2", "S3", "S5"],
    )


def get_dataset(name: str, seed: int = 42):
    factories = {
        "social_work": create_social_work_network,
        "communication": create_communication_network,
        "transport": create_transport_network,
    }
    if name not in factories:
        raise ValueError(f"Unknown dataset: {name}")
    return factories[name](seed=seed)
