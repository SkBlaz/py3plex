"""Null model result container.

This module provides a result object for null model generation operations.
"""

from typing import Any, Dict, List, Optional


class NullModelResult:
    """Result container for null model generation.
    
    Attributes:
        model_type: Type of null model used
        samples: List of generated network samples
        num_samples: Number of samples generated
        seed: Random seed used (if any)
        meta: Additional metadata about the generation
    """
    
    def __init__(
        self,
        model_type: str,
        samples: List[Any],
        seed: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """Initialize NullModelResult.
        
        Args:
            model_type: Type of null model used
            samples: List of generated network samples
            seed: Random seed used
            meta: Additional metadata
        """
        self.model_type = model_type
        self.samples = samples
        self.seed = seed
        self.meta = meta or {}
    
    @property
    def num_samples(self) -> int:
        """Get number of samples generated."""
        return len(self.samples)
    
    def __len__(self) -> int:
        """Return number of samples."""
        return len(self.samples)
    
    def __iter__(self):
        """Iterate over samples."""
        return iter(self.samples)
    
    def __getitem__(self, index: int):
        """Get sample by index."""
        return self.samples[index]
    
    def to_dict(self) -> Dict[str, Any]:
        """Export results as a dictionary.
        
        Returns:
            Dictionary with null model results (without actual samples)
        """
        return {
            "model_type": self.model_type,
            "num_samples": self.num_samples,
            "seed": self.seed,
            "meta": self.meta,
        }
    
    def __repr__(self) -> str:
        return (
            f"NullModelResult(model='{self.model_type}', "
            f"num_samples={self.num_samples}, seed={self.seed})"
        )
