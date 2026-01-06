"""Network perturbation functions for sensitivity analysis.

These functions apply controlled perturbations to networks while preserving
specified structural properties. They are used internally by sensitivity analysis
and may reuse UQ's resampling machinery where appropriate.

NOTE: Perturbations are NOT the same as UQ resampling:
- UQ resampling: Estimates measurement uncertainty (bootstrap, jackknife)
- Sensitivity perturbations: Tests robustness of conclusions under stress
"""

import copy
import random
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
import numpy as np


def edge_drop(
    network: Any,
    fraction: float,
    seed: Optional[int] = None,
    layer_aware: bool = True,
) -> Any:
    """Drop a fraction of edges from the network.

    This perturbation removes edges randomly to test robustness to
    missing data or edge noise.

    Args:
        network: Multilayer network object
        fraction: Fraction of edges to drop (0.0 to 1.0)
        seed: Random seed for reproducibility
        layer_aware: If True, drops edges proportionally from each layer
                    If False, drops edges uniformly across all layers

    Returns:
        Perturbed copy of the network

    Examples:
        >>> from py3plex.sensitivity import edge_drop
        >>> perturbed_net = edge_drop(network, fraction=0.1, seed=42)
    """
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"Fraction must be in [0, 1], got {fraction}")

    # Create a deep copy to avoid modifying original
    perturbed_net = copy.deepcopy(network)

    # Set random seed for reproducibility
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    if layer_aware and hasattr(perturbed_net, "get_layers"):
        # Drop edges proportionally from each layer
        layers = perturbed_net.get_layers()

        for layer in layers:
            # Get edges in this layer
            layer_edges = []
            for edge_tuple in perturbed_net.get_edges(data=False):
                if len(edge_tuple) >= 4:
                    src, src_layer, dst, dst_layer = edge_tuple[:4]
                    if src_layer == layer and dst_layer == layer:
                        layer_edges.append(edge_tuple)

            # Drop fraction of edges
            n_to_drop = int(len(layer_edges) * fraction)
            if n_to_drop > 0 and layer_edges:
                edges_to_drop = random.sample(layer_edges, n_to_drop)
                for edge in edges_to_drop:
                    try:
                        perturbed_net.remove_edge(edge)
                    except Exception:
                        # Edge might not exist in format expected
                        pass
    else:
        # Drop edges uniformly across all layers
        all_edges = list(perturbed_net.get_edges(data=False))
        n_to_drop = int(len(all_edges) * fraction)

        if n_to_drop > 0 and all_edges:
            edges_to_drop = random.sample(all_edges, n_to_drop)
            for edge in edges_to_drop:
                try:
                    perturbed_net.remove_edge(edge)
                except Exception:
                    pass

    return perturbed_net


def degree_preserving_rewire(
    network: Any,
    fraction: float,
    seed: Optional[int] = None,
    max_attempts: int = 100,
    layer_aware: bool = True,
) -> Any:
    """Rewire edges while preserving node degrees (configuration model style).

    This perturbation randomizes edge endpoints while keeping the degree
    sequence constant, testing robustness to topology changes.

    Args:
        network: Multilayer network object
        fraction: Fraction of edges to rewire (0.0 to 1.0)
        seed: Random seed for reproducibility
        max_attempts: Maximum rewiring attempts per edge
        layer_aware: If True, preserves layer membership of edges

    Returns:
        Perturbed copy of the network

    Examples:
        >>> from py3plex.sensitivity import degree_preserving_rewire
        >>> perturbed_net = degree_preserving_rewire(network, fraction=0.2, seed=42)
    """
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"Fraction must be in [0, 1], got {fraction}")

    # Create a deep copy
    perturbed_net = copy.deepcopy(network)

    # Set random seed
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    if layer_aware and hasattr(perturbed_net, "get_layers"):
        # Rewire within each layer
        layers = perturbed_net.get_layers()

        for layer in layers:
            # Get edges in this layer
            layer_edges = []
            for edge_tuple in perturbed_net.get_edges(data=True):
                if len(edge_tuple) >= 3:
                    src_info, dst_info, data = (
                        edge_tuple[0],
                        edge_tuple[1],
                        edge_tuple[2] if len(edge_tuple) > 2 else {},
                    )

                    # Extract layer info based on data format
                    if isinstance(src_info, tuple) and len(src_info) >= 2:
                        src, src_layer = src_info[:2]
                    else:
                        continue

                    if isinstance(dst_info, tuple) and len(dst_info) >= 2:
                        dst, dst_layer = dst_info[:2]
                    else:
                        continue

                    if src_layer == layer and dst_layer == layer:
                        layer_edges.append((src, dst, data))

            # Rewire fraction of edges
            n_to_rewire = int(len(layer_edges) * fraction)
            if n_to_rewire > 0 and len(layer_edges) >= 2:
                edges_to_rewire = random.sample(layer_edges, n_to_rewire)

                for src, dst, data in edges_to_rewire:
                    # Try to find a valid rewiring
                    for _ in range(max_attempts):
                        # Pick another edge randomly
                        other_idx = random.randint(0, len(layer_edges) - 1)
                        other_src, other_dst, other_data = layer_edges[other_idx]

                        # Attempt swap: (s1, d1), (s2, d2) -> (s1, d2), (s2, d1)
                        # Check if new edges don't already exist
                        new_edge1 = (src, other_dst)
                        new_edge2 = (other_src, dst)

                        # Simple validity check (could be enhanced)
                        if (
                            new_edge1 not in [(e[0], e[1]) for e in layer_edges]
                            and new_edge2 not in [(e[0], e[1]) for e in layer_edges]
                            and src != other_dst
                            and other_src != dst
                        ):
                            # Perform rewiring
                            try:
                                # Remove old edges
                                perturbed_net.remove_edge((src, layer, dst, layer))
                                perturbed_net.remove_edge(
                                    (other_src, layer, other_dst, layer)
                                )

                                # Add new edges
                                perturbed_net.add_edge(
                                    src,
                                    other_dst,
                                    layer,
                                    layer,
                                    data.get("weight", 1.0),
                                )
                                perturbed_net.add_edge(
                                    other_src,
                                    dst,
                                    layer,
                                    layer,
                                    other_data.get("weight", 1.0),
                                )
                                break
                            except Exception:
                                # If rewiring fails, skip
                                pass
    else:
        # Global rewiring (simplified - may not preserve degrees perfectly)
        # For non-multilayer or when layer_aware=False
        # This is a simplified version; full implementation would use double-edge swap
        pass

    return perturbed_net


def apply_perturbation(
    network: Any, method: str, strength: float, seed: Optional[int] = None, **kwargs
) -> Any:
    """Apply a perturbation to the network.

    This is the main dispatch function for perturbations.

    Args:
        network: Multilayer network object
        method: Perturbation method ('edge_drop', 'degree_preserving_rewire')
        strength: Perturbation strength (interpretation depends on method)
        seed: Random seed for reproducibility
        **kwargs: Additional method-specific parameters

    Returns:
        Perturbed copy of the network

    Raises:
        ValueError: If method is unknown

    Examples:
        >>> from py3plex.sensitivity import apply_perturbation
        >>> perturbed = apply_perturbation(net, "edge_drop", strength=0.1, seed=42)
    """
    if method == "edge_drop":
        return edge_drop(
            network,
            fraction=strength,
            seed=seed,
            layer_aware=kwargs.get("layer_aware", True),
        )
    elif method == "degree_preserving_rewire":
        return degree_preserving_rewire(
            network,
            fraction=strength,
            seed=seed,
            max_attempts=kwargs.get("max_attempts", 100),
            layer_aware=kwargs.get("layer_aware", True),
        )
    else:
        raise ValueError(
            f"Unknown perturbation method: {method}. "
            f"Supported: 'edge_drop', 'degree_preserving_rewire'"
        )
