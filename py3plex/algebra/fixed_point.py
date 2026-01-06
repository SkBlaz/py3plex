"""Fixed-point iteration engine for semiring operations."""

from typing import Any, Callable, Dict, Optional
from py3plex.exceptions import Py3plexException


def fixed_point_iteration(
    initial_state: Dict[Any, Any],
    update_fn: Callable[[Dict[Any, Any]], Dict[Any, Any]],
    max_iters: int = 100,
    tol: Optional[float] = None,
    convergence_check: Optional[Callable[[Dict[Any, Any], Dict[Any, Any]], bool]] = None,
) -> tuple[Dict[Any, Any], bool, int]:
    """Generic fixed-point iteration for semiring computations.
    
    Useful for idempotent/complete semirings where iterations converge.
    
    Args:
        initial_state: Initial values
        update_fn: Function that computes next state
        max_iters: Maximum iterations
        tol: Optional tolerance for numeric convergence (requires numeric values)
        convergence_check: Optional custom convergence function
        
    Returns:
        Tuple of (final_state, converged, iterations)
    """
    state = initial_state.copy()
    
    for i in range(max_iters):
        new_state = update_fn(state)
        
        # Check convergence
        if convergence_check is not None:
            if convergence_check(state, new_state):
                return (new_state, True, i + 1)
        elif tol is not None:
            # Numeric convergence check
            if _numeric_converged(state, new_state, tol):
                return (new_state, True, i + 1)
        else:
            # Exact equality check (for idempotent semirings)
            if state == new_state:
                return (new_state, True, i + 1)
        
        state = new_state
    
    # Max iterations reached
    return (state, False, max_iters)


def _numeric_converged(state1: Dict[Any, Any], state2: Dict[Any, Any], tol: float) -> bool:
    """Check if numeric states have converged within tolerance."""
    if set(state1.keys()) != set(state2.keys()):
        return False
    
    for key in state1:
        v1 = state1[key]
        v2 = state2[key]
        
        # Try numeric comparison
        try:
            if abs(float(v1) - float(v2)) > tol:
                return False
        except (TypeError, ValueError):
            # Non-numeric values, use exact equality
            if v1 != v2:
                return False
    
    return True
