"""Base reducer protocol for UQ execution.

This module defines the Reducer protocol that all reducers must implement.
Reducers are online aggregators that accumulate statistics from samples
without storing all samples in memory.

Examples
--------
>>> from py3plex.uncertainty.reducers.base import Reducer
>>> 
>>> class MeanReducer(Reducer):
...     def __init__(self):
...         self.sum = 0.0
...         self.count = 0
...     
...     def update(self, sample_output):
...         self.sum += sample_output.value
...         self.count += 1
...     
...     def finalize(self):
...         return self.sum / self.count if self.count > 0 else 0.0
...     
...     def reset(self):
...         self.sum = 0.0
...         self.count = 0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Reducer(ABC):
    """Base protocol for online reducers.
    
    Reducers follow the online aggregation pattern:
    1. Initialize state in __init__
    2. update(sample_output) - accumulate from one sample
    3. finalize() - compute final result
    4. reset() - clear state for reuse
    
    Reducers must be:
    - Online: Process samples one at a time
    - Composable: Multiple reducers can run in parallel
    - Memory-efficient: Don't store all samples (unless explicitly needed)
    - Independent: No dependencies on DSL or QueryResult
    
    Notes
    -----
    - Reducers MUST NOT control execution flow
    - Reducers MUST NOT depend on sample order (unless explicitly designed to)
    - Reducers SHOULD be deterministic given the same sample sequence
    """
    
    @abstractmethod
    def update(self, sample_output: Any):
        """Update reducer with a new sample.
        
        This method is called once per sample during UQ execution.
        It should accumulate whatever statistics are needed without
        storing the full sample (unless storage is required).
        
        Parameters
        ----------
        sample_output : Any
            Output from base_callable for this sample.
            Type depends on the algorithm (e.g., PartitionOutput for communities).
        """
        pass
    
    @abstractmethod
    def finalize(self) -> Any:
        """Finalize and return accumulated statistics.
        
        This method is called once after all samples have been processed.
        It should compute the final result from accumulated state.
        
        Returns
        -------
        Any
            Reducer-specific output (e.g., dict, array, scalar).
            The return type is specific to each reducer implementation.
        """
        pass
    
    @abstractmethod
    def reset(self):
        """Reset reducer to initial state.
        
        This method allows reusing the same reducer instance for multiple
        UQ runs. It should clear all accumulated state.
        """
        pass
