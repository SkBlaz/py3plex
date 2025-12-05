"""Measure registry for dynamics module.

This module provides a registry for measures that can be computed during
simulation (prevalence, incidence, visit_frequency, etc.).
"""

from typing import Any, Callable, Dict, List, Optional

import numpy as np


class MeasureRegistry:
    """Registry for simulation measures.

    Measures are functions that compute statistics from simulation state.
    They are organized by process (some measures only apply to certain processes).
    """

    def __init__(self):
        self._measures: Dict[str, Dict[str, Callable]] = {}
        self._descriptions: Dict[str, Dict[str, str]] = {}
        self._global_measures: Dict[str, Callable] = {}
        self._global_descriptions: Dict[str, str] = {}

    def register(self, process_name: str, name: str, description: str = ""):
        """Decorator to register a measure for a specific process.

        Args:
            process_name: Process name (e.g., "SIS", "SIR")
            name: Measure name (e.g., "prevalence")
            description: Optional description

        Returns:
            Decorator function
        """
        def decorator(fn: Callable) -> Callable:
            self._measures.setdefault(process_name, {})[name] = fn
            self._descriptions.setdefault(process_name, {})[name] = description
            return fn
        return decorator

    def register_global(self, name: str, description: str = ""):
        """Decorator to register a global measure (works for any process).

        Args:
            name: Measure name
            description: Optional description

        Returns:
            Decorator function
        """
        def decorator(fn: Callable) -> Callable:
            self._global_measures[name] = fn
            self._global_descriptions[name] = description
            return fn
        return decorator

    def get(self, process_name: str, name: str) -> Callable:
        """Get a measure function.

        Args:
            process_name: Process name
            name: Measure name

        Returns:
            Measure function

        Raises:
            UnknownMeasureError: If measure not found
        """
        from .errors import UnknownMeasureError

        # Check process-specific measures first
        if process_name in self._measures and name in self._measures[process_name]:
            return self._measures[process_name][name]

        # Check global measures
        if name in self._global_measures:
            return self._global_measures[name]

        # Build list of known measures
        known = list(self._global_measures.keys())
        if process_name in self._measures:
            known.extend(self._measures[process_name].keys())

        raise UnknownMeasureError(name, known, process_name)

    def has(self, process_name: str, name: str) -> bool:
        """Check if a measure exists.

        Args:
            process_name: Process name
            name: Measure name

        Returns:
            True if measure exists
        """
        if process_name in self._measures and name in self._measures[process_name]:
            return True
        return name in self._global_measures

    def list_measures(self, process_name: Optional[str] = None) -> List[str]:
        """List available measures.

        Args:
            process_name: If provided, include process-specific measures

        Returns:
            List of measure names
        """
        measures = list(self._global_measures.keys())
        if process_name and process_name in self._measures:
            measures.extend(self._measures[process_name].keys())
        return sorted(set(measures))

    def get_description(self, process_name: str, name: str) -> Optional[str]:
        """Get measure description.

        Args:
            process_name: Process name
            name: Measure name

        Returns:
            Description string or None
        """
        if process_name in self._descriptions and name in self._descriptions[process_name]:
            return self._descriptions[process_name][name]
        return self._global_descriptions.get(name)


# Global measure registry
measure_registry = MeasureRegistry()


# Register SIS/SIR measures
@measure_registry.register("SIS", "prevalence", "Fraction of nodes in infected state")
@measure_registry.register("SIR", "prevalence", "Fraction of nodes in infected state")
def prevalence(state: np.ndarray, ctx: Dict[str, Any]) -> float:
    """Calculate prevalence (fraction of infected nodes).

    Args:
        state: State array with 0=S, 1=I (for SIS) or 0=S, 1=I, 2=R (for SIR)
        ctx: Context dictionary with additional info

    Returns:
        Fraction of infected nodes
    """
    if len(state) == 0:
        return 0.0
    return float(np.sum(state == 1)) / len(state)


@measure_registry.register("SIS", "incidence", "Number of new infections this step")
@measure_registry.register("SIR", "incidence", "Number of new infections this step")
def incidence(state: np.ndarray, ctx: Dict[str, Any]) -> int:
    """Calculate incidence (new infections this step).

    Requires ctx to have 'prev_state' for comparison.

    Args:
        state: Current state array
        ctx: Context dictionary with 'prev_state'

    Returns:
        Number of new infections
    """
    prev_state = ctx.get("prev_state")
    if prev_state is None:
        return 0

    # New infections: nodes that were S (0) and are now I (1)
    new_infected = np.sum((prev_state == 0) & (state == 1))
    return int(new_infected)


@measure_registry.register("SIS", "prevalence_by_layer", "Prevalence per layer")
@measure_registry.register("SIR", "prevalence_by_layer", "Prevalence per layer")
def prevalence_by_layer(state: np.ndarray, ctx: Dict[str, Any]) -> Dict[str, float]:
    """Calculate prevalence per layer.

    Requires ctx to have 'layer_info' with layer assignments.

    Args:
        state: State array
        ctx: Context dictionary with 'layer_info'

    Returns:
        Dictionary mapping layer name to prevalence
    """
    layer_info = ctx.get("layer_info", {})
    result = {}

    for layer_name, indices in layer_info.items():
        if len(indices) > 0:
            layer_state = state[indices]
            result[layer_name] = float(np.sum(layer_state == 1)) / len(layer_state)
        else:
            result[layer_name] = 0.0

    return result


@measure_registry.register("SIR", "R_t", "Effective reproduction number estimate")
def r_effective(state: np.ndarray, ctx: Dict[str, Any]) -> float:
    """Estimate effective reproduction number.

    Simple estimate based on ratio of new infections to recoveries.

    Args:
        state: Current state array
        ctx: Context dictionary with 'prev_state'

    Returns:
        Estimated R_t (or 0 if undefined)
    """
    prev_state = ctx.get("prev_state")
    if prev_state is None:
        return 0.0

    new_infected = np.sum((prev_state == 0) & (state == 1))
    new_recovered = np.sum((prev_state == 1) & (state == 2))

    if new_recovered == 0:
        return 0.0

    return float(new_infected) / float(new_recovered)


@measure_registry.register("RANDOM_WALK", "visit_frequency", "Visit frequency distribution")
def visit_frequency(state: np.ndarray, ctx: Dict[str, Any]) -> Dict[int, int]:
    """Get visit count for the current node.

    This is incremental - caller should accumulate.

    Args:
        state: State array with 1 at current position
        ctx: Context dictionary

    Returns:
        Dictionary with current node index as key, count 1 as value
    """
    current_pos = np.where(state == 1)[0]
    if len(current_pos) == 0:
        return {}
    return {int(current_pos[0]): 1}


@measure_registry.register_global("state_counts", "Count of nodes in each state")
def state_counts(state: np.ndarray, ctx: Dict[str, Any]) -> Dict[int, int]:
    """Count nodes in each state.

    Args:
        state: State array
        ctx: Context dictionary

    Returns:
        Dictionary mapping state value to count
    """
    unique, counts = np.unique(state, return_counts=True)
    return {int(s): int(c) for s, c in zip(unique, counts)}
