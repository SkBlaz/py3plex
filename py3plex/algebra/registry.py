"""Registry helpers for semirings and legacy algebra operations."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, DefaultDict, Dict, List

from py3plex.exceptions import Py3plexException

from .backend import AlgebraBackend
from .semiring import (
    BooleanSemiring,
    MaxPlusSemiring,
    MaxTimesSemiring,
    MinPlusSemiring,
    Semiring,
)


class SemiringRegistry:
    """Global registry for semirings."""

    def __init__(self):
        self._semirings: Dict[str, Semiring] = {}
        self._register_builtins()

    def _register_builtins(self):
        self.register("boolean", BooleanSemiring(), overwrite=False)
        self.register("max_plus", MaxPlusSemiring(), overwrite=False)
        self.register("max_times", MaxTimesSemiring(), overwrite=False)
        self.register("min_plus", MinPlusSemiring(), overwrite=False)

    def register(self, name: str, semiring: Semiring, overwrite: bool = False):
        if name in self._semirings and not overwrite:
            raise Py3plexException(
                f"Semiring '{name}' already registered. Use overwrite=True to replace."
            )
        self._semirings[name] = semiring

    def get(self, name: str) -> Semiring:
        if name not in self._semirings:
            available = ", ".join(sorted(self._semirings.keys()))
            raise Py3plexException(
                f"Unknown semiring: '{name}'. Available semirings: {available}"
            )
        return self._semirings[name]

    def list(self) -> List[str]:
        return sorted(self._semirings.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._semirings


class AlgebraRegistry:
    """Legacy operation registry kept for backward compatibility."""

    def __init__(self):
        self._operations: DefaultDict[str, Dict[AlgebraBackend, Callable]] = defaultdict(
            dict
        )

    def register(
        self, operation: str, backend: AlgebraBackend, implementation: Callable
    ) -> None:
        self._operations[operation][backend] = implementation

    def get(self, operation: str, backend: AlgebraBackend) -> Callable:
        try:
            return self._operations[operation][backend]
        except KeyError as exc:
            raise KeyError(
                f"No implementation registered for operation '{operation}' on backend "
                f"'{backend.value}'."
            ) from exc

    def list_operations(self) -> List[str]:
        return sorted(self._operations.keys())

    def clear(self) -> None:
        self._operations.clear()


semiring_registry = SemiringRegistry()
_operation_registry = AlgebraRegistry()


def register_semiring(name: str, semiring: Semiring, overwrite: bool = False):
    semiring_registry.register(name, semiring, overwrite=overwrite)


def get_semiring(name: str) -> Semiring:
    return semiring_registry.get(name)


def list_semirings() -> List[str]:
    return semiring_registry.list()


def get_registry() -> AlgebraRegistry:
    return _operation_registry


def register_operation(
    operation: str, backend: AlgebraBackend, implementation: Callable
) -> None:
    _operation_registry.register(operation, backend, implementation)


def get_operation(operation: str, backend: AlgebraBackend) -> Callable:
    return _operation_registry.get(operation, backend)


def list_operations() -> List[str]:
    return _operation_registry.list_operations()


def clear_registry() -> None:
    _operation_registry.clear()
