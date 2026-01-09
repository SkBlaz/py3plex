"""Online reducers for uncertainty quantification.

This module provides the base Reducer protocol and common reducer implementations.
Reducers accumulate statistics from a stream of samples without storing all samples.
"""

from .base import Reducer

__all__ = ["Reducer"]
