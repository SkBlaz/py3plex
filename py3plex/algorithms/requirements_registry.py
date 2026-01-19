"""Algorithm requirements registry for py3plex.

This module provides a centralized registry of algorithm requirements,
making it easy to apply requirements to multiple algorithms at once.

Categories include:
- Community detection algorithms
- Centrality algorithms  
- Dynamics/simulation algorithms
- Statistical algorithms
- Null model generators
"""

from typing import Dict, List, Callable, Tuple
from py3plex.requirements import AlgoRequirements


# ============================================================================
# Standard Requirement Templates
# ============================================================================

# General multilayer algorithms (most permissive)
GENERAL_MULTILAYER_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=False,
    requires_seed_for_repro=False,
    supports_uq=False,
)

# Strict multiplex algorithms (require consistent node sets)
STRICT_MULTIPLEX_REQS = AlgoRequirements(
    allowed_modes=("multiplex",),
    replica_model=("strict",),
    interlayer_coupling=("identity", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=False,
    supports_undirected=True,
    uses_randomness=True,
    requires_seed_for_repro=True,
    supports_uq=False,
)

# Single-layer algorithms (only work on single networks)
SINGLE_LAYER_REQS = AlgoRequirements(
    allowed_modes=("single",),
    replica_model=("none",),
    interlayer_coupling=("none",),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=False,
    requires_seed_for_repro=False,
    supports_uq=False,
)

# Temporal algorithms
TEMPORAL_REQS = AlgoRequirements(
    allowed_modes=("temporal",),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=False,
    requires_seed_for_repro=False,
    supports_uq=False,
)

# Weighted graph algorithms
WEIGHTED_GRAPH_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=True,
    requires_positive_weights=True,
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=False,
    requires_seed_for_repro=False,
    supports_uq=False,
)

# Stochastic algorithms (require seed for reproducibility)
STOCHASTIC_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=True,
    requires_seed_for_repro=True,
    supports_uq=False,
)


# ============================================================================
# Algorithm-Specific Requirements
# ============================================================================

# Community Detection
LEIDEN_MULTILAYER_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),  # Works on single-layer too
    replica_model=("none", "partial", "strict"),  # Allow any replica model
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=False,
    supports_undirected=True,
    uses_randomness=True,
    requires_seed_for_repro=True,
    supports_uq=False,
    expected_complexity="O(n * m) per iteration",
    memory_profile="O(n + m)",
    practical_limits={"max_nodes": 100000, "max_edges": 1000000},
)

LOUVAIN_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=False,
    supports_undirected=True,
    uses_randomness=True,
    requires_seed_for_repro=True,
    supports_uq=False,
    expected_complexity="O(n log n)",
)

LABEL_PROPAGATION_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=False,
    supports_undirected=True,
    uses_randomness=True,
    requires_seed_for_repro=True,
    supports_uq=False,
)

INFOMAP_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=True,
    requires_seed_for_repro=True,
    supports_uq=False,
)

# Centrality
PAGERANK_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=False,
    requires_seed_for_repro=False,
    supports_uq=False,
    expected_complexity="O(k * m) where k is iterations",
    memory_profile="O(n^2) for dense, O(m) for sparse",
    practical_limits={"max_nodes": 100000},
)

BETWEENNESS_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,  # Works with or without weights; handles conversion internally
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=False,
    requires_seed_for_repro=False,
    supports_uq=False,
    expected_complexity="O(n * m)",
)

CLOSENESS_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,  # Works with or without weights; handles conversion internally
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=False,
    requires_seed_for_repro=False,
    supports_uq=False,
    expected_complexity="O(n^2)",
)

# Dynamics
SIS_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=True,
    requires_seed_for_repro=True,
    supports_uq=False,
    expected_complexity="O(m * steps)",
    memory_profile="O(n)",
    practical_limits={"max_nodes": 1000000},
)

SIR_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=True,
    requires_seed_for_repro=True,
    supports_uq=False,
)

RANDOM_WALK_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex", "temporal"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=True,
    requires_seed_for_repro=False,  # Seed can be set after initialization via set_seed()
    supports_uq=False,
)

# Null Models
NULL_MODEL_REQS = AlgoRequirements(
    allowed_modes=("single", "multilayer", "multiplex"),
    replica_model=("none", "partial", "strict"),
    interlayer_coupling=("none", "identity", "explicit_edges", "both"),
    requires_edge_weights=False,
    requires_positive_weights=False,
    supports_directed=True,
    supports_undirected=True,
    uses_randomness=True,
    requires_seed_for_repro=True,
    supports_uq=False,
)


# ============================================================================
# Algorithm Registry
# ============================================================================

class AlgorithmRegistry:
    """Registry for algorithm requirements.
    
    Allows registration and lookup of requirements for algorithms.
    """
    
    def __init__(self):
        self._registry: Dict[str, AlgoRequirements] = {}
        self._function_registry: Dict[Callable, AlgoRequirements] = {}
    
    def register(self, name: str, requirements: AlgoRequirements) -> None:
        """Register requirements for an algorithm by name.
        
        Args:
            name: Algorithm name (e.g., "leiden_multilayer")
            requirements: AlgoRequirements specification
        """
        self._registry[name] = requirements
    
    def register_function(self, func: Callable, requirements: AlgoRequirements) -> None:
        """Register requirements for an algorithm function.
        
        Args:
            func: Algorithm function
            requirements: AlgoRequirements specification
        """
        self._function_registry[func] = requirements
        # Also attach as attribute
        func.requirements = requirements
    
    def get(self, name: str) -> AlgoRequirements:
        """Get requirements for an algorithm by name.
        
        Args:
            name: Algorithm name
            
        Returns:
            AlgoRequirements or None if not found
        """
        return self._registry.get(name)
    
    def get_by_function(self, func: Callable) -> AlgoRequirements:
        """Get requirements for an algorithm function.
        
        Args:
            func: Algorithm function
            
        Returns:
            AlgoRequirements or None if not found
        """
        return self._function_registry.get(func)
    
    def list_algorithms(self, compatible_with=None) -> List[str]:
        """List registered algorithms.
        
        Args:
            compatible_with: Optional network to filter by compatibility
            
        Returns:
            List of algorithm names
        """
        if compatible_with is None:
            return sorted(self._registry.keys())
        
        # Filter by compatibility
        from py3plex.requirements import check_compat
        
        if not hasattr(compatible_with, 'capabilities'):
            return []
        
        caps = compatible_with.capabilities()
        compatible = []
        
        for name, reqs in self._registry.items():
            diagnostics = check_compat(caps, reqs)
            errors = [d for d in diagnostics if d.severity.value == 'error']
            if not errors:
                compatible.append(name)
        
        return sorted(compatible)
    
    def bulk_register(self, requirements: AlgoRequirements, *names: str) -> None:
        """Register the same requirements for multiple algorithms.
        
        Args:
            requirements: AlgoRequirements to apply
            *names: Algorithm names to register
        """
        for name in names:
            self.register(name, requirements)
    
    def is_registered(self, name: str) -> bool:
        """Check if an algorithm is registered.
        
        Args:
            name: Algorithm name
            
        Returns:
            bool: True if registered, False otherwise
        """
        return name in self._registry
    
    def get_unregistered_algorithms(self, module) -> List[str]:
        """Find algorithms in a module that are not registered.
        
        Args:
            module: Python module to check
            
        Returns:
            List of unregistered algorithm names
        """
        import inspect
        
        unregistered = []
        
        # Get all public callable objects from module
        for name, obj in inspect.getmembers(module):
            # Skip private/protected members
            if name.startswith('_'):
                continue
            
            # Check if it's a function
            if inspect.isfunction(obj) or inspect.ismethod(obj):
                # Check if it's NOT registered
                if not self.is_registered(name):
                    unregistered.append(name)
        
        return unregistered


# Global registry instance
_global_registry = AlgorithmRegistry()


# Convenience functions
def register_algorithm(name: str, requirements: AlgoRequirements) -> None:
    """Register an algorithm with requirements.
    
    Args:
        name: Algorithm name
        requirements: AlgoRequirements specification
    """
    _global_registry.register(name, requirements)


def get_algorithm_requirements(name: str) -> AlgoRequirements:
    """Get requirements for an algorithm.
    
    Args:
        name: Algorithm name
        
    Returns:
        AlgoRequirements or None if not found
    """
    return _global_registry.get(name)


def list_algorithms(compatible_with=None) -> List[str]:
    """List available algorithms, optionally filtered by network compatibility.
    
    Args:
        compatible_with: Optional network to filter by
        
    Returns:
        List of algorithm names
    """
    return _global_registry.list_algorithms(compatible_with=compatible_with)


def is_algorithm_registered(name: str) -> bool:
    """Check if an algorithm is registered in the global registry.
    
    Args:
        name: Algorithm name
        
    Returns:
        bool: True if registered, False otherwise
    """
    return _global_registry.is_registered(name)


def validate_module(module, strict: bool = False) -> Tuple[bool, List[str]]:
    """Validate that algorithms in a module are properly registered.
    
    This checks that all public algorithm functions are registered in the
    global registry with their requirements.
    
    Args:
        module: Python module to validate
        strict: If True, raises ValueError on validation failure
        
    Returns:
        tuple: (all_valid, unregistered_algorithms)
    
    Raises:
        ValueError: If strict=True and validation fails
    
    Example:
        >>> import py3plex.algorithms.community_detection as cd
        >>> valid, unregistered = validate_module(cd, strict=True)
    """
    unregistered = _global_registry.get_unregistered_algorithms(module)
    all_valid = len(unregistered) == 0
    
    if not all_valid and strict:
        raise ValueError(
            f"Module '{module.__name__}' has unregistered algorithms: {unregistered}. "
            f"All algorithms must be registered with requirements using @requires decorator "
            f"or manual registration via register_algorithm()."
        )
    
    return all_valid, unregistered


# ============================================================================
# Auto-registration of Known Algorithms
# ============================================================================

def _register_all_algorithms():
    """Register requirements for all known algorithms."""
    registry = _global_registry
    
    # Community detection
    registry.register("leiden_multilayer", LEIDEN_MULTILAYER_REQS)
    registry.register("leiden", LEIDEN_MULTILAYER_REQS)
    registry.register("louvain", LOUVAIN_REQS)
    registry.register("louvain_multilayer", LOUVAIN_REQS)
    registry.register("label_propagation", LABEL_PROPAGATION_REQS)
    registry.register("infomap", INFOMAP_REQS)
    
    # Centrality
    registry.register("pagerank", PAGERANK_REQS)
    registry.register("pagerank_centrality", PAGERANK_REQS)
    registry.register("betweenness", BETWEENNESS_REQS)
    registry.register("betweenness_centrality", BETWEENNESS_REQS)
    registry.register("closeness", CLOSENESS_REQS)
    registry.register("closeness_centrality", CLOSENESS_REQS)
    registry.register("degree", GENERAL_MULTILAYER_REQS)
    registry.register("degree_centrality", GENERAL_MULTILAYER_REQS)
    registry.register("eigenvector", GENERAL_MULTILAYER_REQS)
    registry.register("eigenvector_centrality", GENERAL_MULTILAYER_REQS)
    
    # Dynamics
    registry.register("SIS", SIS_REQS)
    registry.register("SIR", SIR_REQS)
    registry.register("sis_dynamics", SIS_REQS)
    registry.register("sir_dynamics", SIR_REQS)
    registry.register("random_walk", RANDOM_WALK_REQS)
    
    # Null models
    registry.bulk_register(
        NULL_MODEL_REQS,
        "configuration_model",
        "erdos_renyi",
        "random_graph",
        "null_model",
    )
    
    # Statistics (general multilayer)
    registry.bulk_register(
        GENERAL_MULTILAYER_REQS,
        "clustering_coefficient",
        "transitivity",
        "density",
        "assortativity",
        "modularity",
    )
    
    # Multilayer-specific statistics
    registry.bulk_register(
        GENERAL_MULTILAYER_REQS,
        "layer_density",
        "inter_layer_coupling_strength",
        "node_activity",
        "versatility_centrality",
        "interdependence",
        "algebraic_connectivity",
    )
    
    # Temporal algorithms
    registry.bulk_register(
        TEMPORAL_REQS,
        "temporal_pagerank",
        "temporal_betweenness",
        "temporal_closeness",
    )


# Auto-register on module import
_register_all_algorithms()
