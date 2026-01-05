"""Witness tracking structures for path reconstruction.

Optional module for tracking path witnesses (predecessors, k-best paths).
Disabled by default for performance.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class WitnessSpec:
    """Specification for witness tracking.
    
    Attributes:
        enabled: Whether to track witnesses
        mode: Tracking mode:
              - "single": single best predecessor
              - "k_best": track k best paths (requires semiring support)
        compress: Whether to compress witness data (future optimization)
        k: Number of paths to track (for k_best mode)
    """
    enabled: bool = False
    mode: str = "single"
    compress: bool = False
    k: int = 1
    
    def __post_init__(self):
        """Validate specification."""
        if self.mode not in ("single", "k_best"):
            raise ValueError(f"Invalid witness mode: {self.mode}")
        if self.k < 1:
            raise ValueError(f"k must be >= 1, got {self.k}")


@dataclass
class PathWitness:
    """Witness data for a single path.
    
    Attributes:
        value: Semiring value for this path
        predecessor: Previous node in path
        edge_data: Optional edge metadata
    """
    value: Any
    predecessor: Optional[Any] = None
    edge_data: Optional[Dict[str, Any]] = None


@dataclass
class KBestWitnesses:
    """Container for k-best path witnesses.
    
    Attributes:
        witnesses: List of PathWitness objects, sorted by semiring.better()
        max_k: Maximum number of witnesses to track
    """
    witnesses: List[PathWitness] = field(default_factory=list)
    max_k: int = 1
    
    def add(self, witness: PathWitness, better_fn):
        """Add a witness, maintaining k-best invariant.
        
        Args:
            witness: New witness to add
            better_fn: Function to compare witness values
        """
        self.witnesses.append(witness)
        # Sort by value using better_fn
        self.witnesses.sort(key=lambda w: w.value, reverse=False)
        # Keep only top k
        if len(self.witnesses) > self.max_k:
            self.witnesses = self.witnesses[:self.max_k]
    
    def best(self) -> Optional[PathWitness]:
        """Get best witness."""
        return self.witnesses[0] if self.witnesses else None
