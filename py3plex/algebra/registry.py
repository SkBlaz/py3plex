"""Semiring registry for managing and discovering semirings."""

from typing import Dict, List, Optional
from py3plex.exceptions import Py3plexException

from .semiring import (
    Semiring,
    BooleanSemiring,
    MinPlusSemiring,
    MaxPlusSemiring,
    MaxTimesSemiring,
)


class SemiringRegistry:
    """Global registry for semirings.
    
    Maintains a dictionary of available semirings by name.
    Provides deterministic ordering for list_semirings().
    """
    
    def __init__(self):
        """Initialize registry with built-in semirings."""
        self._semirings: Dict[str, Semiring] = {}
        # Register built-ins in deterministic order
        self._register_builtins()
    
    def _register_builtins(self):
        """Register built-in semirings."""
        # Register in alphabetical order for determinism
        self.register("boolean", BooleanSemiring(), overwrite=False)
        self.register("max_plus", MaxPlusSemiring(), overwrite=False)
        self.register("max_times", MaxTimesSemiring(), overwrite=False)
        self.register("min_plus", MinPlusSemiring(), overwrite=False)
    
    def register(self, name: str, semiring: Semiring, overwrite: bool = False):
        """Register a semiring.
        
        Args:
            name: Semiring identifier
            semiring: Semiring instance
            overwrite: If False, raises error if name already exists
            
        Raises:
            Py3plexException: If name exists and overwrite=False
        """
        if name in self._semirings and not overwrite:
            raise Py3plexException(
                f"Semiring '{name}' already registered. "
                f"Use overwrite=True to replace."
            )
        self._semirings[name] = semiring
    
    def get(self, name: str) -> Semiring:
        """Get a semiring by name.
        
        Args:
            name: Semiring identifier
            
        Returns:
            Semiring instance
            
        Raises:
            Py3plexException: If semiring not found
        """
        if name not in self._semirings:
            available = ", ".join(sorted(self._semirings.keys()))
            raise Py3plexException(
                f"Unknown semiring: '{name}'. "
                f"Available semirings: {available}"
            )
        return self._semirings[name]
    
    def list(self) -> List[str]:
        """List all registered semirings in deterministic order.
        
        Returns:
            Sorted list of semiring names
        """
        return sorted(self._semirings.keys())
    
    def __contains__(self, name: str) -> bool:
        """Check if semiring is registered."""
        return name in self._semirings


# Global registry instance
semiring_registry = SemiringRegistry()


# Public API functions
def register_semiring(name: str, semiring: Semiring, overwrite: bool = False):
    """Register a semiring in the global registry.
    
    Args:
        name: Semiring identifier
        semiring: Semiring instance
        overwrite: If False, raises error if name already exists
    """
    semiring_registry.register(name, semiring, overwrite=overwrite)


def get_semiring(name: str) -> Semiring:
    """Get a semiring from the global registry.
    
    Args:
        name: Semiring identifier
        
    Returns:
        Semiring instance
    """
    return semiring_registry.get(name)


def list_semirings() -> List[str]:
    """List all registered semirings in deterministic order.
    
    Returns:
        Sorted list of semiring names
    """
    return semiring_registry.list()
