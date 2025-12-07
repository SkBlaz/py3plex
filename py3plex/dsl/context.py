"""DSL execution context for operators.

This module provides the execution context that is passed to DSL operators.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DSLExecutionContext:
    """Execution context passed to DSL operators.
    
    This context provides operators with access to the network graph,
    selected layers/nodes, and any additional parameters.
    
    Attributes:
        graph: The underlying multilayer network or NetworkX graph
        network: The full multilayer network object (for multilayer operations)
        current_layers: List of active layer names (None means all layers)
        current_nodes: List of selected nodes (None means all nodes)
        params: Global parameters for the DSL execution (e.g., random seed)
        meta: Additional metadata about the query execution
    """
    graph: Any  # NetworkX graph or subgraph
    network: Any  # Full multilayer network object
    current_layers: Optional[List[str]] = None
    current_nodes: Optional[List[Any]] = None
    params: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def get_param(self, name: str, default: Any = None) -> Any:
        """Get a parameter value with optional default.
        
        Args:
            name: Parameter name
            default: Default value if parameter not found
            
        Returns:
            Parameter value or default
        """
        return self.params.get(name, default)
    
    def has_param(self, name: str) -> bool:
        """Check if a parameter exists.
        
        Args:
            name: Parameter name
            
        Returns:
            True if parameter exists
        """
        return name in self.params
