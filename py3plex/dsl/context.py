"""Execution context for DSL operators.

This module defines the DSLExecutionContext dataclass that is passed to
all DSL operators, providing access to the network, current selection, and
query parameters.
"""

from dataclasses import dataclass
from typing import Any, List, Mapping, Optional


@dataclass
class DSLExecutionContext:
    """Execution context passed to DSL operators.

    This context object provides operators with access to the network,
    current selection state, and query parameters.

    Attributes:
        graph: The underlying multilayer network object
        current_layers: Currently selected layers (None = all layers)
        current_nodes: Currently selected nodes (None = all nodes)
        params: Query parameters (e.g., from Param() in builder API)
    """
    graph: Any
    current_layers: Optional[List[str]] = None
    current_nodes: Optional[List[Any]] = None
    params: Mapping[str, Any] = None

    def __post_init__(self):
        if self.params is None:
            self.params = {}
