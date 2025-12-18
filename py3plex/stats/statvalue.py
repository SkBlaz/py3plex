"""StatValue: Container for statistics with first-class uncertainty.

This module provides the core StatValue class that wraps a statistical value
with uncertainty and provenance information.
"""

from dataclasses import dataclass
from typing import Union
import numpy as np

from .uncertainty import Uncertainty, Delta
from .provenance import Provenance


def _scale_uncertainty(uncertainty: Uncertainty, factor: float) -> Uncertainty:
    """Scale an uncertainty distribution by a constant factor.

    Uncertainty models in this module represent *relative* uncertainty (offsets
    around the point estimate). If a statistic is multiplied by a constant k,
    the uncertainty offsets should also be multiplied by k.
    """
    from .uncertainty import Bootstrap, Empirical, Gaussian, Interval

    if factor == 0:
        return Delta(0.0)

    if isinstance(uncertainty, Delta):
        return Delta(abs(factor) * uncertainty.sigma)

    if isinstance(uncertainty, Gaussian):
        return Gaussian(uncertainty.mean * factor, abs(factor) * uncertainty.std_dev)

    if isinstance(uncertainty, Interval):
        low = uncertainty.low * factor
        high = uncertainty.high * factor
        if low <= high:
            return Interval(low, high)
        return Interval(high, low)

    if isinstance(uncertainty, Bootstrap):
        return Bootstrap(np.asarray(uncertainty.samples) * factor)

    if isinstance(uncertainty, Empirical):
        return Empirical(np.asarray(uncertainty.samples) * factor)

    # Best-effort fallback for custom uncertainty types.
    return Empirical(np.asarray(uncertainty.sample(4096, seed=0)) * factor)


@dataclass(frozen=True)
class StatValue:
    """A statistical value with uncertainty and provenance.
    
    This is the fundamental type for all statistics in the uncertainty-first
    system. Every statistic is a StatValue, even deterministic ones (which
    carry Delta(0) uncertainty).
    
    Attributes:
        value: Point estimate (float, int, or ndarray)
        uncertainty: Uncertainty model
        provenance: How this statistic was computed
    
    Examples:
        >>> from py3plex.stats import StatValue, Delta, Provenance
        >>> 
        >>> # Deterministic value
        >>> sv = StatValue(
        ...     value=0.42,
        ...     uncertainty=Delta(0.0),
        ...     provenance=Provenance("degree", "delta", {})
        ... )
        >>> float(sv)
        0.42
        >>> sv.std()
        0.0
        >>> 
        >>> # With uncertainty
        >>> from py3plex.stats import Gaussian
        >>> sv2 = StatValue(
        ...     value=0.5,
        ...     uncertainty=Gaussian(0.0, 0.05),
        ...     provenance=Provenance("betweenness", "analytic", {})
        ... )
        >>> sv2.ci(0.95)
        (0.402, 0.598)  # Approximately
    """
    
    value: Union[float, int, np.ndarray]
    uncertainty: Uncertainty
    provenance: Provenance
    
    def __post_init__(self):
        """Validate and normalize value."""
        # Ensure value is numeric
        if isinstance(self.value, np.ndarray):
            # Keep as array
            pass
        elif not isinstance(self.value, (int, float, np.number)):
            raise TypeError(f"value must be numeric, got {type(self.value)}")
    
    # Conversion methods for backward compatibility
    
    def __float__(self) -> float:
        """Convert to float (point estimate)."""
        if isinstance(self.value, np.ndarray):
            if self.value.size == 1:
                return float(self.value.item())
            raise ValueError("Cannot convert array StatValue to float")
        return float(self.value)
    
    def __int__(self) -> int:
        """Convert to int (point estimate)."""
        if isinstance(self.value, np.ndarray):
            if self.value.size == 1:
                return int(self.value.item())
            raise ValueError("Cannot convert array StatValue to int")
        return int(self.value)
    
    def __array__(self, dtype=None) -> np.ndarray:
        """Enable numpy array conversion."""
        if isinstance(self.value, np.ndarray):
            return np.asarray(self.value, dtype=dtype)
        return np.asarray([self.value], dtype=dtype)
    
    # Uncertainty query methods
    
    def mean(self) -> Union[float, np.ndarray]:
        """Alias for value (point estimate)."""
        return self.value
    
    def std(self) -> float:
        """Return standard deviation if available."""
        s = self.uncertainty.std()
        return s if s is not None else 0.0
    
    def ci(self, level: float = 0.95) -> tuple:
        """Compute confidence interval.
        
        Args:
            level: Confidence level (default 0.95)
            
        Returns:
            Tuple of (low, high) bounds
        """
        ci_low, ci_high = self.uncertainty.ci(level)
        if isinstance(self.value, np.ndarray):
            # Return absolute bounds
            return (self.value + ci_low, self.value + ci_high)
        return (self.value + ci_low, self.value + ci_high)
    
    def robustness(self) -> float:
        """Compute robustness score.
        
        A stable scalar in [0, 1] indicating confidence.
        Higher values = more robust (less relative uncertainty).
        
        Formula: 1 / (1 + std/|mean|) with careful zero handling.
        
        Returns:
            Robustness score in [0, 1]
        """
        s = self.std()
        v = abs(float(self.value)) if not isinstance(self.value, np.ndarray) else abs(float(np.mean(self.value)))
        
        if v == 0:
            # Avoid division by zero
            if s == 0:
                return 1.0  # Deterministic zero
            else:
                return 0.0  # Uncertain zero
        
        relative_std = s / v
        return 1.0 / (1.0 + relative_std)
    
    # Serialization
    
    def to_json_dict(self) -> dict:
        """Convert to JSON-serializable dictionary.
        
        Returns:
            Dictionary with value, uncertainty, and provenance
        """
        # Handle numpy types
        if isinstance(self.value, np.ndarray):
            value_json = self.value.tolist()
        elif isinstance(self.value, np.number):
            value_json = float(self.value)
        else:
            value_json = self.value
        
        return {
            "value": value_json,
            "uncertainty": self.uncertainty.to_json_dict(),
            "provenance": self.provenance.to_json_dict(),
        }
    
    # Arithmetic operations with uncertainty propagation
    
    def __add__(self, other):
        """Add two StatValues or StatValue + scalar."""
        if isinstance(other, StatValue):
            new_value = self.value + other.value
            new_uncertainty = self.uncertainty.propagate("+", other.uncertainty)
            new_provenance = Provenance(
                algorithm=f"{self.provenance.algorithm}+{other.provenance.algorithm}",
                uncertainty_method="propagated",
                parameters={"op": "+"},
            )
            return StatValue(new_value, new_uncertainty, new_provenance)
        elif isinstance(other, (int, float, np.number)):
            # Adding a scalar doesn't change uncertainty
            new_value = self.value + other
            return StatValue(new_value, self.uncertainty, self.provenance)
        else:
            return NotImplemented
    
    def __radd__(self, other):
        """Right add (scalar + StatValue)."""
        return self.__add__(other)
    
    def __sub__(self, other):
        """Subtract two StatValues or StatValue - scalar."""
        if isinstance(other, StatValue):
            new_value = self.value - other.value
            new_uncertainty = self.uncertainty.propagate("-", other.uncertainty)
            new_provenance = Provenance(
                algorithm=f"{self.provenance.algorithm}-{other.provenance.algorithm}",
                uncertainty_method="propagated",
                parameters={"op": "-"},
            )
            return StatValue(new_value, new_uncertainty, new_provenance)
        elif isinstance(other, (int, float, np.number)):
            new_value = self.value - other
            return StatValue(new_value, self.uncertainty, self.provenance)
        else:
            return NotImplemented
    
    def __rsub__(self, other):
        """Right subtract (scalar - StatValue)."""
        if isinstance(other, (int, float, np.number)):
            new_value = other - self.value
            # Negation of uncertainty
            new_uncertainty = self.uncertainty.propagate("neg", None)
            return StatValue(new_value, new_uncertainty, self.provenance)
        return NotImplemented
    
    def __mul__(self, other):
        """Multiply two StatValues or StatValue * scalar."""
        if isinstance(other, StatValue):
            new_value = self.value * other.value
            new_uncertainty = self.uncertainty.propagate("*", other.uncertainty)
            new_provenance = Provenance(
                algorithm=f"{self.provenance.algorithm}*{other.provenance.algorithm}",
                uncertainty_method="propagated",
                parameters={"op": "*"},
            )
            return StatValue(new_value, new_uncertainty, new_provenance)
        elif isinstance(other, (int, float, np.number)):
            # Scaling: multiply value and scale uncertainty proportionally
            new_value = self.value * other
            new_uncertainty = _scale_uncertainty(self.uncertainty, float(other))
            return StatValue(new_value, new_uncertainty, self.provenance)
        else:
            return NotImplemented
    
    def __rmul__(self, other):
        """Right multiply (scalar * StatValue)."""
        return self.__mul__(other)
    
    def __truediv__(self, other):
        """Divide two StatValues or StatValue / scalar."""
        if isinstance(other, StatValue):
            new_value = self.value / other.value
            new_uncertainty = self.uncertainty.propagate("/", other.uncertainty)
            new_provenance = Provenance(
                algorithm=f"{self.provenance.algorithm}/{other.provenance.algorithm}",
                uncertainty_method="propagated",
                parameters={"op": "/"},
            )
            return StatValue(new_value, new_uncertainty, new_provenance)
        elif isinstance(other, (int, float, np.number)):
            if other == 0:
                raise ZeroDivisionError("Cannot divide by zero")
            new_value = self.value / other
            new_uncertainty = _scale_uncertainty(self.uncertainty, 1.0 / float(other))
            return StatValue(new_value, new_uncertainty, self.provenance)
        else:
            return NotImplemented
    
    def __rtruediv__(self, other):
        """Right divide (scalar / StatValue)."""
        if isinstance(other, (int, float, np.number)):
            new_value = other / self.value
            # This is complex - fall back to propagation with scalar as Delta(0)
            scalar_unc = Delta(0.0)
            new_uncertainty = scalar_unc.propagate("/", self.uncertainty)
            return StatValue(new_value, new_uncertainty, self.provenance)
        return NotImplemented
    
    def __pow__(self, other):
        """Power: StatValue ** other."""
        if isinstance(other, StatValue):
            new_value = self.value ** other.value
            new_uncertainty = self.uncertainty.propagate("**", other.uncertainty)
            new_provenance = Provenance(
                algorithm=f"{self.provenance.algorithm}**{other.provenance.algorithm}",
                uncertainty_method="propagated",
                parameters={"op": "**"},
            )
            return StatValue(new_value, new_uncertainty, new_provenance)
        elif isinstance(other, (int, float, np.number)):
            new_value = self.value ** other
            # For power with constant exponent, propagation is complex
            # Fall back to treating exponent as Delta(0)
            exponent_unc = Delta(0.0)
            new_uncertainty = self.uncertainty.propagate("**", exponent_unc)
            return StatValue(new_value, new_uncertainty, self.provenance)
        else:
            return NotImplemented
    
    def __neg__(self):
        """Unary negation."""
        new_value = -self.value
        new_uncertainty = self.uncertainty.propagate("neg", None)
        return StatValue(new_value, new_uncertainty, self.provenance)
    
    def __repr__(self) -> str:
        """String representation."""
        if self.std() == 0:
            return f"StatValue({self.value})"
        else:
            return f"StatValue({self.value} ± {self.std():.3g})"
