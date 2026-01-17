"""Distribution type for UQ-aware Graph Programs.

This module implements Distribution as a first-class type for uncertainty
quantification results, with proper propagation semantics.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import numpy as np


class UQMode(Enum):
    """Uncertainty quantification modes."""
    SEED = "seed"  # Multiple runs with different seeds
    BOOTSTRAP = "bootstrap"  # Bootstrap resampling
    PERTURBATION = "perturbation"  # Edge/node perturbations
    STRATIFIED_PERTURBATION = "stratified_perturbation"  # Layer-aware perturbations
    NULL_MODEL = "null_model"  # Comparison against null models


@dataclass
class UQMetadata:
    """Metadata for uncertainty quantification."""
    mode: UQMode
    n_samples: int
    seed: Optional[int] = None
    ci_level: float = 0.95
    bootstrap_unit: Optional[str] = None  # "edges", "nodes", "layers"
    bootstrap_mode: Optional[str] = None  # "resample", "permute"
    perturbation_rate: Optional[float] = None
    null_model_type: Optional[str] = None
    method_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Distribution:
    """Distribution type for UQ results.
    
    Represents uncertainty-quantified values with mean, std, quantiles,
    and optional sample data.
    
    Attributes:
        mean: Point estimate (mean of samples)
        std: Standard deviation
        quantiles: Dictionary of quantile -> value
        samples: Optional list of individual sample values
        metadata: UQ method metadata
        certainty: Confidence score (0-1)
    
    Example:
        >>> dist = Distribution(
        ...     mean=0.5,
        ...     std=0.1,
        ...     quantiles={0.025: 0.3, 0.5: 0.5, 0.975: 0.7},
        ...     metadata=UQMetadata(mode=UQMode.BOOTSTRAP, n_samples=100)
        ... )
        >>> dist.ci(0.95)
        (0.3, 0.7)
    """
    mean: float
    std: float
    quantiles: Dict[float, float]
    samples: Optional[List[float]] = None
    metadata: Optional[UQMetadata] = None
    certainty: float = 1.0
    
    def ci(self, level: float = 0.95) -> tuple[float, float]:
        """Get confidence interval at specified level.
        
        Args:
            level: Confidence level (default: 0.95)
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        alpha = (1 - level) / 2
        lower_q = alpha
        upper_q = 1 - alpha
        
        # Find closest quantiles
        lower = self.quantiles.get(lower_q)
        upper = self.quantiles.get(upper_q)
        
        if lower is None or upper is None:
            # Fallback to mean +/- z * std
            z = 1.96 if level == 0.95 else 2.576 if level == 0.99 else 1.645
            lower = self.mean - z * self.std
            upper = self.mean + z * self.std
            
        return (lower, upper)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "mean": self.mean,
            "std": self.std,
            "quantiles": self.quantiles,
            "samples": self.samples,
            "metadata": {
                "mode": self.metadata.mode.value if self.metadata else None,
                "n_samples": self.metadata.n_samples if self.metadata else None,
                "seed": self.metadata.seed if self.metadata else None,
                "ci_level": self.metadata.ci_level if self.metadata else 0.95,
            } if self.metadata else None,
            "certainty": self.certainty,
        }
    
    @classmethod
    def from_samples(
        cls,
        samples: List[float],
        metadata: Optional[UQMetadata] = None,
        quantile_levels: Optional[List[float]] = None
    ) -> "Distribution":
        """Create Distribution from sample values.
        
        Args:
            samples: List of sample values
            metadata: UQ metadata
            quantile_levels: Quantile levels to compute (default: [0.025, 0.05, 0.5, 0.95, 0.975])
            
        Returns:
            Distribution object
        """
        if quantile_levels is None:
            quantile_levels = [0.025, 0.05, 0.5, 0.95, 0.975]
        
        arr = np.array(samples)
        quantiles = {q: float(np.quantile(arr, q)) for q in quantile_levels}
        
        return cls(
            mean=float(np.mean(arr)),
            std=float(np.std(arr)),
            quantiles=quantiles,
            samples=samples,
            metadata=metadata,
            certainty=1.0 if len(samples) >= 30 else len(samples) / 30.0
        )
    
    def __repr__(self) -> str:
        ci_low, ci_high = self.ci(0.95)
        return f"Distribution(mean={self.mean:.4f}, std={self.std:.4f}, CI=[{ci_low:.4f}, {ci_high:.4f}])"


def propagate_distribution(
    values: List[Union[float, Distribution]],
    operation: str
) -> Union[float, Distribution]:
    """Propagate distributions through operations.
    
    Args:
        values: List of values (floats or Distributions)
        operation: Operation name ("mean", "sum", "max", "min")
        
    Returns:
        Float if all inputs are floats, Distribution if any input is Distribution
    """
    # Check if any value is a Distribution
    has_dist = any(isinstance(v, Distribution) for v in values)
    
    if not has_dist:
        # All deterministic - apply operation directly
        if operation == "mean":
            return float(np.mean(values))
        elif operation == "sum":
            return float(np.sum(values))
        elif operation == "max":
            return float(np.max(values))
        elif operation == "min":
            return float(np.min(values))
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    # Extract samples or use mean
    all_samples = []
    for v in values:
        if isinstance(v, Distribution):
            if v.samples:
                all_samples.append(v.samples)
            else:
                # Use mean as single sample
                all_samples.append([v.mean])
        else:
            all_samples.append([float(v)])
    
    # Align sample counts (use minimum)
    min_samples = min(len(s) for s in all_samples)
    aligned = [s[:min_samples] for s in all_samples]
    
    # Apply operation across samples
    result_samples = []
    for i in range(min_samples):
        sample_values = [s[i] for s in aligned]
        if operation == "mean":
            result_samples.append(np.mean(sample_values))
        elif operation == "sum":
            result_samples.append(np.sum(sample_values))
        elif operation == "max":
            result_samples.append(np.max(sample_values))
        elif operation == "min":
            result_samples.append(np.min(sample_values))
    
    # Get metadata from first Distribution
    metadata = None
    for v in values:
        if isinstance(v, Distribution) and v.metadata:
            metadata = v.metadata
            break
    
    return Distribution.from_samples(result_samples, metadata=metadata)
