"""Uncertainty models for statistics.

This module provides base and concrete uncertainty models that can be attached
to StatValue objects. Each model supports sampling, CI computation, and
propagation through arithmetic operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np


class Uncertainty(ABC):
    """Base class for uncertainty models.
    
    All uncertainty models must support:
    - summary(): Dict with std, ci, and other info
    - sample(): Generate random samples
    - ci(): Compute confidence intervals
    - std(): Return standard deviation (if available)
    - propagate(): Combine uncertainties through operations
    """
    
    @abstractmethod
    def summary(self, level: float = 0.95) -> dict:
        """Get summary statistics for this uncertainty.
        
        Args:
            level: Confidence level for intervals
            
        Returns:
            Dictionary with 'type', 'std', 'ci', and other model-specific info
        """
        pass
    
    @abstractmethod
    def sample(self, n: int, *, seed: Optional[int] = None) -> np.ndarray:
        """Generate random samples from this uncertainty distribution.
        
        Args:
            n: Number of samples
            seed: Random seed for reproducibility
            
        Returns:
            Array of samples, shape (n,)
        """
        pass
    
    @abstractmethod
    def ci(self, level: float = 0.95) -> Tuple[float, float]:
        """Compute confidence interval.
        
        Args:
            level: Confidence level (e.g., 0.95 for 95% CI)
            
        Returns:
            Tuple of (low, high) bounds
        """
        pass
    
    @abstractmethod
    def std(self) -> Optional[float]:
        """Return standard deviation if available.
        
        Returns:
            Standard deviation or None if not applicable
        """
        pass
    
    @abstractmethod
    def propagate(self, op: str, other: Optional["Uncertainty"], *, seed: Optional[int] = None) -> "Uncertainty":
        """Propagate uncertainty through an operation.
        
        Args:
            op: Operation name ("+", "-", "*", "/", "**", "neg")
            other: Other uncertainty (None for unary ops)
            seed: Random seed for Monte Carlo propagation
            
        Returns:
            New Uncertainty representing the result
        """
        pass
    
    @abstractmethod
    def to_json_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        pass


@dataclass(frozen=True)
class Delta(Uncertainty):
    """Deterministic uncertainty model (Dirac delta).
    
    Represents a value with known precision or zero uncertainty.
    
    Attributes:
        sigma: Standard deviation (typically 0 for deterministic)
    
    Examples:
        >>> d = Delta(0.0)  # Perfect certainty
        >>> d.std()
        0.0
        >>> d.ci()
        (0.0, 0.0)
        >>> d2 = Delta(0.01)  # Small known error
        >>> d2.std()
        0.01
    """
    
    sigma: float = 0.0
    
    def summary(self, level: float = 0.95) -> dict:
        return {
            "type": "delta",
            "std": self.sigma,
            "ci": self.ci(level),
        }
    
    def sample(self, n: int, *, seed: Optional[int] = None) -> np.ndarray:
        """Generate samples for this uncertainty.

        For sigma == 0, this is deterministic (all zeros).
        For sigma > 0, we treat sigma as a standard deviation and sample
        zero-mean Gaussian noise. This ensures Monte Carlo propagation
        correctly reflects non-zero Delta uncertainty when combined with
        non-Delta models.
        """
        if self.sigma == 0:
            return np.full(n, 0.0)
        rng = np.random.default_rng(seed)
        return rng.normal(0.0, self.sigma, size=n)
    
    def ci(self, level: float = 0.95) -> Tuple[float, float]:
        """Return zero-width interval."""
        # For Delta, CI is centered at 0 with width based on sigma
        # For sigma=0, this is (0, 0)
        # For small sigma, we can use Gaussian-like bounds
        if self.sigma == 0:
            return (0.0, 0.0)
        # Use 1.96 * sigma for 95% CI (approximate)
        z = 1.96 if level == 0.95 else 2.576 if level == 0.99 else 1.645 if level == 0.90 else 1.96
        half_width = z * self.sigma
        return (-half_width, half_width)
    
    def std(self) -> Optional[float]:
        return self.sigma
    
    def propagate(self, op: str, other: Optional["Uncertainty"], *, seed: Optional[int] = None) -> "Uncertainty":
        """Propagate deterministic uncertainty.
        
        For Delta models, we use simple error propagation rules when both are Delta.
        """
        if other is None:
            # Unary operation
            if op == "neg":
                return Delta(self.sigma)
            else:
                return Delta(self.sigma)
        
        if isinstance(other, Delta):
            # Both deterministic - use standard error propagation
            if op == "+":
                # σ_sum = sqrt(σ1² + σ2²)
                return Delta(np.sqrt(self.sigma**2 + other.sigma**2))
            elif op == "-":
                return Delta(np.sqrt(self.sigma**2 + other.sigma**2))
            elif op in ("*", "/", "**"):
                # For multiplication/division, we'd need the actual values
                # to compute relative errors. Fall back to conservative estimate.
                return Delta(np.sqrt(self.sigma**2 + other.sigma**2))
        
        # Fallback: if other is not Delta, fall back to MC
        return _mc_propagate(self, op, other, seed=seed)
    
    def to_json_dict(self) -> dict:
        return {
            "type": "delta",
            "sigma": self.sigma,
        }


@dataclass(frozen=True)
class Gaussian(Uncertainty):
    """Gaussian (Normal) uncertainty model.
    
    Represents a value with normally distributed uncertainty.
    
    Attributes:
        mean: Mean of the distribution (relative to value, usually 0)
        std: Standard deviation
    
    Examples:
        >>> g = Gaussian(mean=0.0, std=0.1)
        >>> g.std()
        0.1
        >>> g.ci(0.95)
        (-0.196, 0.196)  # Approximately ±1.96*std
    """
    
    mean: float
    std_dev: float
    
    def summary(self, level: float = 0.95) -> dict:
        return {
            "type": "gaussian",
            "mean": self.mean,
            "std": self.std_dev,
            "ci": self.ci(level),
        }
    
    def sample(self, n: int, *, seed: Optional[int] = None) -> np.ndarray:
        """Generate Gaussian samples."""
        rng = np.random.default_rng(seed)
        return rng.normal(self.mean, self.std_dev, size=n)
    
    def ci(self, level: float = 0.95) -> Tuple[float, float]:
        """Compute exact Gaussian CI."""
        # Use z-scores for common levels
        if level == 0.95:
            z = 1.96
        elif level == 0.99:
            z = 2.576
        elif level == 0.90:
            z = 1.645
        else:
            # Approximate using percentile
            from scipy import stats
            z = stats.norm.ppf((1 + level) / 2)
        
        low = self.mean - z * self.std_dev
        high = self.mean + z * self.std_dev
        return (low, high)
    
    def std(self) -> Optional[float]:
        return self.std_dev
    
    def propagate(self, op: str, other: Optional["Uncertainty"], *, seed: Optional[int] = None) -> "Uncertainty":
        """Propagate Gaussian uncertainty analytically where possible."""
        if other is None:
            # Unary operation
            if op == "neg":
                return Gaussian(-self.mean, self.std_dev)
            else:
                return Gaussian(self.mean, self.std_dev)
        
        if isinstance(other, Gaussian):
            # Both Gaussian - use exact error propagation
            if op == "+":
                new_mean = self.mean + other.mean
                new_std = np.sqrt(self.std_dev**2 + other.std_dev**2)
                return Gaussian(new_mean, new_std)
            elif op == "-":
                new_mean = self.mean - other.mean
                new_std = np.sqrt(self.std_dev**2 + other.std_dev**2)
                return Gaussian(new_mean, new_std)
            elif op == "*":
                # For multiplication, assuming independence and small relative errors
                # σ_product ≈ |x*y| * sqrt((σ_x/x)² + (σ_y/y)²)
                # But we don't have x, y here, so we approximate
                # or fall back to MC
                return _mc_propagate(self, op, other, seed=seed)
            elif op in ("/", "**"):
                # Fall back to MC for complex operations
                return _mc_propagate(self, op, other, seed=seed)
        
        # Fallback to MC
        return _mc_propagate(self, op, other, seed=seed)
    
    def to_json_dict(self) -> dict:
        return {
            "type": "gaussian",
            "mean": self.mean,
            "std": self.std_dev,
        }


@dataclass(frozen=True)
class Bootstrap(Uncertainty):
    """Bootstrap-based uncertainty model.
    
    Stores bootstrap samples and computes statistics from them.
    
    Attributes:
        samples: Array of bootstrap sample values (relative to point estimate)
    
    Examples:
        >>> samples = np.array([0.1, -0.05, 0.15, 0.0, 0.08])
        >>> b = Bootstrap(samples)
        >>> b.std()
        0.0707...  # Sample std
        >>> b.ci(0.95)
        (-0.05, 0.15)  # Percentile-based CI
    """
    
    samples: np.ndarray
    
    def __post_init__(self):
        """Validate samples."""
        if not isinstance(self.samples, np.ndarray):
            # Use object.__setattr__ since this is a frozen dataclass
            object.__setattr__(self, 'samples', np.asarray(self.samples))
    
    def summary(self, level: float = 0.95) -> dict:
        return {
            "type": "bootstrap",
            "n": len(self.samples),
            "mean": float(np.mean(self.samples)),
            "std": float(np.std(self.samples, ddof=1)),
            "ci": self.ci(level),
            "method": "percentile",
        }
    
    def sample(self, n: int, *, seed: Optional[int] = None) -> np.ndarray:
        """Resample from stored bootstrap samples."""
        rng = np.random.default_rng(seed)
        return rng.choice(self.samples, size=n, replace=True)
    
    def ci(self, level: float = 0.95) -> Tuple[float, float]:
        """Compute CI using percentile method."""
        alpha = 1 - level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        low = float(np.percentile(self.samples, lower_percentile))
        high = float(np.percentile(self.samples, upper_percentile))
        return (low, high)
    
    def std(self) -> Optional[float]:
        """Compute sample standard deviation."""
        if len(self.samples) < 2:
            return 0.0
        return float(np.std(self.samples, ddof=1))
    
    def propagate(self, op: str, other: Optional["Uncertainty"], *, seed: Optional[int] = None) -> "Uncertainty":
        """Propagate via Monte Carlo."""
        return _mc_propagate(self, op, other, seed=seed)
    
    def to_json_dict(self) -> dict:
        """Serialize without full sample array to keep size manageable."""
        return {
            "type": "bootstrap",
            "n": len(self.samples),
            "std": float(np.std(self.samples, ddof=1)) if len(self.samples) > 1 else 0.0,
            "ci95": list(self.ci(0.95)),
        }


@dataclass(frozen=True)
class Empirical(Uncertainty):
    """Empirical uncertainty from arbitrary samples.
    
    Similar to Bootstrap but conceptually represents samples from any
    empirical distribution (not necessarily bootstrap resampling).
    
    Attributes:
        samples: Array of sample values (relative to point estimate)
    """
    
    samples: np.ndarray
    
    def __post_init__(self):
        """Validate samples."""
        if not isinstance(self.samples, np.ndarray):
            object.__setattr__(self, 'samples', np.asarray(self.samples))
    
    def summary(self, level: float = 0.95) -> dict:
        return {
            "type": "empirical",
            "n": len(self.samples),
            "mean": float(np.mean(self.samples)),
            "std": float(np.std(self.samples, ddof=1)),
            "ci": self.ci(level),
        }
    
    def sample(self, n: int, *, seed: Optional[int] = None) -> np.ndarray:
        """Resample from stored samples."""
        rng = np.random.default_rng(seed)
        return rng.choice(self.samples, size=n, replace=True)
    
    def ci(self, level: float = 0.95) -> Tuple[float, float]:
        """Compute CI using percentiles."""
        alpha = 1 - level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        low = float(np.percentile(self.samples, lower_percentile))
        high = float(np.percentile(self.samples, upper_percentile))
        return (low, high)
    
    def std(self) -> Optional[float]:
        """Compute sample standard deviation."""
        if len(self.samples) < 2:
            return 0.0
        return float(np.std(self.samples, ddof=1))
    
    def propagate(self, op: str, other: Optional["Uncertainty"], *, seed: Optional[int] = None) -> "Uncertainty":
        """Propagate via Monte Carlo."""
        return _mc_propagate(self, op, other, seed=seed)
    
    def to_json_dict(self) -> dict:
        """Serialize without full sample array."""
        return {
            "type": "empirical",
            "n": len(self.samples),
            "std": float(np.std(self.samples, ddof=1)) if len(self.samples) > 1 else 0.0,
            "ci95": list(self.ci(0.95)),
        }


@dataclass(frozen=True)
class Interval(Uncertainty):
    """Interval-based uncertainty model.
    
    Represents uncertainty as a range [low, high] without assuming a
    specific distribution.
    
    Attributes:
        low: Lower bound (relative to point estimate)
        high: Upper bound (relative to point estimate)
    
    Examples:
        >>> i = Interval(-0.1, 0.15)
        >>> i.ci()
        (-0.1, 0.15)
        >>> i.sample(5)  # Uniform sampling by default
        array([...])
    """
    
    low: float
    high: float
    
    def summary(self, level: float = 0.95) -> dict:
        return {
            "type": "interval",
            "low": self.low,
            "high": self.high,
            "std": self.std(),
            "ci": self.ci(level),
        }
    
    def sample(self, n: int, *, seed: Optional[int] = None) -> np.ndarray:
        """Sample uniformly from interval."""
        rng = np.random.default_rng(seed)
        return rng.uniform(self.low, self.high, size=n)
    
    def ci(self, level: float = 0.95) -> Tuple[float, float]:
        """Return the interval bounds."""
        # For interval model, the CI is just the interval itself
        return (self.low, self.high)
    
    def std(self) -> Optional[float]:
        """Estimate std assuming uniform distribution."""
        # For uniform distribution on [a, b], std = (b - a) / sqrt(12)
        return (self.high - self.low) / np.sqrt(12)
    
    def propagate(self, op: str, other: Optional["Uncertainty"], *, seed: Optional[int] = None) -> "Uncertainty":
        """Propagate via Monte Carlo."""
        return _mc_propagate(self, op, other, seed=seed)
    
    def to_json_dict(self) -> dict:
        return {
            "type": "interval",
            "low": self.low,
            "high": self.high,
        }


def _mc_propagate(unc1: Uncertainty, op: str, unc2: Optional[Uncertainty], *, seed: Optional[int] = None, n_samples: int = 4096) -> Uncertainty:
    """Monte Carlo propagation fallback.
    
    Args:
        unc1: First uncertainty
        op: Operation ("+", "-", "*", "/", "**", "neg")
        unc2: Second uncertainty (None for unary ops)
        seed: Random seed
        n_samples: Number of MC samples
        
    Returns:
        Empirical uncertainty from MC samples
    """
    rng = np.random.default_rng(seed)
    
    # Generate samples from first uncertainty
    samples1 = unc1.sample(n_samples, seed=int(rng.integers(0, 2**31)))
    
    if unc2 is None:
        # Unary operation
        if op == "neg":
            result_samples = -samples1
        else:
            result_samples = samples1
    else:
        # Binary operation
        samples2 = unc2.sample(n_samples, seed=int(rng.integers(0, 2**31)))
        
        if op == "+":
            result_samples = samples1 + samples2
        elif op == "-":
            result_samples = samples1 - samples2
        elif op == "*":
            result_samples = samples1 * samples2
        elif op == "/":
            # Guard against division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                result_samples = samples1 / samples2
                result_samples = result_samples[np.isfinite(result_samples)]
        elif op == "**":
            # Guard against invalid operations
            with np.errstate(over='ignore', under='ignore', invalid='ignore'):
                result_samples = samples1 ** samples2
                result_samples = result_samples[np.isfinite(result_samples)]
        else:
            raise ValueError(f"Unknown operation: {op}")
    
    # Filter out NaN/inf
    result_samples = result_samples[np.isfinite(result_samples)]
    
    if len(result_samples) == 0:
        # All samples were invalid - return Delta(0)
        return Delta(0.0)
    
    return Empirical(result_samples)
