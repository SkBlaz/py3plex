"""
Utility functions for py3plex.

This module provides common utilities used across the library,
including random state management for reproducibility.
"""

from typing import Optional, Union
import numpy as np


def get_rng(seed: Optional[Union[int, np.random.Generator]] = None) -> np.random.Generator:
    """
    Get a NumPy random number generator with optional seed.
    
    This provides a unified interface for random state management across
    the library, ensuring reproducibility when a seed is provided.
    
    Args:
        seed: Random seed for reproducibility. Can be:
            - None: Use default unseeded generator
            - int: Seed value for the generator
            - np.random.Generator: Pass through existing generator
        
    Returns:
        np.random.Generator: Initialized random number generator
        
    Examples:
        >>> rng = get_rng(42)
        >>> rng.random()  # Reproducible random number
        0.7739560485559633
        
        >>> rng1 = get_rng(42)
        >>> rng2 = get_rng(42)
        >>> rng1.random() == rng2.random()
        True
        
        >>> existing_rng = np.random.default_rng(123)
        >>> rng = get_rng(existing_rng)
        >>> rng is existing_rng
        True
    
    Note:
        Uses numpy.random.Generator (modern API introduced in NumPy 1.17)
        rather than the legacy numpy.random.RandomState API.
    """
    if isinstance(seed, np.random.Generator):
        return seed
    return np.random.default_rng(seed)
