"""Algorithm requirements and network capabilities for compatibility checking.

This module defines the data model for declaring algorithm requirements and
computing network capabilities. It enables explicit, enforceable compatibility
checking across the py3plex ecosystem.

The system supports:
- Multilayer/multiplex network mode requirements
- Replica model constraints (strict, partial, none)
- Interlayer coupling requirements
- Weight and directedness requirements
- Randomness and seed requirements
- UQ support declarations
- Performance hints (complexity, memory, practical limits)

Example usage:
    >>> from py3plex.requirements import AlgoRequirements, check_compat, requires
    >>> 
    >>> # Define algorithm requirements
    >>> leiden_reqs = AlgoRequirements(
    ...     allowed_modes=("multiplex",),
    ...     replica_model=("strict",),
    ...     interlayer_coupling=("identity", "both"),
    ... )
    >>> 
    >>> # Check compatibility
    >>> net_caps = network.capabilities()
    >>> diagnostics = check_compat(net_caps, leiden_reqs)
    >>> 
    >>> # Or use decorator
    >>> @requires(leiden_reqs)
    ... def leiden_algorithm(network, **kwargs):
    ...     # Algorithm implementation
    ...     pass
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union
from functools import wraps

# Import diagnostic infrastructure
from py3plex.diagnostics.core import (
    Diagnostic,
    DiagnosticSeverity,
    DiagnosticContext,
    FixSuggestion,
)
from py3plex.exceptions import Py3plexException


# Type literals for network characteristics
NetworkMode = Literal["single", "multilayer", "multiplex", "temporal"]
ReplicaModel = Literal["none", "partial", "strict"]
CouplingType = Literal["none", "identity", "explicit_edges", "both"]
WeightDomain = Literal["binary", "positive", "real", "integer"]


@dataclass
class AlgoRequirements:
    """Requirements specification for an algorithm.
    
    This dataclass captures all constraints that an algorithm places on its
    input network. Defaults are permissive to allow gradual adoption.
    
    Attributes:
        allowed_modes: Acceptable network modes (single, multilayer, multiplex, temporal)
        replica_model: Acceptable replica models (none, partial, strict)
        interlayer_coupling: Required coupling types (none, identity, explicit_edges, both)
        requires_edge_weights: Whether algorithm requires weighted edges
        requires_positive_weights: Whether weights must be positive (>0)
        supports_directed: Whether algorithm works with directed networks
        supports_undirected: Whether algorithm works with undirected networks
        uses_randomness: Whether algorithm has stochastic components
        requires_seed_for_repro: Whether seed is mandatory for reproducibility
        supports_uq: Whether algorithm supports uncertainty quantification
        uq_methods: Supported UQ methods (bootstrap, perturbation, etc.)
        expected_complexity: Time/space complexity hint (e.g., "O(n^2)", "O(m log n)")
        memory_profile: Memory usage profile (e.g., "linear", "quadratic")
        practical_limits: Practical size limits (e.g., {"max_nodes": 10000})
    """
    
    allowed_modes: Tuple[NetworkMode, ...] = ("single", "multilayer", "multiplex", "temporal")
    replica_model: Tuple[ReplicaModel, ...] = ("none", "partial", "strict")
    interlayer_coupling: Tuple[CouplingType, ...] = ("none", "identity", "explicit_edges", "both")
    requires_edge_weights: bool = False
    requires_positive_weights: bool = False
    supports_directed: bool = True
    supports_undirected: bool = True
    uses_randomness: bool = False
    requires_seed_for_repro: bool = False
    supports_uq: bool = False
    uq_methods: Tuple[str, ...] = ()
    expected_complexity: Optional[str] = None
    memory_profile: Optional[str] = None
    practical_limits: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class NetworkCapabilities:
    """Computed capabilities of a network.
    
    This dataclass captures structural properties of a network that algorithms
    may require or constrain. Computed by network.capabilities().
    
    Attributes:
        mode: Network mode (single, multilayer, multiplex, temporal)
        replica_model: Replica model (none, partial, strict)
        interlayer_coupling: Coupling type (none, identity, explicit_edges, both)
        directed: Whether network is directed
        weighted: Whether network has edge weights
        weight_domain: Domain of edge weights (binary, positive, real, integer)
        has_missing_replicas: Whether some nodes don't appear in all layers
        layer_count: Number of layers
        base_node_count: Number of distinct base nodes (None for single layer)
        node_replica_count: Total node-layer pairs (None for single layer)
        has_self_loops: Whether network contains self-loops
        has_parallel_edges: Whether network has parallel edges
        total_edges: Total number of edges
    """
    
    mode: NetworkMode
    replica_model: ReplicaModel
    interlayer_coupling: CouplingType
    directed: bool
    weighted: bool
    weight_domain: Optional[WeightDomain] = None
    has_missing_replicas: Optional[bool] = None
    layer_count: int = 1
    base_node_count: Optional[int] = None
    node_replica_count: Optional[int] = None
    has_self_loops: bool = False
    has_parallel_edges: bool = False
    total_edges: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        for k, v in asdict(self).items():
            if v is not None:
                result[k] = v
        return result


# Diagnostic codes for algorithm requirements
ALGO_REQ_CODES = {
    "ALGO_REQ_001": "Network mode incompatible",
    "ALGO_REQ_002": "Replica model incompatible",
    "ALGO_REQ_003": "Interlayer coupling incompatible",
    "ALGO_REQ_004": "Edge weights required but missing",
    "ALGO_REQ_005": "Positive weights required but not satisfied",
    "ALGO_REQ_006": "Directedness incompatible",
    "ALGO_REQ_007": "Random seed missing",
    "ALGO_REQ_008": "UQ not supported",
    "ALGO_REQ_009": "UQ method not supported",
}


def check_compat(
    net_caps: NetworkCapabilities,
    req: AlgoRequirements,
    algorithm_name: Optional[str] = None,
    seed: Optional[int] = None,
    uq_requested: bool = False,
    uq_method: Optional[str] = None,
) -> List[Diagnostic]:
    """Check compatibility between network capabilities and algorithm requirements.
    
    Args:
        net_caps: Network capabilities computed from network structure
        req: Algorithm requirements specification
        algorithm_name: Name of algorithm for diagnostic context (optional)
        seed: Random seed if provided (optional)
        uq_requested: Whether uncertainty quantification was requested
        uq_method: UQ method if requested (optional)
    
    Returns:
        List of diagnostics (errors, warnings, or empty if compatible)
    """
    diagnostics = []
    algo_ctx = {"algorithm": algorithm_name} if algorithm_name else {}
    
    # Check network mode
    if net_caps.mode not in req.allowed_modes:
        diagnostics.append(Diagnostic(
            severity=DiagnosticSeverity.ERROR,
            code="ALGO_REQ_001",
            message=f"Algorithm requires network mode in {req.allowed_modes}, but got '{net_caps.mode}'",
            context=DiagnosticContext(
                additional={
                    "required": list(req.allowed_modes),
                    "got": net_caps.mode,
                    **algo_ctx,
                }
            ),
            cause=f"The algorithm is designed for {req.allowed_modes} networks and cannot handle '{net_caps.mode}' networks.",
            fixes=[
                FixSuggestion(
                    description=f"Convert from '{net_caps.mode}' to compatible mode",
                    replacement=_suggest_mode_conversion(net_caps.mode, req.allowed_modes),
                ),
                FixSuggestion(
                    description="Find algorithms compatible with your network type",
                    replacement="py3plex.algorithms.list(compatible_with=net)",
                ),
            ],
            related=["net.capabilities()", "net.summary()", "net.to_multiplex()", "net.to_multilayer()", "net.flatten_to_monoplex()"],
        ))
    
    # Check replica model
    if net_caps.replica_model not in req.replica_model:
        # Build context-aware fix suggestions
        fix_suggestions = []
        
        if "strict" in req.replica_model and net_caps.replica_model in ("partial", "none"):
            fix_suggestions.append(FixSuggestion(
                description="Convert to strict multiplex (all nodes present in all layers)",
                replacement="net.to_multiplex(method='intersection')  # Keeps only nodes in all layers",
            ))
        
        if "partial" in req.replica_model and net_caps.replica_model == "none":
            fix_suggestions.append(FixSuggestion(
                description="Convert single-layer to multilayer (enables partial replicas)",
                replacement="net.to_multilayer()  # Convert to multilayer representation",
            ))
        elif "partial" in req.replica_model and net_caps.replica_model == "strict":
            fix_suggestions.append(FixSuggestion(
                description="Relax from strict to partial replicas",
                replacement="net.to_multilayer()  # Allows nodes in subset of layers",
            ))
        
        if "none" in req.replica_model and net_caps.replica_model in ("partial", "strict"):
            fix_suggestions.append(FixSuggestion(
                description="Flatten to single-layer network",
                replacement="net.flatten_to_monoplex(method='union')  # Merge all layers",
            ))
        
        if not fix_suggestions:
            fix_suggestions.append(FixSuggestion(
                description="Use a compatible algorithm",
                replacement="py3plex.algorithms.list(compatible_with=net)",
            ))
        
        diagnostics.append(Diagnostic(
            severity=DiagnosticSeverity.ERROR,
            code="ALGO_REQ_002",
            message=f"Algorithm requires replica model in {req.replica_model}, but got '{net_caps.replica_model}'",
            context=DiagnosticContext(
                additional={
                    "required": list(req.replica_model),
                    "got": net_caps.replica_model,
                    **algo_ctx,
                }
            ),
            cause=f"The algorithm expects {req.replica_model} replica model but network uses '{net_caps.replica_model}'.",
            fixes=fix_suggestions,
            related=["net.capabilities()", "net.to_multiplex()", "net.to_multilayer()", "net.flatten_to_monoplex()"],
        ))
    
    # Check interlayer coupling
    if net_caps.interlayer_coupling not in req.interlayer_coupling:
        # Build context-aware fix suggestions  
        fix_suggestions = []
        
        if "identity" in req.interlayer_coupling and net_caps.interlayer_coupling == "none":
            fix_suggestions.append(FixSuggestion(
                description="Add identity interlayer edges (connect same nodes across layers)",
                replacement="net.add_identity_interlayer_edges(weight=1.0)  # Links node replicas",
            ))
        
        if "explicit_edges" in req.interlayer_coupling and net_caps.interlayer_coupling == "none":
            fix_suggestions.append(FixSuggestion(
                description="Add explicit interlayer edges",
                replacement="net.add_edges([{'source': node1, 'target': node2, 'source_type': layer1, 'target_type': layer2}])  # Custom cross-layer edges",
            ))
        
        if "both" in req.interlayer_coupling and net_caps.interlayer_coupling in ("none", "identity", "explicit_edges"):
            if net_caps.interlayer_coupling == "none":
                fix_suggestions.append(FixSuggestion(
                    description="Add both identity and explicit interlayer edges",
                    replacement="net.add_identity_interlayer_edges(weight=1.0); net.add_edges([...])  # Add both types",
                ))
            elif net_caps.interlayer_coupling == "identity":
                fix_suggestions.append(FixSuggestion(
                    description="Add explicit interlayer edges (identity edges already present)",
                    replacement="net.add_edges([{'source': node1, 'target': node2, 'source_type': layer1, 'target_type': layer2}])  # Add custom edges",
                ))
            elif net_caps.interlayer_coupling == "explicit_edges":
                fix_suggestions.append(FixSuggestion(
                    description="Add identity interlayer edges (explicit edges already present)",
                    replacement="net.add_identity_interlayer_edges(weight=1.0)  # Add identity edges",
                ))
        
        if "none" in req.interlayer_coupling and net_caps.interlayer_coupling != "none":
            fix_suggestions.append(FixSuggestion(
                description="Remove interlayer edges or flatten to single layer",
                replacement="net.flatten_to_monoplex(method='union')  # Merge layers without interlayer edges",
            ))
        
        if not fix_suggestions:
            fix_suggestions.append(FixSuggestion(
                description="Use a compatible algorithm",
                replacement="py3plex.algorithms.list(compatible_with=net)",
            ))
        
        diagnostics.append(Diagnostic(
            severity=DiagnosticSeverity.ERROR,
            code="ALGO_REQ_003",
            message=f"Algorithm requires coupling type in {req.interlayer_coupling}, but got '{net_caps.interlayer_coupling}'",
            context=DiagnosticContext(
                additional={
                    "required": list(req.interlayer_coupling),
                    "got": net_caps.interlayer_coupling,
                    **algo_ctx,
                }
            ),
            cause=f"The algorithm needs {req.interlayer_coupling} coupling but network has '{net_caps.interlayer_coupling}'.",
            fixes=fix_suggestions,
            related=["net.add_identity_interlayer_edges()", "net.add_edges()", "net.capabilities()", "net.flatten_to_monoplex()"],
        ))
    
    # Check edge weights requirement
    if req.requires_edge_weights and not net_caps.weighted:
        diagnostics.append(Diagnostic(
            severity=DiagnosticSeverity.ERROR,
            code="ALGO_REQ_004",
            message="Algorithm requires edge weights, but network is unweighted",
            context=DiagnosticContext(
                additional={
                    "required": "weighted",
                    "got": "unweighted",
                    **algo_ctx,
                }
            ),
            cause="The algorithm uses edge weights in its computation but no weights are present.",
            fixes=[
                FixSuggestion(
                    description="Add uniform weights to all edges",
                    replacement="net.set_uniform_weights(weight=1.0)",
                ),
                FixSuggestion(
                    description="Use an unweighted variant of the algorithm if available",
                ),
            ],
            related=["net.set_uniform_weights()"],
        ))
    
    # Check positive weights requirement
    if req.requires_positive_weights and net_caps.weighted:
        if net_caps.weight_domain not in ("positive", "binary"):
            diagnostics.append(Diagnostic(
                severity=DiagnosticSeverity.ERROR,
                code="ALGO_REQ_005",
                message=f"Algorithm requires positive weights, but network has '{net_caps.weight_domain}' weights",
                context=DiagnosticContext(
                    additional={
                        "required": "positive",
                        "got": net_caps.weight_domain,
                        **algo_ctx,
                    }
                ),
                cause="The algorithm assumes positive edge weights but some weights may be zero or negative.",
                fixes=[
                    FixSuggestion(
                        description="Transform weights to positive domain",
                        replacement="net.transform_weights(lambda w: abs(w) + epsilon)",
                    ),
                ],
                related=["net.get_edge_weights()"],
            ))
    
    # Check directedness
    if net_caps.directed and not req.supports_directed:
        diagnostics.append(Diagnostic(
            severity=DiagnosticSeverity.ERROR,
            code="ALGO_REQ_006",
            message="Algorithm does not support directed networks, but network is directed",
            context=DiagnosticContext(
                additional={
                    "required": "undirected",
                    "got": "directed",
                    **algo_ctx,
                }
            ),
            cause="The algorithm is designed for undirected networks only.",
            fixes=[
                FixSuggestion(
                    description="Convert to undirected network (symmetrize edges)",
                    replacement="net.to_undirected()",
                ),
            ],
            related=["net.to_undirected()"],
        ))
    
    if not net_caps.directed and not req.supports_undirected:
        diagnostics.append(Diagnostic(
            severity=DiagnosticSeverity.ERROR,
            code="ALGO_REQ_006",
            message="Algorithm requires directed network, but network is undirected",
            context=DiagnosticContext(
                additional={
                    "required": "directed",
                    "got": "undirected",
                    **algo_ctx,
                }
            ),
            cause="The algorithm is designed for directed networks only.",
            fixes=[
                FixSuggestion(
                    description="Convert to directed network",
                    replacement="net.to_directed()",
                ),
            ],
            related=["net.to_directed()"],
        ))
    
    # Check randomness/seed
    if req.uses_randomness and seed is None:
        severity = DiagnosticSeverity.ERROR if req.requires_seed_for_repro else DiagnosticSeverity.WARNING
        diagnostics.append(Diagnostic(
            severity=severity,
            code="ALGO_REQ_007",
            message="Algorithm uses randomness but no seed provided",
            context=DiagnosticContext(
                additional={
                    "required": "seed",
                    "got": None,
                    **algo_ctx,
                }
            ),
            cause="The algorithm has stochastic components that require a random seed for reproducibility.",
            fixes=[
                FixSuggestion(
                    description="Provide a random seed",
                    replacement="algorithm(..., seed=42)" if algorithm_name else "Pass seed=42 parameter",
                    example="result = leiden_multilayer(net, seed=42, ...)",
                ),
                FixSuggestion(
                    description="Set global random state",
                    replacement="np.random.seed(42); random.seed(42)",
                ),
            ],
            related=["Reproducibility Policy in AGENTS.md"],
        ))
    
    # Check UQ support
    if uq_requested:
        if not req.supports_uq:
            diagnostics.append(Diagnostic(
                severity=DiagnosticSeverity.ERROR,
                code="ALGO_REQ_008",
                message="Uncertainty quantification requested but algorithm does not support UQ",
                context=DiagnosticContext(
                    additional={
                        "supports_uq": False,
                        "uq_requested": True,
                        **algo_ctx,
                    }
                ),
                cause="The algorithm has not been designed to work with UQ estimation methods.",
                fixes=[
                    FixSuggestion(
                        description="Remove .uq() from query",
                        replacement="Remove the .uq(...) call from your DSL query",
                    ),
                    FixSuggestion(
                        description="Use a UQ-compatible algorithm",
                        replacement="py3plex.algorithms.list(supports_uq=True, compatible_with=net)",
                    ),
                ],
                related=["Uncertainty Quantification in AGENTS.md"],
            ))
        elif uq_method and req.uq_methods and uq_method not in req.uq_methods:
            diagnostics.append(Diagnostic(
                severity=DiagnosticSeverity.ERROR,
                code="ALGO_REQ_009",
                message=f"UQ method '{uq_method}' not supported by algorithm",
                context=DiagnosticContext(
                    additional={
                        "supported_methods": list(req.uq_methods),
                        "requested_method": uq_method,
                        **algo_ctx,
                    }
                ),
                cause=f"The algorithm only supports UQ methods: {req.uq_methods}",
                fixes=[
                    FixSuggestion(
                        description=f"Use supported UQ method",
                        replacement=f".uq(method='{req.uq_methods[0]}', ...)" if req.uq_methods else None,
                    ),
                ],
                related=["Uncertainty Quantification in AGENTS.md"],
            ))
    
    return diagnostics


def _suggest_mode_conversion(current_mode: NetworkMode, allowed_modes: Tuple[NetworkMode, ...]) -> str:
    """Suggest appropriate conversion based on current and allowed modes.
    
    Args:
        current_mode: Current network mode
        allowed_modes: Tuple of allowed modes for the algorithm
    
    Returns:
        Code snippet or description for converting network
    """
    # Priority order: multiplex > multilayer > single
    if "multiplex" in allowed_modes and current_mode != "multiplex":
        if current_mode == "multilayer":
            return "net.to_multiplex(method='intersection')  # Keep only nodes present in all layers"
        elif current_mode == "single":
            return "# Single-layer cannot be converted to multiplex; use multilayer algorithm instead"
        else:
            return "net.to_multiplex(method='intersection')"
    
    elif "multilayer" in allowed_modes and current_mode != "multilayer":
        if current_mode == "single":
            return "net.to_multilayer()  # Convert single-layer to multilayer representation"
        elif current_mode == "multiplex":
            return "net.to_multilayer()  # Relax to multilayer (allows partial replicas)"
        else:
            return "net.to_multilayer()"
    
    elif "single" in allowed_modes and current_mode != "single":
        if current_mode in ("multilayer", "multiplex"):
            return "net.flatten_to_monoplex(method='union')  # Merge all layers into single network"
        else:
            return "net.flatten_to_monoplex(method='union')"
    
    elif "temporal" in allowed_modes:
        return "# Convert to temporal network representation with time-stamped edges"
    
    else:
        return "# No direct conversion available; check py3plex.algorithms.list(compatible_with=net)"


class AlgorithmCompatibilityError(Py3plexException):
    """Exception raised when an algorithm is incompatible with a network.
    
    This exception wraps a list of diagnostics describing all compatibility
    issues between an algorithm's requirements and a network's capabilities.
    
    Attributes:
        diagnostics: List of Diagnostic objects describing issues
        algo_name: Name of the algorithm (optional)
    """
    
    default_code = "PX305"
    
    def __init__(
        self,
        diagnostics: List[Diagnostic],
        algo_name: Optional[str] = None,
        **kwargs
    ):
        """Initialize with diagnostics.
        
        Args:
            diagnostics: List of compatibility diagnostics
            algo_name: Name of the algorithm
            **kwargs: Additional arguments for Py3plexException
        """
        self.diagnostics = diagnostics
        self.algo_name = algo_name
        
        # Build message from diagnostics
        error_count = sum(1 for d in diagnostics if d.severity == DiagnosticSeverity.ERROR)
        warning_count = sum(1 for d in diagnostics if d.severity == DiagnosticSeverity.WARNING)
        
        algo_str = f" '{algo_name}'" if algo_name else ""
        message = f"Algorithm{algo_str} is incompatible with network: {error_count} error(s), {warning_count} warning(s)"
        
        # Extract top fix suggestions
        suggestions = []
        for diag in diagnostics[:3]:  # Top 3 diagnostics
            if diag.fixes:
                suggestions.append(diag.fixes[0].description)
        
        super().__init__(message, suggestions=suggestions, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error": "AlgorithmCompatibilityError",
            "code": self.code,
            "algorithm": self.algo_name,
            "message": str(self.args[0]) if self.args else "",
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "summary": {
                "errors": len([d for d in self.diagnostics if d.severity == DiagnosticSeverity.ERROR]),
                "warnings": len([d for d in self.diagnostics if d.severity == DiagnosticSeverity.WARNING]),
            }
        }
    
    def format_concise(self) -> str:
        """Format as concise error message for CLI."""
        lines = [str(self.args[0]) if self.args else "Algorithm compatibility error"]
        lines.append("")
        
        # Show top 2 errors
        errors = [d for d in self.diagnostics if d.severity == DiagnosticSeverity.ERROR]
        for diag in errors[:2]:
            lines.append(f"  • {diag.message}")
            if diag.fixes:
                lines.append(f"    Fix: {diag.fixes[0].description}")
        
        if len(errors) > 2:
            lines.append(f"  ... and {len(errors) - 2} more error(s)")
        
        lines.append("")
        lines.append("Use --verbose for full diagnostic details")
        
        return "\n".join(lines)
    
    def format_verbose(self) -> str:
        """Format as verbose error message with all diagnostics."""
        lines = [str(self.args[0]) if self.args else "Algorithm compatibility error"]
        lines.append("=" * 60)
        
        for diag in self.diagnostics:
            lines.append("")
            lines.append(diag.format(use_color=True))
        
        return "\n".join(lines)


def requires(requirements: AlgoRequirements, register: bool = True):
    """Decorator to attach requirements to an algorithm and enforce compatibility.
    
    This decorator:
    1. Attaches the requirements object as an attribute
    2. Wraps the function to check compatibility before execution
    3. Raises AlgorithmCompatibilityError if incompatible
    4. Propagates warnings into result metadata where possible
    5. Auto-registers the algorithm in the global registry (if register=True)
    
    Args:
        requirements: AlgoRequirements specification
        register: Whether to auto-register in global registry (default: True)
    
    Returns:
        Decorator function
    
    Example:
        >>> leiden_reqs = AlgoRequirements(
        ...     allowed_modes=("multiplex",),
        ...     replica_model=("strict",),
        ... )
        >>> 
        >>> @requires(leiden_reqs)
        ... def leiden_multilayer(network, **kwargs):
        ...     # Implementation
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        # Attach requirements as attribute
        func.requirements = requirements
        
        # Auto-register if requested (deferred to avoid circular import)
        if register:
            try:
                from py3plex.algorithms.requirements_registry import register_algorithm
                register_algorithm(func.__name__, requirements)
            except ImportError:
                # Registry not available yet during early imports
                pass
        
        @wraps(func)
        def wrapper(network, *args, **kwargs):
            # Get network capabilities
            if hasattr(network, 'capabilities'):
                net_caps = network.capabilities()
            else:
                # Fallback for networks without capabilities() method
                # This allows gradual adoption
                return func(network, *args, **kwargs)
            
            # Extract relevant kwargs
            seed = kwargs.get('seed') or kwargs.get('random_state')
            uq_requested = kwargs.get('uq', False) or kwargs.get('uncertainty', False)
            uq_method = kwargs.get('uq_method')
            
            # Check compatibility
            diagnostics = check_compat(
                net_caps,
                requirements,
                algorithm_name=func.__name__,
                seed=seed,
                uq_requested=uq_requested,
                uq_method=uq_method,
            )
            
            # Filter errors and warnings
            errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.ERROR]
            warnings = [d for d in diagnostics if d.severity == DiagnosticSeverity.WARNING]
            
            # Raise if errors
            if errors:
                raise AlgorithmCompatibilityError(
                    diagnostics=diagnostics,
                    algo_name=func.__name__,
                )
            
            # Execute function
            result = func(network, *args, **kwargs)
            
            # Attach warnings to result if it has metadata
            if warnings and hasattr(result, 'meta'):
                if 'diagnostics' not in result.meta:
                    result.meta['diagnostics'] = []
                result.meta['diagnostics'].extend([w.to_dict() for w in warnings])
            
            return result
        
        return wrapper
    
    return decorator


def validate_module_algorithms(module, exempt_patterns: Optional[List[str]] = None):
    """Validate that all public algorithm functions in a module have requirements.
    
    This function inspects a module and checks that all public callable functions
    (not starting with '_') have a 'requirements' attribute attached by @requires.
    
    Args:
        module: Python module to validate
        exempt_patterns: List of function name patterns to exempt from validation
                        (e.g., ["helper_", "internal_"])
    
    Returns:
        tuple: (all_valid, missing_requirements)
            - all_valid: Boolean indicating if all algorithms have requirements
            - missing_requirements: List of function names without requirements
    
    Example:
        >>> import py3plex.algorithms.community_detection as cd
        >>> all_valid, missing = validate_module_algorithms(cd)
        >>> if not all_valid:
        ...     print(f"Missing requirements: {missing}")
    """
    import inspect
    
    if exempt_patterns is None:
        exempt_patterns = []
    
    missing_requirements = []
    
    # Get all public callable objects from module
    for name, obj in inspect.getmembers(module):
        # Skip private/protected members
        if name.startswith('_'):
            continue
        
        # Skip exempted patterns
        if any(pattern in name for pattern in exempt_patterns):
            continue
        
        # Check if it's a function (not a class)
        if inspect.isfunction(obj) or inspect.ismethod(obj):
            # Check if it has requirements attribute
            if not hasattr(obj, 'requirements'):
                missing_requirements.append(name)
        elif inspect.isclass(obj):
            # For classes, check their public methods
            for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
                if not method_name.startswith('_'):
                    full_name = f"{name}.{method_name}"
                    if not hasattr(method, 'requirements'):
                        # Some methods might be utility methods, not algorithms
                        # Only flag if they seem like algorithm entry points
                        if any(keyword in method_name.lower() for keyword in 
                               ['centrality', 'community', 'detect', 'compute', 'calculate', 'simulate', 'run']):
                            missing_requirements.append(full_name)
    
    all_valid = len(missing_requirements) == 0
    return all_valid, missing_requirements


def enforce_requirements(module, raise_on_missing: bool = True, exempt_patterns: Optional[List[str]] = None):
    """Enforce that all algorithms in a module have requirements declared.
    
    This function validates that algorithms have requirements and optionally
    raises an error if any are missing.
    
    Args:
        module: Python module to validate
        raise_on_missing: If True, raise ValueError when algorithms lack requirements
        exempt_patterns: List of function name patterns to exempt
    
    Raises:
        ValueError: If raise_on_missing=True and algorithms lack requirements
    
    Example:
        >>> import py3plex.algorithms.community_detection as cd
        >>> enforce_requirements(cd)  # Raises if any algorithms lack requirements
    """
    all_valid, missing = validate_module_algorithms(module, exempt_patterns)
    
    if not all_valid and raise_on_missing:
        raise ValueError(
            f"Module '{module.__name__}' has algorithms without requirements: {missing}. "
            f"All algorithms must use @requires decorator to declare their requirements."
        )
    
    return all_valid, missing


def check_algorithm_has_requirements(func: Callable, warn: bool = True) -> bool:
    """Check if an algorithm function has requirements declared.
    
    This is a runtime check that can be used to validate algorithms
    before execution. Optionally emits a warning if requirements are missing.
    
    Args:
        func: Function to check
        warn: If True, emit warning when requirements are missing
    
    Returns:
        bool: True if requirements are present, False otherwise
    
    Example:
        >>> if not check_algorithm_has_requirements(my_algorithm):
        ...     print("Warning: Algorithm missing requirements!")
    """
    has_reqs = hasattr(func, 'requirements')
    
    if not has_reqs and warn:
        import warnings
        warnings.warn(
            f"Algorithm '{func.__name__}' does not declare requirements. "
            f"This is deprecated and will become an error in future versions. "
            f"Please use @requires decorator to declare algorithm requirements.",
            DeprecationWarning,
            stacklevel=2
        )
    
    return has_reqs
