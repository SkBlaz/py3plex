"""Core statistic types for first-class uncertainty representation.

This module defines the fundamental types that wrap statistics with optional
uncertainty information (standard deviations, confidence intervals, quantiles).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np


class ResamplingStrategy(Enum):
    """Strategy for estimating uncertainty via resampling.
    
    Attributes
    ----------
    SEED : str
        Run with different random seeds (Monte Carlo).
    BOOTSTRAP : str
        Bootstrap resampling of nodes or edges.
    JACKKNIFE : str
        Leave-one-out jackknife resampling.
    PERTURBATION : str
        Add noise/perturbations to network structure or parameters.
    """
    SEED = "seed"
    BOOTSTRAP = "bootstrap"
    JACKKNIFE = "jackknife"
    PERTURBATION = "perturbation"


class UncertaintyMode(Enum):
    """Global mode for uncertainty computation.
    
    Attributes
    ----------
    OFF : str
        Always deterministic, std=None.
    ON : str
        Try to compute uncertainty when supported.
    AUTO : str
        Only do it if explicitly requested by a function.
    """
    OFF = "off"
    ON = "on"
    AUTO = "auto"


@dataclass
class UncertaintyConfig:
    """Configuration for uncertainty estimation.
    
    Attributes
    ----------
    mode : UncertaintyMode
        The current uncertainty mode.
    default_n_runs : int
        Default number of runs for uncertainty estimation.
    default_resampling : ResamplingStrategy
        Default resampling strategy.
    """
    mode: UncertaintyMode = UncertaintyMode.OFF
    default_n_runs: int = 50
    default_resampling: ResamplingStrategy = ResamplingStrategy.SEED


@dataclass
class StatSeries:
    """A series of statistics with optional uncertainty information.
    
    This is the canonical result type for statistics that return a value per
    node, time point, or other index.
    
    In deterministic mode (uncertainty=False):
    - mean contains the single-run values
    - std = None
    - quantiles = None
    - certainty = 1.0
    
    In uncertain mode (uncertainty=True):
    - mean contains the average across runs
    - std contains the standard deviation
    - quantiles contains percentile arrays (e.g., {0.025: arr, 0.975: arr})
    - certainty < 1.0
    
    Parameters
    ----------
    index : list[Any]
        The index labels (e.g., node IDs, time points).
    mean : np.ndarray
        The mean values, shape (n,).
    std : np.ndarray or None
        The standard deviations, shape (n,), or None if deterministic.
    quantiles : dict[float, np.ndarray] or None
        Quantile arrays, e.g., {0.025: (n,), 0.975: (n,)}, or None.
    meta : dict[str, Any]
        Optional metadata (e.g., algorithm parameters, run info).
    
    Examples
    --------
    >>> import numpy as np
    >>> # Deterministic
    >>> s = StatSeries(
    ...     index=['a', 'b', 'c'],
    ...     mean=np.array([1.0, 2.0, 3.0])
    ... )
    >>> s.is_deterministic
    True
    >>> s.certainty
    1.0
    >>> np.array(s)
    array([1., 2., 3.])
    
    >>> # With uncertainty
    >>> s_unc = StatSeries(
    ...     index=['a', 'b', 'c'],
    ...     mean=np.array([1.0, 2.0, 3.0]),
    ...     std=np.array([0.1, 0.2, 0.15]),
    ...     quantiles={0.025: np.array([0.8, 1.6, 2.7]), 
    ...                0.975: np.array([1.2, 2.4, 3.3])}
    ... )
    >>> s_unc.is_deterministic
    False
    >>> s_unc.certainty
    0.0
    """
    
    index: List[Any]
    mean: np.ndarray
    std: Optional[np.ndarray] = None
    quantiles: Optional[Dict[float, np.ndarray]] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and convert arrays."""
        # Convert mean to numpy array if needed
        if not isinstance(self.mean, np.ndarray):
            self.mean = np.asarray(self.mean, dtype=float)
        
        # Convert std if present
        if self.std is not None and not isinstance(self.std, np.ndarray):
            self.std = np.asarray(self.std, dtype=float)
        
        # Convert quantile arrays if present
        if self.quantiles is not None:
            self.quantiles = {
                k: np.asarray(v, dtype=float) if not isinstance(v, np.ndarray) else v
                for k, v in self.quantiles.items()
            }
        
        # Validate shapes
        n = len(self.index)
        if len(self.mean) != n:
            raise ValueError(f"mean length {len(self.mean)} != index length {n}")
        
        if self.std is not None and len(self.std) != n:
            raise ValueError(f"std length {len(self.std)} != index length {n}")
        
        if self.quantiles is not None:
            for q, arr in self.quantiles.items():
                if len(arr) != n:
                    raise ValueError(
                        f"quantile {q} length {len(arr)} != index length {n}"
                    )
    
    @property
    def is_deterministic(self) -> bool:
        """Return True if this is a deterministic result (no uncertainty)."""
        return self.std is None or np.all(self.std == 0)
    
    @property
    def certainty(self) -> float:
        """Return certainty level.
        
        Returns 1.0 if deterministic, 0.0 otherwise.
        In the future, this could return a richer metric.
        """
        return 1.0 if self.is_deterministic else 0.0
    
    def __array__(self, *args, **kwargs) -> np.ndarray:
        """Enable numpy array conversion - returns mean values.
        
        This provides backward compatibility with code that expects
        numpy arrays.
        """
        return np.asarray(self.mean, *args, **kwargs)
    
    def __len__(self) -> int:
        """Return the number of elements in the series."""
        return len(self.index)
    
    def __getitem__(self, key):
        """Enable dictionary-like access by index label."""
        if key in self.index:
            idx = self.index.index(key)
            result = {"mean": float(self.mean[idx])}
            if self.std is not None:
                result["std"] = float(self.std[idx])
            if self.quantiles is not None:
                result["quantiles"] = {
                    q: float(arr[idx]) for q, arr in self.quantiles.items()
                }
            return result
        raise KeyError(f"Index {key} not found in StatSeries")
    
    def to_dict(self) -> Dict[Any, Dict[str, Any]]:
        """Convert to dictionary mapping index -> stats dict.
        
        Returns
        -------
        dict
            Dictionary with keys from index, values are dicts with 'mean',
            optionally 'std' and 'quantiles'.
        """
        result = {}
        for i, key in enumerate(self.index):
            item = {"mean": float(self.mean[i])}
            if self.std is not None:
                item["std"] = float(self.std[i])
            if self.quantiles is not None:
                item["quantiles"] = {
                    q: float(arr[i]) for q, arr in self.quantiles.items()
                }
            result[key] = item
        return result


@dataclass
class StatMatrix:
    """A matrix of statistics with optional uncertainty.
    
    Used for adjacency matrices, co-association matrices, distance matrices, etc.
    
    Parameters
    ----------
    index : list[Any]
        Row/column labels (assumed square matrix for simplicity).
    mean : np.ndarray
        The mean matrix, shape (n, n).
    std : np.ndarray or None
        The standard deviation matrix, shape (n, n), or None.
    quantiles : dict[float, np.ndarray] or None
        Quantile matrices, e.g., {0.025: (n, n), 0.975: (n, n)}.
    meta : dict[str, Any]
        Optional metadata.
    
    Examples
    --------
    >>> import numpy as np
    >>> m = StatMatrix(
    ...     index=['a', 'b', 'c'],
    ...     mean=np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)
    ... )
    >>> m.is_deterministic
    True
    >>> np.array(m).shape
    (3, 3)
    """
    
    index: List[Any]
    mean: np.ndarray
    std: Optional[np.ndarray] = None
    quantiles: Optional[Dict[float, np.ndarray]] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and convert arrays."""
        # Convert mean to numpy array
        if not isinstance(self.mean, np.ndarray):
            self.mean = np.asarray(self.mean, dtype=float)
        
        # Convert std if present
        if self.std is not None and not isinstance(self.std, np.ndarray):
            self.std = np.asarray(self.std, dtype=float)
        
        # Convert quantile matrices if present
        if self.quantiles is not None:
            self.quantiles = {
                k: np.asarray(v, dtype=float) if not isinstance(v, np.ndarray) else v
                for k, v in self.quantiles.items()
            }
        
        # Validate shapes
        n = len(self.index)
        if self.mean.shape != (n, n):
            raise ValueError(
                f"mean shape {self.mean.shape} != ({n}, {n}) for index length {n}"
            )
        
        if self.std is not None and self.std.shape != (n, n):
            raise ValueError(
                f"std shape {self.std.shape} != ({n}, {n}) for index length {n}"
            )
        
        if self.quantiles is not None:
            for q, mat in self.quantiles.items():
                if mat.shape != (n, n):
                    raise ValueError(
                        f"quantile {q} shape {mat.shape} != ({n}, {n})"
                    )
    
    @property
    def is_deterministic(self) -> bool:
        """Return True if this is a deterministic result."""
        return self.std is None or np.all(self.std == 0)
    
    @property
    def certainty(self) -> float:
        """Return certainty level (1.0 if deterministic, 0.0 otherwise)."""
        return 1.0 if self.is_deterministic else 0.0
    
    def __array__(self, *args, **kwargs) -> np.ndarray:
        """Enable numpy array conversion - returns mean matrix."""
        return np.asarray(self.mean, *args, **kwargs)
    
    def __len__(self) -> int:
        """Return the dimension of the matrix."""
        return len(self.index)


@dataclass
class CommunityStats:
    """Statistics from community detection with optional uncertainty.
    
    Wraps cluster labels, modularity, co-association matrix, and stability
    indices computed from multiple runs.
    
    Parameters
    ----------
    labels : dict[Any, int]
        Node -> community ID mapping (from deterministic run or consensus).
    modularity : float or None
        Modularity score (mean if multiple runs).
    modularity_std : float or None
        Standard deviation of modularity across runs.
    coassoc : StatMatrix or None
        Co-association matrix (probability nodes are in same community).
    stability : dict[Any, float] or None
        Per-node stability index (how often node stays in same cluster).
    n_communities : int
        Number of communities detected.
    meta : dict[str, Any]
        Optional metadata.
    
    Examples
    --------
    >>> cs = CommunityStats(
    ...     labels={'a': 0, 'b': 0, 'c': 1},
    ...     modularity=0.42,
    ...     n_communities=2
    ... )
    >>> cs.is_deterministic
    True
    >>> cs.labels['a']
    0
    """
    
    labels: Dict[Any, int]
    modularity: Optional[float] = None
    modularity_std: Optional[float] = None
    coassoc: Optional[StatMatrix] = None
    stability: Optional[Dict[Any, float]] = None
    n_communities: int = 0
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and compute defaults."""
        # Compute n_communities if not provided
        if self.n_communities == 0 and self.labels:
            self.n_communities = len(set(self.labels.values()))
    
    @property
    def is_deterministic(self) -> bool:
        """Return True if no uncertainty info is present."""
        return (
            self.modularity_std is None
            and self.coassoc is None
            and self.stability is None
        )
    
    @property
    def certainty(self) -> float:
        """Return certainty level (1.0 if deterministic, 0.0 otherwise)."""
        return 1.0 if self.is_deterministic else 0.0
    
    def __len__(self) -> int:
        """Return the number of nodes."""
        return len(self.labels)
