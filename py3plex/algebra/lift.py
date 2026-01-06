"""Weight lifting specifications for edge attribute extraction.

Weight lifting defines how to extract a semiring element from edge attributes.
This is essential for mapping graph edges to semiring values.
"""

import math
from typing import Any, Callable, Dict, Optional, Union
from dataclasses import dataclass
from py3plex.exceptions import Py3plexException


@dataclass
class WeightLiftSpec:
    """Specification for lifting edge attributes to semiring elements.
    
    Defines how to extract and transform edge weights for semiring operations.
    
    Attributes:
        attr: Edge attribute name to read (e.g., "weight", "probability")
              If None, uses default value
        transform: Optional transformation to apply:
                   - "log": natural logarithm (for log-domain semirings)
                   - callable: custom function (value) -> transformed_value
                   - None: no transformation
        default: Default value if attribute is missing (based on on_missing)
        on_missing: Behavior when attribute is missing:
                   - "default": use default value
                   - "fail": raise exception
                   - "drop": skip edge (for sparse operations)
        
    Examples:
        >>> # Simple weight extraction
        >>> spec = WeightLiftSpec(attr="weight", default=1.0)
        >>> 
        >>> # Log-domain transformation
        >>> spec = WeightLiftSpec(attr="p", transform="log", default=0.0)
        >>> 
        >>> # Custom transformation
        >>> spec = WeightLiftSpec(
        ...     attr="reliability",
        ...     transform=lambda x: 1.0 - x,  # Convert to cost
        ...     default=0.5
        ... )
    """
    
    attr: Optional[str] = None
    transform: Optional[Union[str, Callable[[Any], Any]]] = None
    default: Any = 1.0
    on_missing: str = "default"
    
    def __post_init__(self):
        """Validate specification."""
        if self.on_missing not in ("default", "fail", "drop"):
            raise Py3plexException(
                f"Invalid on_missing value: '{self.on_missing}'. "
                f"Must be 'default', 'fail', or 'drop'."
            )
        
        if self.transform is not None:
            if not (self.transform == "log" or callable(self.transform)):
                raise Py3plexException(
                    f"Invalid transform: must be 'log' or callable, got {type(self.transform)}"
                )


def lift_edge_value(edge_attrs: Dict[str, Any], spec: WeightLiftSpec) -> Any:
    """Extract and transform edge weight according to lift specification.
    
    Args:
        edge_attrs: Dictionary of edge attributes
        spec: Weight lift specification
        
    Returns:
        Transformed value (semiring element)
        
    Raises:
        Py3plexException: If attribute missing and on_missing="fail"
        
    Examples:
        >>> attrs = {"weight": 2.5, "label": "A"}
        >>> spec = WeightLiftSpec(attr="weight", default=1.0)
        >>> lift_edge_value(attrs, spec)
        2.5
        >>> 
        >>> # Missing attribute with default
        >>> spec = WeightLiftSpec(attr="cost", default=1.0)
        >>> lift_edge_value(attrs, spec)
        1.0
        >>> 
        >>> # Log transformation
        >>> attrs = {"p": 0.8}
        >>> spec = WeightLiftSpec(attr="p", transform="log")
        >>> lift_edge_value(attrs, spec)
        -0.223...
    """
    # Get raw value
    if spec.attr is None:
        value = spec.default
    elif spec.attr in edge_attrs:
        value = edge_attrs[spec.attr]
    else:
        # Handle missing attribute
        if spec.on_missing == "fail":
            raise Py3plexException(
                f"Required edge attribute '{spec.attr}' not found. "
                f"Available attributes: {list(edge_attrs.keys())}"
            )
        elif spec.on_missing == "drop":
            # Signal to caller to skip this edge
            # Caller should check for this sentinel
            return None
        else:  # on_missing == "default"
            value = spec.default
    
    # Apply transformation
    if spec.transform is None:
        return value
    elif spec.transform == "log":
        if value <= 0:
            # Handle non-positive values for log
            # Return -inf for proper semiring behavior
            return -math.inf
        return math.log(value)
    elif callable(spec.transform):
        try:
            return spec.transform(value)
        except Exception as e:
            raise Py3plexException(
                f"Transform function failed for value {value}: {e}"
            )
    else:
        raise Py3plexException(f"Invalid transform: {spec.transform}")


def parse_lift_shorthand(weight: Optional[Union[str, WeightLiftSpec]] = None, **kwargs) -> WeightLiftSpec:
    """Parse shorthand notation into WeightLiftSpec.
    
    Helper for ergonomic API usage.
    
    Args:
        weight: Shorthand specification:
                - None: use default (attr=None, default=1.0)
                - str: attribute name (e.g., "weight")
                - WeightLiftSpec: pass through
        **kwargs: Additional WeightLiftSpec parameters
        
    Returns:
        WeightLiftSpec instance
        
    Examples:
        >>> # Simple attribute name
        >>> parse_lift_shorthand("weight")
        WeightLiftSpec(attr='weight', ...)
        >>> 
        >>> # Full spec
        >>> parse_lift_shorthand(WeightLiftSpec(attr="cost", default=2.0))
        WeightLiftSpec(attr='cost', default=2.0, ...)
        >>> 
        >>> # Default (no weight)
        >>> parse_lift_shorthand()
        WeightLiftSpec(attr=None, default=1.0, ...)
    """
    if isinstance(weight, WeightLiftSpec):
        return weight
    elif isinstance(weight, str):
        return WeightLiftSpec(attr=weight, **kwargs)
    elif weight is None:
        return WeightLiftSpec(attr=None, default=kwargs.get("default", 1.0), **kwargs)
    else:
        raise Py3plexException(f"Invalid weight specification: {weight}")
