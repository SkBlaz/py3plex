"""Statistics registry for uncertainty-first system.

This module provides a registry for statistics that enforces uncertainty
model requirements.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .statvalue import StatValue
from .uncertainty import Uncertainty


@dataclass(frozen=True)
class StatisticSpec:
    """Specification for a registered statistic.
    
    Attributes:
        name: Unique identifier for the statistic
        estimator: Function that computes the statistic
        uncertainty_model: Function that provides uncertainty
        assumptions: List of assumptions (e.g., ["independence", "normality"])
        supports: Dict of capabilities (e.g., {"directed": True, "weighted": True})
    
    Examples:
        >>> from py3plex.stats import StatisticSpec, StatValue, Delta, Provenance
        >>> 
        >>> def compute_degree(network, node):
        ...     return network.core_network.degree(node)
        >>> 
        >>> def degree_uncertainty(network, node, **kwargs):
        ...     return Delta(0.0)  # Deterministic
        >>> 
        >>> spec = StatisticSpec(
        ...     name="degree",
        ...     estimator=compute_degree,
        ...     uncertainty_model=degree_uncertainty,
        ...     assumptions=["deterministic"],
        ...     supports={"directed": True, "weighted": True}
        ... )
    """
    
    name: str
    estimator: Callable[..., Any]
    uncertainty_model: Callable[..., Uncertainty]
    assumptions: List[str] = field(default_factory=list)
    supports: Dict[str, Any] = field(default_factory=dict)


class StatisticsRegistry:
    """Registry for statistics with enforced uncertainty models.
    
    This registry ensures that every registered statistic has an associated
    uncertainty model, even if it's just Delta(0) for deterministic stats.
    
    Examples:
        >>> from py3plex.stats import StatisticsRegistry
        >>> 
        >>> registry = StatisticsRegistry()
        >>> 
        >>> # This would fail - no uncertainty_model
        >>> # registry.register_statistic(StatisticSpec("bad", fn, None))
        >>> 
        >>> # This works
        >>> from py3plex.stats import Delta
        >>> registry.register_statistic(StatisticSpec(
        ...     "good",
        ...     lambda net: 42,
        ...     lambda net: Delta(0.0)
        ... ))
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._statistics: Dict[str, StatisticSpec] = {}
    
    def register_statistic(self, spec: StatisticSpec) -> None:
        """Register a statistic.
        
        Args:
            spec: Statistic specification
            
        Raises:
            ValueError: If uncertainty_model is missing or name already registered
        """
        if spec.uncertainty_model is None:
            raise ValueError(
                f"Cannot register statistic '{spec.name}': uncertainty_model is required. "
                f"For deterministic statistics, provide lambda: Delta(0.0)"
            )
        
        if spec.name in self._statistics:
            raise ValueError(
                f"Statistic '{spec.name}' is already registered. "
                f"Use force=True to overwrite."
            )
        
        self._statistics[spec.name] = spec
    
    def register_statistic_force(self, spec: StatisticSpec) -> None:
        """Register a statistic, overwriting if exists.
        
        Args:
            spec: Statistic specification
        """
        if spec.uncertainty_model is None:
            raise ValueError(
                f"Cannot register statistic '{spec.name}': uncertainty_model is required"
            )
        
        self._statistics[spec.name] = spec
    
    def get_statistic(self, name: str) -> StatisticSpec:
        """Retrieve a statistic by name.
        
        Args:
            name: Statistic name
            
        Returns:
            StatisticSpec
            
        Raises:
            KeyError: If statistic not found
        """
        if name not in self._statistics:
            raise KeyError(
                f"Statistic '{name}' not found. "
                f"Available: {', '.join(self.list_statistics())}"
            )
        return self._statistics[name]
    
    def has_statistic(self, name: str) -> bool:
        """Check if a statistic is registered.
        
        Args:
            name: Statistic name
            
        Returns:
            True if registered
        """
        return name in self._statistics
    
    def list_statistics(self) -> List[str]:
        """List all registered statistic names.
        
        Returns:
            List of statistic names
        """
        return sorted(self._statistics.keys())
    
    def compute(self, name: str, *args, with_uncertainty: bool = True, **kwargs) -> Any:
        """Compute a statistic with optional uncertainty.
        
        Args:
            name: Statistic name
            *args: Arguments to pass to estimator
            with_uncertainty: If True, return StatValue; if False, return raw value
            **kwargs: Keyword arguments to pass to estimator and uncertainty model
            
        Returns:
            StatValue if with_uncertainty=True, else raw value
        """
        spec = self.get_statistic(name)
        
        # Compute point estimate
        value = spec.estimator(*args, **kwargs)
        
        if not with_uncertainty:
            return value
        
        # Compute uncertainty
        uncertainty = spec.uncertainty_model(*args, **kwargs)
        
        # Build provenance
        from .provenance import Provenance
        provenance = Provenance(
            algorithm=name,
            uncertainty_method=uncertainty.to_json_dict().get("type", "unknown"),
            parameters=kwargs,
            seed=kwargs.get("seed"),
        )
        
        return StatValue(value, uncertainty, provenance)


# Global registry instance
_global_registry = StatisticsRegistry()


def register_statistic(spec: StatisticSpec, force: bool = False) -> None:
    """Register a statistic in the global registry.
    
    Args:
        spec: Statistic specification
        force: If True, overwrite existing registration
    """
    if force:
        _global_registry.register_statistic_force(spec)
    else:
        _global_registry.register_statistic(spec)


def get_statistic(name: str) -> StatisticSpec:
    """Get a statistic from the global registry.
    
    Args:
        name: Statistic name
        
    Returns:
        StatisticSpec
    """
    return _global_registry.get_statistic(name)


def list_statistics() -> List[str]:
    """List all statistics in the global registry.
    
    Returns:
        List of statistic names
    """
    return _global_registry.list_statistics()


def compute_statistic(name: str, *args, with_uncertainty: bool = True, **kwargs) -> Any:
    """Compute a statistic using the global registry.
    
    Args:
        name: Statistic name
        *args: Arguments for estimator
        with_uncertainty: If True, return StatValue
        **kwargs: Keyword arguments
        
    Returns:
        StatValue or raw value
    """
    return _global_registry.compute(name, *args, with_uncertainty=with_uncertainty, **kwargs)
