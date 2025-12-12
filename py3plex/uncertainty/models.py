"""Core uncertainty value models.

This module defines UncertainValue, a unified way to represent statistics
that may be deterministic or uncertain. It complements the existing StatSeries
by providing a low-level primitive for individual values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class UncertainValue:
    """A single value with optional uncertainty information.

    This is the fundamental building block for uncertainty-native computation.
    Unlike StatSeries (which represents arrays of values), UncertainValue
    represents a single scalar that can be deterministic or uncertain.

    Parameters
    ----------
    kind : str
        The type of distribution. Supported kinds:
        - "deterministic": A fixed value (no uncertainty)
        - "bernoulli": Bernoulli distribution (binary: 0 or 1)
        - "normal": Normal/Gaussian distribution
        - "empirical": Empirical distribution from samples
    params : dict
        Distribution parameters. Required keys depend on kind:
        - "deterministic": {"value": float}
        - "bernoulli": {"p": float}  # probability of 1
        - "normal": {"mu": float, "sigma": float}
        - "empirical": {"samples": array-like}

    Examples
    --------
    >>> # Deterministic value
    >>> v = UncertainValue(kind="deterministic", params={"value": 1.0})
    >>> v.mean()
    1.0
    >>> v.var()
    0.0
    >>> v.is_deterministic()
    True

    >>> # Normal distribution
    >>> v = UncertainValue(kind="normal", params={"mu": 5.0, "sigma": 1.0})
    >>> v.mean()
    5.0
    >>> v.var()
    1.0
    >>> samples = v.sample(np.random.default_rng(42), n=100)
    >>> len(samples)
    100

    >>> # Bernoulli (e.g., for edge existence probability)
    >>> v = UncertainValue(kind="bernoulli", params={"p": 0.8})
    >>> v.mean()
    0.8
    >>> v.var()
    0.16
    """

    kind: str
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate kind and params."""
        valid_kinds = {"deterministic", "bernoulli", "normal", "empirical"}
        if self.kind not in valid_kinds:
            raise ValueError(
                f"Invalid kind '{self.kind}'. Must be one of {valid_kinds}"
            )

        # Validate required params for each kind
        if self.kind == "deterministic":
            if "value" not in self.params:
                raise ValueError("deterministic requires 'value' in params")
        elif self.kind == "bernoulli":
            if "p" not in self.params:
                raise ValueError("bernoulli requires 'p' in params")
            p = self.params["p"]
            if not 0 <= p <= 1:
                raise ValueError(f"bernoulli p must be in [0, 1], got {p}")
        elif self.kind == "normal":
            if "mu" not in self.params or "sigma" not in self.params:
                raise ValueError("normal requires 'mu' and 'sigma' in params")
            if self.params["sigma"] < 0:
                raise ValueError(f"normal sigma must be >= 0, got {self.params['sigma']}")
        elif self.kind == "empirical":
            if "samples" not in self.params:
                raise ValueError("empirical requires 'samples' in params")
            # Convert to numpy array if not already
            if not isinstance(self.params["samples"], np.ndarray):
                self.params["samples"] = np.asarray(self.params["samples"])

    def mean(self) -> float:
        """Compute the mean (expected value) of this distribution.

        Returns
        -------
        float
            The expected value.
        """
        if self.kind == "deterministic":
            return float(self.params["value"])
        elif self.kind == "bernoulli":
            return float(self.params["p"])
        elif self.kind == "normal":
            return float(self.params["mu"])
        elif self.kind == "empirical":
            return float(np.mean(self.params["samples"]))
        else:
            raise NotImplementedError(f"mean() not implemented for kind={self.kind}")

    def var(self) -> float:
        """Compute the variance of this distribution.

        Returns
        -------
        float
            The variance. Returns 0.0 for deterministic values.
        """
        if self.kind == "deterministic":
            return 0.0
        elif self.kind == "bernoulli":
            p = self.params["p"]
            return float(p * (1 - p))
        elif self.kind == "normal":
            sigma = self.params["sigma"]
            return float(sigma ** 2)
        elif self.kind == "empirical":
            return float(np.var(self.params["samples"]))
        else:
            raise NotImplementedError(f"var() not implemented for kind={self.kind}")

    def std(self) -> float:
        """Compute the standard deviation of this distribution.

        Returns
        -------
        float
            The standard deviation.
        """
        return float(np.sqrt(self.var()))

    def sample(self, rng: np.random.Generator, n: int = 1) -> np.ndarray:
        """Draw samples from this distribution.

        Parameters
        ----------
        rng : np.random.Generator
            Numpy random generator instance.
        n : int, default=1
            Number of samples to draw.

        Returns
        -------
        np.ndarray
            Array of shape (n,) containing samples.

        Examples
        --------
        >>> rng = np.random.default_rng(42)
        >>> v = UncertainValue(kind="normal", params={"mu": 0.0, "sigma": 1.0})
        >>> samples = v.sample(rng, n=5)
        >>> samples.shape
        (5,)
        """
        if self.kind == "deterministic":
            return np.full(n, self.params["value"])
        elif self.kind == "bernoulli":
            return rng.binomial(1, self.params["p"], size=n).astype(float)
        elif self.kind == "normal":
            return rng.normal(self.params["mu"], self.params["sigma"], size=n)
        elif self.kind == "empirical":
            samples = self.params["samples"]
            # Resample with replacement
            indices = rng.choice(len(samples), size=n, replace=True)
            return samples[indices]
        else:
            raise NotImplementedError(f"sample() not implemented for kind={self.kind}")

    def is_deterministic(self) -> bool:
        """Check if this value is deterministic (no uncertainty).

        Returns
        -------
        bool
            True if deterministic, False otherwise.
        """
        return self.kind == "deterministic" or self.var() == 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serializable dictionary.

        Returns
        -------
        dict
            Dictionary with 'kind' and 'params' keys.
        """
        params = dict(self.params)
        # Convert numpy arrays to lists for JSON serialization
        if self.kind == "empirical" and "samples" in params:
            params["samples"] = params["samples"].tolist()
        return {"kind": self.kind, "params": params}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UncertainValue:
        """Create an UncertainValue from a dictionary.

        Parameters
        ----------
        data : dict
            Dictionary with 'kind' and 'params' keys.

        Returns
        -------
        UncertainValue
            The reconstructed uncertain value.
        """
        return cls(kind=data["kind"], params=data["params"])

    @classmethod
    def from_value(cls, value: float | int | UncertainValue) -> UncertainValue:
        """Create an UncertainValue from a scalar or existing UncertainValue.

        This is a convenience method for accepting either deterministic or
        uncertain values in algorithms.

        Parameters
        ----------
        value : float, int, or UncertainValue
            The value to wrap.

        Returns
        -------
        UncertainValue
            If value is already UncertainValue, returns it unchanged.
            Otherwise, wraps it as a deterministic value.

        Examples
        --------
        >>> v1 = UncertainValue.from_value(1.0)
        >>> v1.kind
        'deterministic'
        >>> v1.mean()
        1.0

        >>> v2 = UncertainValue(kind="normal", params={"mu": 1.0, "sigma": 0.1})
        >>> v3 = UncertainValue.from_value(v2)
        >>> v3 is v2
        True
        """
        if isinstance(value, UncertainValue):
            return value
        return cls(kind="deterministic", params={"value": float(value)})

    def __float__(self) -> float:
        """Convert to float - returns the mean value.

        This enables backward compatibility with code expecting floats.
        """
        return self.mean()

    def __repr__(self) -> str:
        """String representation."""
        if self.kind == "deterministic":
            return f"UncertainValue({self.params['value']})"
        elif self.kind == "bernoulli":
            return f"UncertainValue(Bernoulli(p={self.params['p']}))"
        elif self.kind == "normal":
            mu, sigma = self.params["mu"], self.params["sigma"]
            return f"UncertainValue(Normal(μ={mu}, σ={sigma}))"
        elif self.kind == "empirical":
            n = len(self.params["samples"])
            return f"UncertainValue(Empirical(n={n}))"
        return f"UncertainValue(kind={self.kind}, params={self.params})"
