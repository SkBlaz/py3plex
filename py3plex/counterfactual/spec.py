"""Immutable intervention specifications for counterfactual analysis.

This module defines the intervention specifications that describe how to
modify networks for counterfactual analysis. All specs are immutable,
hashable, and serializable.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Union
from abc import ABC, abstractmethod
import hashlib
import json
import re


# Type for target specifications
TargetSpec = Union[
    List[Any],           # List of node/edge IDs
    Set[Any],            # Set of node/edge IDs
    Callable[[Any], bool],  # Predicate function
    str,                 # Regex pattern or QueryBuilder serialization
    "QueryResult",       # Query result object
    "QueryBuilder",      # Query builder object
]


class InterventionSpec(ABC):
    """Base class for intervention specifications.
    
    All intervention specs must be:
    - Immutable (frozen dataclass)
    - Hashable (implement spec_hash)
    - Serializable (implement to_dict)
    """
    
    @abstractmethod
    def spec_hash(self) -> str:
        """Generate a stable hash for this specification.
        
        Returns:
            Hex digest string uniquely identifying this spec
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        pass
    
    @abstractmethod
    def apply(self, network: Any, seed: int) -> Any:
        """Apply this intervention to a network.
        
        Args:
            network: Network object to modify (will be copied)
            seed: Random seed for reproducibility
            
        Returns:
            Modified network copy
        """
        pass


@dataclass(frozen=True)
class RemoveEdgesSpec(InterventionSpec):
    """Remove edges from the network.
    
    Attributes:
        proportion: Fraction of edges to remove (0.0 to 1.0) OR
        budget: Exact number of edges to remove
        on: Optional target specification (nodes, layers, or predicate)
        mode: "random" or "targeted" (by weight/centrality)
    """
    proportion: Optional[float] = None
    budget: Optional[int] = None
    on: Optional[Any] = None  # TargetSpec
    mode: str = "random"
    
    def __post_init__(self):
        """Validate parameters."""
        if self.proportion is None and self.budget is None:
            raise ValueError("Must specify either proportion or budget")
        if self.proportion is not None and self.budget is not None:
            raise ValueError("Cannot specify both proportion and budget")
        if self.proportion is not None and not (0.0 <= self.proportion <= 1.0):
            raise ValueError(f"Proportion must be in [0, 1], got {self.proportion}")
        if self.budget is not None and self.budget < 0:
            raise ValueError(f"Budget must be non-negative, got {self.budget}")
        if self.mode not in ("random", "targeted"):
            raise ValueError(f"Mode must be 'random' or 'targeted', got {self.mode}")
    
    def spec_hash(self) -> str:
        """Generate stable hash."""
        data = {
            "type": "remove_edges",
            "proportion": self.proportion,
            "budget": self.budget,
            "on": str(self.on) if self.on is not None else None,
            "mode": self.mode,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "remove_edges",
            "proportion": self.proportion,
            "budget": self.budget,
            "on": str(self.on) if self.on is not None else None,
            "mode": self.mode,
        }
    
    def apply(self, network: Any, seed: int) -> Any:
        """Apply edge removal to network."""
        import copy
        import numpy as np
        
        # Create a copy of the network
        net_copy = copy.deepcopy(network)
        
        # Get edges to consider - format is ((source, source_layer), (target, target_layer))
        all_edges = list(net_copy.get_edges())
        
        # Filter by target if specified
        if self.on is not None:
            all_edges = self._filter_edges(all_edges, self.on)
        
        # Determine number of edges to remove
        if self.proportion is not None:
            n_remove = int(len(all_edges) * self.proportion)
        else:
            n_remove = min(self.budget, len(all_edges))
        
        if n_remove == 0:
            return net_copy
        
        # Select edges to remove
        rng = np.random.default_rng(seed)
        
        if self.mode == "random":
            edges_to_remove = rng.choice(len(all_edges), size=n_remove, replace=False)
            edges_to_remove = [all_edges[i] for i in edges_to_remove]
        else:  # targeted
            # For targeted removal, remove highest weight edges first
            # Need to get weights - for now use default if not available
            edges_with_weights = []
            for e in all_edges:
                # Edge format: ((source, source_layer), (target, target_layer))
                weight = 1.0  # Default weight
                edges_with_weights.append((e, weight))
            
            edges_with_weights.sort(key=lambda x: x[1], reverse=True)
            edges_to_remove = [e for e, w in edges_with_weights[:n_remove]]
        
        # Remove edges using the network API
        # Convert from ((source, src_layer), (target, tgt_layer)) to [source, src_layer, target, tgt_layer, weight]
        # Weight is required even for removal (will be ignored)
        edges_to_remove_list = [[e[0][0], e[0][1], e[1][0], e[1][1], 1.0] for e in edges_to_remove]
        net_copy.remove_edges(edges_to_remove_list, input_type="list")
        
        return net_copy
    
    def _filter_edges(self, edges: List[Any], target: Any) -> List[Any]:
        """Filter edges based on target specification.
        
        Edge format: ((source, source_layer), (target, target_layer))
        """
        # Simple implementation - can be extended
        if isinstance(target, (list, set)):
            # Filter edges involving target nodes
            target_set = set(target)
            return [e for e in edges if e[0][0] in target_set or e[1][0] in target_set]
        elif callable(target):
            # Apply predicate function
            return [e for e in edges if target(e)]
        elif isinstance(target, str):
            # Regex pattern on layer names
            pattern = re.compile(target)
            return [e for e in edges if pattern.match(str(e[0][1])) or pattern.match(str(e[1][1]))]
        else:
            return edges


@dataclass(frozen=True)
class RewireDegreePreservingSpec(InterventionSpec):
    """Rewire edges while preserving node degrees.
    
    Uses a double-edge swap algorithm to randomly rewire edges
    while maintaining the degree sequence.
    
    Attributes:
        n_swaps: Number of edge swaps to perform
        on: Optional target specification (layers to rewire)
    """
    n_swaps: int
    on: Optional[Any] = None
    
    def __post_init__(self):
        """Validate parameters."""
        if self.n_swaps < 0:
            raise ValueError(f"n_swaps must be non-negative, got {self.n_swaps}")
    
    def spec_hash(self) -> str:
        """Generate stable hash."""
        data = {
            "type": "rewire_degree_preserving",
            "n_swaps": self.n_swaps,
            "on": str(self.on) if self.on is not None else None,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "rewire_degree_preserving",
            "n_swaps": self.n_swaps,
            "on": str(self.on) if self.on is not None else None,
        }
    
    def apply(self, network: Any, seed: int) -> Any:
        """Apply degree-preserving rewiring."""
        import copy
        import numpy as np
        
        net_copy = copy.deepcopy(network)
        rng = np.random.default_rng(seed)
        
        # Get edges to rewire - format: ((source, src_layer), (target, tgt_layer))
        edges = list(net_copy.get_edges())
        
        if self.on is not None:
            edges = self._filter_edges(edges, self.on)
        
        if len(edges) < 4:
            # Need at least 4 edges for double-edge swap
            return net_copy
        
        # Perform swaps
        successful_swaps = 0
        attempts = 0
        max_attempts = self.n_swaps * 10  # Avoid infinite loops
        
        while successful_swaps < self.n_swaps and attempts < max_attempts:
            attempts += 1
            
            # Pick two random edges
            idx1, idx2 = rng.choice(len(edges), size=2, replace=False)
            edge1 = edges[idx1]
            edge2 = edges[idx2]
            
            # Extract components: ((u1, l1), (v1, l2)) and ((u2, l3), (v2, l4))
            u1, l1 = edge1[0][0], edge1[0][1]
            v1, l2 = edge1[1][0], edge1[1][1]
            
            u2, l3 = edge2[0][0], edge2[0][1]
            v2, l4 = edge2[1][0], edge2[1][1]
            
            # Try to swap: (u1, l1) -> (v2, l4) and (u2, l3) -> (v1, l2)
            # Check if nodes are different to avoid self-loops
            if u1 != v2 and u2 != v1:
                try:
                    # Remove old edges (need weight even though it's ignored)
                    net_copy.remove_edges([[u1, l1, v1, l2, 1.0], [u2, l3, v2, l4, 1.0]], input_type="list")
                    
                    # Add new edges
                    net_copy.add_edges([[u1, l1, v2, l4, 1.0], [u2, l3, v1, l2, 1.0]], input_type="list")
                    
                    # Update edges list
                    edges[idx1] = ((u1, l1), (v2, l4))
                    edges[idx2] = ((u2, l3), (v1, l2))
                    
                    successful_swaps += 1
                except Exception:
                    # If swap fails (e.g., edge already exists), continue
                    pass
        
        return net_copy
    
    def _filter_edges(self, edges: List[Any], target: Any) -> List[Any]:
        """Filter edges based on target specification.
        
        Edge format: ((source, source_layer), (target, target_layer))
        """
        if isinstance(target, (list, set)):
            target_set = set(target)
            return [e for e in edges if e[0][1] in target_set or e[1][1] in target_set]
        elif isinstance(target, str):
            pattern = re.compile(target)
            return [e for e in edges if pattern.match(str(e[0][1])) or pattern.match(str(e[1][1]))]
        else:
            return edges


@dataclass(frozen=True)
class ShuffleWeightsSpec(InterventionSpec):
    """Shuffle edge weights randomly.
    
    Attributes:
        on: Optional target specification (edges/layers to shuffle)
        preserve_layer: If True, shuffle weights only within each layer
    """
    on: Optional[Any] = None
    preserve_layer: bool = True
    
    def spec_hash(self) -> str:
        """Generate stable hash."""
        data = {
            "type": "shuffle_weights",
            "on": str(self.on) if self.on is not None else None,
            "preserve_layer": self.preserve_layer,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "shuffle_weights",
            "on": str(self.on) if self.on is not None else None,
            "preserve_layer": self.preserve_layer,
        }
    
    def apply(self, network: Any, seed: int) -> Any:
        """Apply weight shuffling."""
        import copy
        import numpy as np
        
        net_copy = copy.deepcopy(network)
        rng = np.random.default_rng(seed)
        
        # Get edges - format: ((source, src_layer), (target, tgt_layer))
        edges = list(net_copy.get_edges())
        
        if self.on is not None:
            edges = self._filter_edges(edges, self.on)
        
        if not edges:
            return net_copy
        
        # For weight shuffling, we'll use default weight 1.0 for all edges
        # since we don't have access to stored weights
        weights = [1.0] * len(edges)
        
        if self.preserve_layer:
            # Group by layer pairs
            layer_groups = {}
            for i, e in enumerate(edges):
                key = (e[0][1], e[1][1])  # (source_layer, target_layer)
                if key not in layer_groups:
                    layer_groups[key] = []
                layer_groups[key].append((i, weights[i]))
            
            # Shuffle within each group
            shuffled_weights = weights.copy()
            for key, group in layer_groups.items():
                indices, group_weights = zip(*group)
                shuffled_group_weights = rng.permutation(list(group_weights))
                for idx, new_weight in zip(indices, shuffled_group_weights):
                    shuffled_weights[idx] = float(new_weight)
        else:
            # Shuffle all weights together
            shuffled_weights = rng.permutation(weights)
        
        # Apply shuffled weights by removing old edges and adding new ones
        edges_to_remove = [[e[0][0], e[0][1], e[1][0], e[1][1], 1.0] for e in edges]
        edges_to_add = [[e[0][0], e[0][1], e[1][0], e[1][1], float(w)] for e, w in zip(edges, shuffled_weights)]
        
        net_copy.remove_edges(edges_to_remove, input_type="list")
        net_copy.add_edges(edges_to_add, input_type="list")
        
        return net_copy
    
    def _filter_edges(self, edges: List[Any], target: Any) -> List[Any]:
        """Filter edges based on target specification.
        
        Edge format: ((source, source_layer), (target, target_layer))
        """
        if isinstance(target, (list, set)):
            target_set = set(target)
            return [e for e in edges if e[0][1] in target_set or e[1][1] in target_set]
        elif isinstance(target, str):
            pattern = re.compile(target)
            return [e for e in edges if pattern.match(str(e[0][1])) or pattern.match(str(e[1][1]))]
        else:
            return edges


@dataclass(frozen=True)
class KnockoutSpec(InterventionSpec):
    """Remove specific nodes from the network.
    
    Attributes:
        nodes: List of node IDs to remove
        mode: "replicas" (remove from all layers) or "single_layer" (remove from specific layers)
        layers: If mode="single_layer", which layers to remove from
    """
    nodes: tuple  # Use tuple for immutability
    mode: str = "replicas"
    layers: Optional[tuple] = None  # Use tuple for immutability
    
    def __post_init__(self):
        """Validate parameters."""
        if self.mode not in ("replicas", "single_layer"):
            raise ValueError(f"Mode must be 'replicas' or 'single_layer', got {self.mode}")
        if self.mode == "single_layer" and self.layers is None:
            raise ValueError("Must specify layers when mode='single_layer'")
    
    def spec_hash(self) -> str:
        """Generate stable hash."""
        data = {
            "type": "knockout",
            "nodes": list(self.nodes),
            "mode": self.mode,
            "layers": list(self.layers) if self.layers else None,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": "knockout",
            "nodes": list(self.nodes),
            "mode": self.mode,
            "layers": list(self.layers) if self.layers else None,
        }
    
    def apply(self, network: Any, seed: int) -> Any:
        """Apply node knockout."""
        import copy
        
        net_copy = copy.deepcopy(network)
        
        # Get all edges - format: ((source, src_layer), (target, tgt_layer))
        all_edges = list(net_copy.get_edges())
        
        if self.mode == "replicas":
            # Remove nodes from all layers
            edges_to_remove = set()
            for node in self.nodes:
                # Find all edges involving this node
                for e in all_edges:
                    if e[0][0] == node or e[1][0] == node:
                        # Use tuple for deduplication
                        edges_to_remove.add((e[0][0], e[0][1], e[1][0], e[1][1], 1.0))
            
            if edges_to_remove:
                # Convert set to list for remove_edges
                net_copy.remove_edges([list(e) for e in edges_to_remove], input_type="list")
        else:  # single_layer
            # Remove nodes only from specific layers
            edges_to_remove = set()
            for node in self.nodes:
                for layer in self.layers:
                    for e in all_edges:
                        if (e[0][0] == node and e[0][1] == layer) or \
                           (e[1][0] == node and e[1][1] == layer):
                            # Use tuple for deduplication
                            edges_to_remove.add((e[0][0], e[0][1], e[1][0], e[1][1], 1.0))
            
            if edges_to_remove:
                # Convert set to list for remove_edges
                net_copy.remove_edges([list(e) for e in edges_to_remove], input_type="list")
        
        return net_copy


def remove_edges(proportion: Optional[float] = None, 
                budget: Optional[int] = None,
                on: Optional[TargetSpec] = None,
                mode: str = "random") -> RemoveEdgesSpec:
    """Create a RemoveEdgesSpec intervention.
    
    Args:
        proportion: Fraction of edges to remove (0.0 to 1.0)
        budget: Exact number of edges to remove
        on: Target specification (nodes, layers, or predicate)
        mode: "random" or "targeted"
        
    Returns:
        RemoveEdgesSpec instance
    """
    return RemoveEdgesSpec(proportion=proportion, budget=budget, on=on, mode=mode)


def rewire_degree_preserving(n_swaps: int, on: Optional[TargetSpec] = None) -> RewireDegreePreservingSpec:
    """Create a RewireDegreePreservingSpec intervention.
    
    Args:
        n_swaps: Number of edge swaps to perform
        on: Target specification (layers to rewire)
        
    Returns:
        RewireDegreePreservingSpec instance
    """
    return RewireDegreePreservingSpec(n_swaps=n_swaps, on=on)


def shuffle_weights(on: Optional[TargetSpec] = None, 
                   preserve_layer: bool = True) -> ShuffleWeightsSpec:
    """Create a ShuffleWeightsSpec intervention.
    
    Args:
        on: Target specification (edges/layers)
        preserve_layer: If True, shuffle only within layers
        
    Returns:
        ShuffleWeightsSpec instance
    """
    return ShuffleWeightsSpec(on=on, preserve_layer=preserve_layer)


def knockout(nodes: Union[List, tuple], 
            mode: str = "replicas",
            layers: Optional[Union[List, tuple]] = None) -> KnockoutSpec:
    """Create a KnockoutSpec intervention.
    
    Args:
        nodes: List of node IDs to remove
        mode: "replicas" (all layers) or "single_layer"
        layers: Layers to remove from (if single_layer mode)
        
    Returns:
        KnockoutSpec instance
    """
    # Convert to tuples for immutability
    nodes_tuple = tuple(nodes) if not isinstance(nodes, tuple) else nodes
    layers_tuple = tuple(layers) if layers and not isinstance(layers, tuple) else layers
    return KnockoutSpec(nodes=nodes_tuple, mode=mode, layers=layers_tuple)
