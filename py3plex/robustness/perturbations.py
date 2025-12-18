"""Perturbation primitives for robustness analysis on multilayer networks.

This module provides a Protocol for perturbations and several concrete
perturbation classes (EdgeDrop, EdgeAdd, NodeDrop) along with a composition
helper to chain perturbations together.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np

from py3plex.core import multinet


class Perturbation(Protocol):
    """Protocol for perturbations on a multi_layer_network.

    Implementations must not mutate the input network in-place.
    They must produce and return a new network instance.
    """

    def apply(
        self,
        network: multinet.multi_layer_network,
        rng: np.random.Generator,
    ) -> multinet.multi_layer_network:
        """Apply the perturbation to a network.

        Args:
            network: The input multilayer network (not mutated).
            rng: NumPy random generator for reproducibility.

        Returns:
            A new multi_layer_network with the perturbation applied.
        """
        ...


class EdgeDrop:
    """Randomly remove edges from a multilayer network.

    Parameters
    ----------
    p : float
        Probability of dropping each edge independently (0 <= p <= 1).
    layer : str or None
        If provided, restrict edge dropping to this layer name only.
        If None, apply to all layers.
    """

    def __init__(self, p: float, layer: str | None = None) -> None:
        if not (0.0 <= p <= 1.0):
            raise ValueError("p must be in [0, 1]")
        self.p = p
        self.layer = layer

    def apply(
        self,
        network: multinet.multi_layer_network,
        rng: np.random.Generator,
    ) -> multinet.multi_layer_network:
        """Apply edge drop perturbation.

        Args:
            network: The input multilayer network (not mutated).
            rng: NumPy random generator for reproducibility.

        Returns:
            A new multi_layer_network with edges randomly dropped.
        """
        new_net = multinet.multi_layer_network(
            directed=network.directed,
            network_type=network.network_type,
            verbose=False,
        )

        # Ensure the network is initialized even if empty
        new_net._initiate_network()

        # Collect edges to keep (preserve edge attributes)
        kept_edges: list[dict] = []
        for edge in network.get_edges(data=True):
            if len(edge) == 3:
                source_node, target_node, edge_data = edge
            else:
                source_node, target_node, _, edge_data = edge
            edge_data = edge_data or {}

            # Check if we should consider this edge for dropping
            should_consider = True
            if self.layer is not None:
                # Check if both endpoints are in the specified layer
                source_layer = source_node[1] if isinstance(source_node, tuple) else None
                target_layer = target_node[1] if isinstance(target_node, tuple) else None
                if source_layer != self.layer or target_layer != self.layer:
                    should_consider = False

            # Drop with probability p, keep with probability (1 - p)
            if should_consider and rng.random() < self.p:
                continue  # Drop this edge

            # Keep the edge
            kept_edges.append(
                {
                    "source": source_node[0],
                    "target": target_node[0],
                    "source_type": source_node[1],
                    "target_type": target_node[1],
                    **edge_data,
                    "weight": edge_data.get("weight", 1.0),
                    "type": edge_data.get("type", "default"),
                }
            )

        # Add all kept edges to the new network
        if kept_edges:
            new_net.add_edges(kept_edges, input_type="dict")

        # Preserve all nodes (including isolated) and their attributes.
        for node, attrs in network.get_nodes(data=True):
            new_net.core_network.add_node(node, **(attrs or {}))

        return new_net


class EdgeAdd:
    """Randomly add edges between currently non-adjacent node pairs.

    Parameters
    ----------
    p : float
        Probability for each candidate non-edge to be added (0 <= p <= 1).
        For MVP, we sample a limited number of candidate pairs to avoid O(n^2).
    layer : str or None
        If provided, restrict additions to this layer; otherwise, apply to all layers.
        Edges are only added within each layer (no new inter-layer edges).
    """

    def __init__(self, p: float, layer: str | None = None) -> None:
        if not (0.0 <= p <= 1.0):
            raise ValueError("p must be in [0, 1]")
        self.p = p
        self.layer = layer

    def apply(
        self,
        network: multinet.multi_layer_network,
        rng: np.random.Generator,
    ) -> multinet.multi_layer_network:
        """Apply edge add perturbation.

        Args:
            network: The input multilayer network (not mutated).
            rng: NumPy random generator for reproducibility.

        Returns:
            A new multi_layer_network with edges randomly added.
        """
        new_net = multinet.multi_layer_network(
            directed=network.directed,
            network_type=network.network_type,
            verbose=False,
        )

        # Ensure the network is initialized even if empty
        new_net._initiate_network()

        # Copy all existing edges
        edges_to_add: list[dict] = []
        existing_edge_set = set()

        for edge in network.get_edges(data=True):
            if len(edge) == 3:
                source_node, target_node, edge_data = edge
            else:
                source_node, target_node, _, edge_data = edge
            edge_data = edge_data or {}
            edges_to_add.append(
                {
                    "source": source_node[0],
                    "target": target_node[0],
                    "source_type": source_node[1],
                    "target_type": target_node[1],
                    **edge_data,
                    "weight": edge_data.get("weight", 1.0),
                    "type": edge_data.get("type", "default"),
                }
            )
            # Track existing edges (both directions for undirected)
            existing_edge_set.add((source_node, target_node))
            if not network.directed:
                existing_edge_set.add((target_node, source_node))

        # Group nodes by layer
        nodes_by_layer: dict = {}
        for node in network.get_nodes():
            layer = node[1] if isinstance(node, tuple) else None
            if layer not in nodes_by_layer:
                nodes_by_layer[layer] = []
            nodes_by_layer[layer].append(node)

        # Determine which layers to process
        if self.layer is not None:
            layers_to_process = [self.layer] if self.layer in nodes_by_layer else []
        else:
            layers_to_process = list(nodes_by_layer.keys())

        # For each layer, sample candidate pairs and potentially add edges
        for layer in layers_to_process:
            layer_nodes = nodes_by_layer[layer]
            n_nodes = len(layer_nodes)
            if n_nodes < 2:
                continue

            # Limit number of samples to avoid O(n^2)
            # Sample approximately num_edges candidate pairs
            num_existing = sum(
                1
                for e in edges_to_add
                if e.get("source_type") == layer and e.get("target_type") == layer
            )
            num_samples = max(n_nodes, num_existing, 10)

            for _ in range(num_samples):
                # Sample two distinct nodes
                i, j = rng.choice(n_nodes, size=2, replace=False)
                node_a = layer_nodes[i]
                node_b = layer_nodes[j]

                # Check if edge already exists
                if (node_a, node_b) in existing_edge_set:
                    continue

                # Add with probability p
                if rng.random() < self.p:
                    edges_to_add.append(
                        {
                            "source": node_a[0],
                            "target": node_b[0],
                            "source_type": node_a[1],
                            "target_type": node_b[1],
                            "weight": 1.0,
                            "type": "default",
                        }
                    )
                    existing_edge_set.add((node_a, node_b))
                    if not network.directed:
                        existing_edge_set.add((node_b, node_a))

        # Add all edges to the new network
        if edges_to_add:
            new_net.add_edges(edges_to_add, input_type="dict")

        # Preserve all nodes (including isolated) and their attributes.
        for node, attrs in network.get_nodes(data=True):
            new_net.core_network.add_node(node, **(attrs or {}))

        return new_net


class NodeDrop:
    """Randomly remove nodes (and all incident edges) from a multilayer network.

    Parameters
    ----------
    p : float
        Probability of dropping each node independently (0 <= p <= 1).
    """

    def __init__(self, p: float) -> None:
        if not (0.0 <= p <= 1.0):
            raise ValueError("p must be in [0, 1]")
        self.p = p

    def apply(
        self,
        network: multinet.multi_layer_network,
        rng: np.random.Generator,
    ) -> multinet.multi_layer_network:
        """Apply node drop perturbation.

        Args:
            network: The input multilayer network (not mutated).
            rng: NumPy random generator for reproducibility.

        Returns:
            A new multi_layer_network with nodes randomly dropped.
        """
        new_net = multinet.multi_layer_network(
            directed=network.directed,
            network_type=network.network_type,
            verbose=False,
        )

        # Ensure the network is initialized even if empty
        new_net._initiate_network()

        # Decide which nodes to keep
        kept_nodes = set()
        kept_node_attrs: dict = {}
        for node, attrs in network.get_nodes(data=True):
            if rng.random() >= self.p:  # Keep with probability (1 - p)
                kept_nodes.add(node)
                kept_node_attrs[node] = attrs or {}

        # Collect edges where both endpoints are kept
        kept_edges: list[dict] = []
        for edge in network.get_edges(data=True):
            if len(edge) == 3:
                source_node, target_node, edge_data = edge
            else:
                source_node, target_node, _, edge_data = edge
            edge_data = edge_data or {}

            if source_node in kept_nodes and target_node in kept_nodes:
                kept_edges.append(
                    {
                        "source": source_node[0],
                        "target": target_node[0],
                        "source_type": source_node[1],
                        "target_type": target_node[1],
                        **edge_data,
                        "weight": edge_data.get("weight", 1.0),
                        "type": edge_data.get("type", "default"),
                    }
                )

        # Add all kept edges to the new network
        if kept_edges:
            new_net.add_edges(kept_edges, input_type="dict")

        # Preserve kept nodes (including isolated) and their attributes.
        for node in kept_nodes:
            new_net.core_network.add_node(node, **kept_node_attrs.get(node, {}))

        return new_net


class _ComposedPerturbation:
    """Internal class for composed perturbations."""

    def __init__(self, perturbations: tuple) -> None:
        self._perturbations = list(perturbations)

    def apply(
        self,
        network: multinet.multi_layer_network,
        rng: np.random.Generator,
    ) -> multinet.multi_layer_network:
        """Apply all perturbations in sequence.

        Args:
            network: The input multilayer network (not mutated).
            rng: NumPy random generator for reproducibility.

        Returns:
            A new multi_layer_network with all perturbations applied.
        """
        result = network
        for p in self._perturbations:
            result = p.apply(result, rng)
        return result


def compose(*perturbations: Perturbation) -> Perturbation:
    """Compose multiple perturbations into a single perturbation applied in sequence.

    Args:
        *perturbations: Variable number of perturbation objects to compose.

    Returns:
        A new perturbation that applies all given perturbations in order.

    Example
    -------
    >>> perturb = compose(EdgeDrop(0.1), NodeDrop(0.05))
    >>> net2 = perturb.apply(net1, rng)
    """
    return _ComposedPerturbation(perturbations)
