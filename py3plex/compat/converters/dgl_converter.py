"""
DGL converter (optional dependency).

This converter requires dgl to be installed.
Install with: pip install dgl
"""

from typing import Any

from ..exceptions import ConversionNotSupportedError
from ..ir import GraphIR

# Try to import DGL
try:
    import dgl
    
    DGL_AVAILABLE = True
except ImportError:
    DGL_AVAILABLE = False


def to_dgl_from_ir(ir: GraphIR, *, strict: bool = True, **kwargs) -> Any:
    """
    Convert GraphIR to DGL graph.
    
    Args:
        ir: GraphIR to convert
        strict: If True, raise on incompatibilities
        **kwargs: Additional arguments
    
    Returns:
        DGL graph object
    
    Raises:
        ConversionNotSupportedError: If DGL is not installed
    """
    if not DGL_AVAILABLE:
        raise ConversionNotSupportedError(
            "DGL conversion requires dgl to be installed. "
            "Install with: pip install dgl"
        )
    
    # For now, return a minimal implementation
    raise NotImplementedError("DGL converter is not yet fully implemented")


def from_dgl_to_ir(g: Any) -> GraphIR:
    """
    Convert DGL graph to GraphIR.
    
    Args:
        g: DGL graph object
    
    Returns:
        GraphIR representation
    
    Raises:
        ConversionNotSupportedError: If DGL is not installed
    """
    if not DGL_AVAILABLE:
        raise ConversionNotSupportedError(
            "DGL conversion requires dgl to be installed. "
            "Install with: pip install dgl"
        )
    
    raise NotImplementedError("DGL converter is not yet fully implemented")
