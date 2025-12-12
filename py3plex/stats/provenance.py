"""Provenance tracking for statistics.

This module provides a lightweight dataclass for recording how a statistic
was computed, including algorithm, uncertainty method, parameters, and seed.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Provenance:
    """Provenance information for a statistic.
    
    Records how a statistic was computed for reproducibility and transparency.
    
    Attributes:
        algorithm: Name of the algorithm (e.g., "brandes", "degree")
        uncertainty_method: Method used for uncertainty (e.g., "bootstrap", "analytic", "delta")
        parameters: Algorithm and uncertainty parameters
        seed: Random seed (if applicable)
        timestamp: When the computation occurred (optional)
        library_version: Version of py3plex (optional)
    
    Examples:
        >>> prov = Provenance(
        ...     algorithm="brandes",
        ...     uncertainty_method="bootstrap",
        ...     parameters={"n_samples": 100, "unit": "edges"},
        ...     seed=42
        ... )
        >>> prov.to_json_dict()
        {'algorithm': 'brandes', 'uncertainty_method': 'bootstrap', ...}
    """
    
    algorithm: str
    uncertainty_method: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    seed: Optional[int] = None
    timestamp: Optional[str] = None
    library_version: Optional[str] = None
    
    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary.
        
        Returns:
            Dictionary with provenance information
        """
        result = {
            "algorithm": self.algorithm,
            "uncertainty_method": self.uncertainty_method,
            "params": self.parameters.copy(),
        }
        if self.seed is not None:
            result["seed"] = self.seed
        if self.timestamp is not None:
            result["timestamp"] = self.timestamp
        if self.library_version is not None:
            result["library_version"] = self.library_version
        return result
    
    @classmethod
    def from_json_dict(cls, data: Dict[str, Any]) -> "Provenance":
        """Create from JSON dictionary.
        
        Args:
            data: Dictionary with provenance data
            
        Returns:
            Provenance instance
        """
        return cls(
            algorithm=data["algorithm"],
            uncertainty_method=data["uncertainty_method"],
            parameters=data.get("params", {}),
            seed=data.get("seed"),
            timestamp=data.get("timestamp"),
            library_version=data.get("library_version"),
        )
