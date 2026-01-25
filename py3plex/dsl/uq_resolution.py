"""UQ Resolution and Validation for DSL v2.

This module implements the canonical UQ resolution mechanism and schema validation
to ensure deterministic, fail-fast, and fully verifiable uncertainty quantification.

Resolution Order:
    metric-level > query-level > global defaults > library defaults

All UQ configurations are materialized before execution and validated against
the canonical schema.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from .ast import UQConfig, ComputeItem
from .errors import DslExecutionError


# Canonical UQ schema - all UQ results must conform to this
CANONICAL_UQ_SCHEMA = {
    "value",  # or "mean" - the point estimate
    "std",  # standard deviation
    "ci_low",  # lower confidence interval bound
    "ci_high",  # upper confidence interval bound
    "quantiles",  # dict of quantile values
    "n_samples",  # number of samples used
    "method",  # UQ method used
    "seed",  # random seed (if applicable)
}

# Optional schema fields for specific methods
OPTIONAL_UQ_FIELDS = {
    "null_model",  # null model type (for null_model method)
    "bootstrap_unit",  # bootstrap unit (for bootstrap method)
    "bootstrap_mode",  # bootstrap mode (for bootstrap method)
    "certainty",  # certainty metric (deprecated but maintained for compatibility)
    "zscore",  # z-score (for null_model method)
    "pvalue",  # p-value (for null_model method)
    "mean_null",  # null model mean (for null_model method)
}

# Library defaults for UQ
LIBRARY_UQ_DEFAULTS = {
    "method": "perturbation",
    "n_samples": 50,
    "ci": 0.95,
    "seed": None,
    "mode": "summarize_only",  # Default to current behavior
    "keep_samples": None,  # Will be determined based on mode/reduce
    "reduce": "empirical",  # Default reduction method
}

# Global defaults storage (mutable)
_GLOBAL_UQ_DEFAULTS: Dict[str, Any] = {}


class UQResolutionError(DslExecutionError):
    """Error raised when UQ configuration conflicts or is invalid."""
    pass


class UQSchemaValidationError(DslExecutionError):
    """Error raised when UQ result doesn't conform to canonical schema."""
    pass


class UQUnsupportedError(DslExecutionError):
    """Error raised when UQ is requested for unsupported context."""
    pass


class UQPropagationError(DslExecutionError):
    """Error raised when UQ propagation mode encounters an error."""
    pass


class UQIncompatibleConfiguration(DslExecutionError):
    """Error raised when UQ configurations are incompatible."""
    pass


class UQReductionError(DslExecutionError):
    """Error raised when UQ reduction operation fails."""
    pass


@dataclass
class ResolvedUQConfig:
    """Fully resolved and materialized UQ configuration.
    
    This represents the final UQ configuration after applying resolution order.
    It includes provenance information about where each setting came from.
    
    Attributes:
        method: UQ method to use
        n_samples: Number of samples for uncertainty estimation
        ci: Confidence interval level
        seed: Random seed for reproducibility
        mode: UQ execution mode ('summarize_only' or 'propagate')
        keep_samples: Whether to keep raw samples
        reduce: Reduction method ('empirical' or 'gaussian')
        kwargs: Additional method-specific parameters
        provenance: Dict mapping each config key to its source
        context: Where this config applies (metric name, query, global)
        enabled: Whether UQ is enabled
    """
    method: str
    n_samples: int
    ci: float
    seed: Optional[int]
    mode: str = "summarize_only"  # New: 'summarize_only' or 'propagate'
    keep_samples: bool = False  # New: Whether to keep raw samples
    reduce: str = "empirical"  # New: 'empirical' or 'gaussian'
    kwargs: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, str] = field(default_factory=dict)
    context: str = "unknown"
    enabled: bool = True  # New: Whether UQ is enabled
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)
    
    @property
    def structural_hash(self) -> str:
        """Compute a stable hash for determinism checks.
        
        This hash includes all configuration parameters that affect execution.
        Used to verify that replicate execution is deterministic.
        """
        import hashlib
        import json
        
        # Build deterministic dict of all relevant fields
        config_dict = {
            "method": self.method,
            "n_samples": self.n_samples,
            "ci": self.ci,
            "seed": self.seed,
            "mode": self.mode,
            "keep_samples": self.keep_samples,
            "reduce": self.reduce,
            "kwargs": sorted(self.kwargs.items()),  # Stable ordering
        }
        
        # Compute hash
        config_str = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def disable_inside_replicate(self) -> "ResolvedUQConfig":
        """Create a copy with UQ disabled for use inside replicate execution.
        
        Returns a copy of this config with enabled=False to prevent nested UQ loops.
        """
        import copy
        disabled = copy.deepcopy(self)
        disabled.enabled = False
        return disabled
    
    def validate(self) -> None:
        """Validate the resolved configuration.
        
        Raises:
            UQResolutionError: If configuration is invalid
        """
        # Validate method
        valid_methods = {"bootstrap", "perturbation", "seed", "null_model", "stratified_perturbation"}
        if self.method not in valid_methods:
            raise UQResolutionError(
                f"Invalid UQ method '{self.method}'. "
                f"Valid methods: {', '.join(sorted(valid_methods))}"
            )
        
        # Validate mode
        valid_modes = {"summarize_only", "propagate"}
        if self.mode not in valid_modes:
            raise UQResolutionError(
                f"Invalid UQ mode '{self.mode}'. "
                f"Valid modes: {', '.join(sorted(valid_modes))}"
            )
        
        # Validate reduce
        valid_reduce = {"empirical", "gaussian"}
        if self.reduce not in valid_reduce:
            raise UQResolutionError(
                f"Invalid reduce method '{self.reduce}'. "
                f"Valid methods: {', '.join(sorted(valid_reduce))}"
            )
        
        # Validate n_samples
        if self.n_samples <= 0:
            raise UQResolutionError(
                f"n_samples must be positive, got {self.n_samples}"
            )
        
        # Validate ci
        if not (0 < self.ci < 1):
            raise UQResolutionError(
                f"ci must be between 0 and 1, got {self.ci}"
            )
        
        # Validate method-specific requirements
        if self.method == "bootstrap":
            bootstrap_unit = self.kwargs.get("bootstrap_unit", "edges")
            if bootstrap_unit not in {"edges", "nodes", "layers"}:
                raise UQResolutionError(
                    f"Invalid bootstrap_unit '{bootstrap_unit}'. "
                    f"Valid units: edges, nodes, layers"
                )
            
            bootstrap_mode = self.kwargs.get("bootstrap_mode", "resample")
            if bootstrap_mode not in {"resample", "permute"}:
                raise UQResolutionError(
                    f"Invalid bootstrap_mode '{bootstrap_mode}'. "
                    f"Valid modes: resample, permute"
                )
        
        elif self.method == "null_model":
            null_model = self.kwargs.get("null_model")
            if not null_model:
                raise UQResolutionError(
                    "null_model method requires 'null_model' parameter "
                    "(e.g., 'degree_preserving', 'erdos_renyi', 'configuration')"
                )
            valid_null_models = {"degree_preserving", "erdos_renyi", "configuration"}
            if null_model not in valid_null_models:
                raise UQResolutionError(
                    f"Invalid null_model '{null_model}'. "
                    f"Valid models: {', '.join(sorted(valid_null_models))}"
                )


def set_global_uq_defaults(**kwargs) -> None:
    """Set global UQ defaults.
    
    These defaults are used when no query-level or metric-level config is provided.
    
    Args:
        **kwargs: UQ parameters (method, n_samples, ci, seed, etc.)
    """
    global _GLOBAL_UQ_DEFAULTS
    _GLOBAL_UQ_DEFAULTS.update(kwargs)


def get_global_uq_defaults() -> Dict[str, Any]:
    """Get current global UQ defaults."""
    return _GLOBAL_UQ_DEFAULTS.copy()


def reset_global_uq_defaults() -> None:
    """Reset global UQ defaults to empty."""
    global _GLOBAL_UQ_DEFAULTS
    _GLOBAL_UQ_DEFAULTS = {}


def resolve_uq_config(
    compute_item: ComputeItem,
    query_uq_config: Optional[UQConfig],
    metric_name: str,
) -> Optional[ResolvedUQConfig]:
    """Resolve UQ configuration following the priority order.
    
    Resolution order:
        1. Metric-level (from compute_item parameters)
        2. Query-level (from .uq() call)
        3. Global defaults (from UQ.defaults())
        4. Library defaults
    
    Args:
        compute_item: ComputeItem with potential metric-level config
        query_uq_config: Query-level UQConfig (from .uq() call)
        metric_name: Name of the metric being computed
        
    Returns:
        ResolvedUQConfig if UQ is enabled, None otherwise
        
    Raises:
        UQResolutionError: If conflicting configs at same priority level
    """
    # Check if UQ is explicitly disabled at metric level
    # Note: uncertainty=False is the default, so we need to distinguish
    # between explicit False and default False. We do this by checking
    # if any UQ parameters are set at the metric level.
    has_metric_uq_params = any([
        compute_item.method is not None,
        compute_item.n_samples is not None,
        compute_item.random_state is not None,
        compute_item.bootstrap_unit is not None,
        compute_item.n_null is not None,
    ])
    
    if compute_item.uncertainty is False and not has_metric_uq_params:
        # uncertainty=False and no UQ params at metric level
        # Check if query-level UQ should override
        if query_uq_config is not None and query_uq_config.method is not None:
            # Query-level UQ is set, so enable UQ
            pass  # Continue to resolution
        else:
            # No UQ at any level
            return None
    
    # Check if UQ is explicitly enabled at metric or query level
    uq_enabled = (
        compute_item.uncertainty is True
        or has_metric_uq_params
        or (query_uq_config is not None and query_uq_config.method is not None)
    )
    
    if not uq_enabled:
        return None
    
    provenance = {}
    
    # Start with library defaults
    resolved = LIBRARY_UQ_DEFAULTS.copy()
    for key in resolved:
        provenance[key] = "library_default"
    
    # Apply global defaults
    global_defaults = get_global_uq_defaults()
    for key, value in global_defaults.items():
        if value is not None:
            resolved[key] = value
            provenance[key] = "global_default"
    
    # Apply query-level config
    if query_uq_config is not None:
        if query_uq_config.method is not None:
            resolved["method"] = query_uq_config.method
            provenance["method"] = "query_level"
        if query_uq_config.n_samples is not None:
            resolved["n_samples"] = query_uq_config.n_samples
            provenance["n_samples"] = "query_level"
        if query_uq_config.ci is not None:
            resolved["ci"] = query_uq_config.ci
            provenance["ci"] = "query_level"
        if query_uq_config.seed is not None:
            resolved["seed"] = query_uq_config.seed
            provenance["seed"] = "query_level"
        
        # New fields for propagate mode
        if query_uq_config.mode is not None:
            resolved["mode"] = query_uq_config.mode
            provenance["mode"] = "query_level"
        if query_uq_config.keep_samples is not None:
            resolved["keep_samples"] = query_uq_config.keep_samples
            provenance["keep_samples"] = "query_level"
        if query_uq_config.reduce is not None:
            resolved["reduce"] = query_uq_config.reduce
            provenance["reduce"] = "query_level"
        
        # Merge kwargs
        query_kwargs = query_uq_config.kwargs or {}
        for key, value in query_kwargs.items():
            resolved[key] = value
            provenance[key] = "query_level"
    
    # Apply metric-level config (highest priority)
    metric_kwargs = {}
    
    if compute_item.method is not None:
        resolved["method"] = compute_item.method
        provenance["method"] = "metric_level"
    
    if compute_item.n_samples is not None:
        resolved["n_samples"] = compute_item.n_samples
        provenance["n_samples"] = "metric_level"
    
    if compute_item.ci is not None:
        resolved["ci"] = compute_item.ci
        provenance["ci"] = "metric_level"
    
    if compute_item.random_state is not None:
        resolved["seed"] = compute_item.random_state
        provenance["seed"] = "metric_level"
    
    # Handle metric-level specific parameters
    if compute_item.bootstrap_unit is not None:
        metric_kwargs["bootstrap_unit"] = compute_item.bootstrap_unit
        provenance["bootstrap_unit"] = "metric_level"
    
    if compute_item.bootstrap_mode is not None:
        metric_kwargs["bootstrap_mode"] = compute_item.bootstrap_mode
        provenance["bootstrap_mode"] = "metric_level"
    
    if compute_item.n_null is not None:
        metric_kwargs["n_null"] = compute_item.n_null
        provenance["n_null"] = "metric_level"
    
    if compute_item.null_model is not None:
        metric_kwargs["null_model"] = compute_item.null_model
        provenance["null_model"] = "metric_level"
    
    # Merge metric kwargs into resolved
    for key, value in metric_kwargs.items():
        resolved[key] = value
    
    # Extract kwargs from resolved
    standard_keys = {"method", "n_samples", "ci", "seed", "mode", "keep_samples", "reduce"}
    kwargs = {k: v for k, v in resolved.items() if k not in standard_keys}
    
    # Determine default keep_samples based on mode and reduce
    mode = resolved.get("mode", "summarize_only")
    reduce = resolved.get("reduce", "empirical")
    keep_samples = resolved.get("keep_samples")
    
    if keep_samples is None:
        # Default: keep samples in propagate mode unless using gaussian reduction
        if mode == "propagate":
            keep_samples = (reduce != "gaussian")
        else:
            keep_samples = False
    
    # Validate mode compatibility in propagate mode
    if mode == "propagate":
        # Check if metric-level method conflicts with query method
        if "method" in provenance and provenance["method"] == "metric_level":
            # Metric-level method set - check if it matches query method
            query_method = None
            if query_uq_config is not None:
                query_method = query_uq_config.method
            
            if query_method is not None and query_method != resolved["method"]:
                raise UQIncompatibleConfiguration(
                    f"In propagate mode, per-metric UQ method must match query-level method. "
                    f"Query method: '{query_method}', metric '{metric_name}' method: '{resolved['method']}'. "
                    f"Fix: Remove per-metric method parameter or use mode='summarize_only'."
                )
    
    # Create resolved config
    config = ResolvedUQConfig(
        method=resolved["method"],
        n_samples=resolved["n_samples"],
        ci=resolved["ci"],
        seed=resolved.get("seed"),
        mode=mode,
        keep_samples=keep_samples,
        reduce=reduce,
        kwargs=kwargs,
        provenance=provenance,
        context=f"metric:{metric_name}",
        enabled=True,
    )
    
    # Validate before returning
    config.validate()
    
    return config


def validate_uq_result_schema(
    result: Dict[str, Any],
    metric_name: str,
    allow_degenerate: bool = False,
) -> None:
    """Validate that a UQ result conforms to the canonical schema.
    
    Args:
        result: UQ result dictionary to validate
        metric_name: Name of the metric (for error messages)
        allow_degenerate: If True, allow degenerate UQ (std=0, no quantiles)
        
    Raises:
        UQSchemaValidationError: If result doesn't conform to schema
    """
    if not isinstance(result, dict):
        raise UQSchemaValidationError(
            f"UQ result for '{metric_name}' must be a dictionary, got {type(result).__name__}"
        )
    
    # Check for required fields (use 'mean' as synonym for 'value')
    required_fields = {"std", "n_samples", "method"}
    if "mean" in result:
        # 'mean' is acceptable as synonym for 'value'
        result_fields = set(result.keys())
    elif "value" in result:
        result_fields = set(result.keys())
    else:
        raise UQSchemaValidationError(
            f"UQ result for '{metric_name}' missing point estimate "
            f"(must have 'value' or 'mean' field). Got fields: {list(result.keys())}"
        )
    
    missing_fields = required_fields - result_fields
    if missing_fields:
        raise UQSchemaValidationError(
            f"UQ result for '{metric_name}' missing required fields: "
            f"{', '.join(sorted(missing_fields))}. "
            f"Got fields: {', '.join(sorted(result_fields))}"
        )
    
    # Validate std field
    std_val = result.get("std")
    if std_val is None or (not isinstance(std_val, (int, float)) and std_val != 0):
        if not allow_degenerate:
            raise UQSchemaValidationError(
                f"UQ result for '{metric_name}' has invalid 'std' field: {std_val}. "
                f"Must be a non-negative number."
            )
    
    # Check for CI bounds (at least one of ci_low/ci_high or quantiles)
    has_ci_bounds = "ci_low" in result_fields and "ci_high" in result_fields
    has_quantiles = "quantiles" in result_fields and isinstance(result.get("quantiles"), dict)
    
    if not (has_ci_bounds or has_quantiles):
        if not allow_degenerate or result.get("std", 0) > 0:
            raise UQSchemaValidationError(
                f"UQ result for '{metric_name}' must have either "
                f"(ci_low, ci_high) or quantiles. Got fields: {', '.join(sorted(result_fields))}"
            )
    
    # Validate quantiles structure if present
    if has_quantiles:
        quantiles = result["quantiles"]
        for q, value in quantiles.items():
            if not isinstance(q, (int, float)) or not (0 <= q <= 1):
                raise UQSchemaValidationError(
                    f"UQ result for '{metric_name}' has invalid quantile key: {q}. "
                    f"Quantile keys must be floats between 0 and 1."
                )
            if not isinstance(value, (int, float)):
                raise UQSchemaValidationError(
                    f"UQ result for '{metric_name}' has invalid quantile value for q={q}: {value}. "
                    f"Quantile values must be numeric."
                )
    
    # Validate n_samples
    n_samples = result.get("n_samples")
    if not isinstance(n_samples, int) or n_samples <= 0:
        raise UQSchemaValidationError(
            f"UQ result for '{metric_name}' has invalid 'n_samples': {n_samples}. "
            f"Must be a positive integer."
        )
    
    # Validate method
    method = result.get("method")
    if not isinstance(method, str) or not method:
        raise UQSchemaValidationError(
            f"UQ result for '{metric_name}' has invalid 'method': {method}. "
            f"Must be a non-empty string."
        )


def create_degenerate_uq_result(
    value: float,
    method: str = "deterministic",
    n_samples: int = 1,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a degenerate UQ result for deterministic metrics.
    
    This is used when UQ is requested but the metric is deterministic
    (e.g., degree, which doesn't vary with random seeds).
    
    Args:
        value: The deterministic value
        method: Method name (default: "deterministic")
        n_samples: Number of samples (default: 1)
        seed: Random seed (optional)
        
    Returns:
        Dictionary conforming to canonical UQ schema with std=0
    """
    result = {
        "mean": value,
        "value": value,  # Include both for compatibility
        "std": 0.0,
        "ci_low": value,
        "ci_high": value,
        "quantiles": {},
        "n_samples": n_samples,
        "method": method,
        "certainty": 1.0,
    }
    
    if seed is not None:
        result["seed"] = seed
    
    return result


def wrap_deterministic_as_uq(
    value: Any,
    resolved_config: ResolvedUQConfig,
) -> Dict[str, Any]:
    """Wrap a deterministic value with UQ scaffolding.
    
    This is used when UQ is requested but the computation is deterministic.
    
    Args:
        value: The deterministic value (scalar or dict)
        resolved_config: The resolved UQ configuration
        
    Returns:
        Dictionary conforming to canonical UQ schema
    """
    if isinstance(value, dict) and "mean" in value:
        # Already has UQ structure
        return value
    
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        # Non-numeric value - return with warning
        return {
            "value": value,
            "mean": value,
            "std": None,
            "ci_low": None,
            "ci_high": None,
            "quantiles": {},
            "n_samples": resolved_config.n_samples,
            "method": resolved_config.method,
            "seed": resolved_config.seed,
            "certainty": 1.0,
            "_warning": "Non-numeric value, UQ not applicable",
        }
    
    return create_degenerate_uq_result(
        numeric_value,
        method=resolved_config.method,
        n_samples=resolved_config.n_samples,
        seed=resolved_config.seed,
    )


def resolve_query_level_uq(
    query_uq_config: Optional[UQConfig],
) -> Optional[ResolvedUQConfig]:
    """Resolve query-level UQ configuration for execution planning.
    
    This is used when we need to determine if UQ propagation should be used,
    without resolving per-metric configurations.
    
    Args:
        query_uq_config: Query-level UQConfig from .uq() call
        
    Returns:
        ResolvedUQConfig if UQ is enabled at query level, None otherwise
    """
    if query_uq_config is None or query_uq_config.method is None:
        return None
    
    provenance = {}
    
    # Start with library defaults
    resolved = LIBRARY_UQ_DEFAULTS.copy()
    for key in resolved:
        provenance[key] = "library_default"
    
    # Apply global defaults
    global_defaults = get_global_uq_defaults()
    for key, value in global_defaults.items():
        if value is not None:
            resolved[key] = value
            provenance[key] = "global_default"
    
    # Apply query-level config
    if query_uq_config.method is not None:
        resolved["method"] = query_uq_config.method
        provenance["method"] = "query_level"
    if query_uq_config.n_samples is not None:
        resolved["n_samples"] = query_uq_config.n_samples
        provenance["n_samples"] = "query_level"
    if query_uq_config.ci is not None:
        resolved["ci"] = query_uq_config.ci
        provenance["ci"] = "query_level"
    if query_uq_config.seed is not None:
        resolved["seed"] = query_uq_config.seed
        provenance["seed"] = "query_level"
    
    # New fields for propagate mode
    if query_uq_config.mode is not None:
        resolved["mode"] = query_uq_config.mode
        provenance["mode"] = "query_level"
    if query_uq_config.keep_samples is not None:
        resolved["keep_samples"] = query_uq_config.keep_samples
        provenance["keep_samples"] = "query_level"
    if query_uq_config.reduce is not None:
        resolved["reduce"] = query_uq_config.reduce
        provenance["reduce"] = "query_level"
    
    # Merge kwargs
    query_kwargs = query_uq_config.kwargs or {}
    for key, value in query_kwargs.items():
        resolved[key] = value
        provenance[key] = "query_level"
    
    # Extract kwargs from resolved
    standard_keys = {"method", "n_samples", "ci", "seed", "mode", "keep_samples", "reduce"}
    kwargs = {k: v for k, v in resolved.items() if k not in standard_keys}
    
    # Determine default keep_samples based on mode and reduce
    mode = resolved.get("mode", "summarize_only")
    reduce = resolved.get("reduce", "empirical")
    keep_samples = resolved.get("keep_samples")
    
    if keep_samples is None:
        # Default: keep samples in propagate mode unless using gaussian reduction
        if mode == "propagate":
            keep_samples = (reduce != "gaussian")
        else:
            keep_samples = False
    
    # Create resolved config
    config = ResolvedUQConfig(
        method=resolved["method"],
        n_samples=resolved["n_samples"],
        ci=resolved["ci"],
        seed=resolved.get("seed"),
        mode=mode,
        keep_samples=keep_samples,
        reduce=reduce,
        kwargs=kwargs,
        provenance=provenance,
        context="query",
        enabled=True,
    )
    
    # Validate before returning
    config.validate()
    
    return config
