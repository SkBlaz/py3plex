"""
PyTorch Geometric (PyG) converter (optional dependency).

This converter requires torch and torch-geometric to be installed.
Install with: pip install torch torch-geometric
"""

from typing import Any

from ..exceptions import ConversionNotSupportedError
from ..ir import GraphIR

# Try to import PyG
try:
    import torch
    from torch_geometric.data import Data, HeteroData
    
    PYG_AVAILABLE = True
except ImportError:
    PYG_AVAILABLE = False
    Data = None
    HeteroData = None


def to_pyg_from_ir(ir: GraphIR, *, strict: bool = True, **kwargs) -> Any:
    """
    Convert GraphIR to PyTorch Geometric Data object.
    
    Args:
        ir: GraphIR to convert
        strict: If True, raise on incompatibilities
        **kwargs: Additional arguments
    
    Returns:
        PyG Data or HeteroData object
    
    Raises:
        ConversionNotSupportedError: If PyG is not installed
    """
    if not PYG_AVAILABLE:
        raise ConversionNotSupportedError(
            "PyTorch Geometric conversion requires torch and torch-geometric. "
            "Install with: pip install torch torch-geometric"
        )
    
    # For now, return a minimal implementation
    # Full implementation would handle heterogeneous graphs, node features, etc.
    raise NotImplementedError("PyG converter is not yet fully implemented")


def from_pyg_to_ir(data: Any) -> GraphIR:
    """
    Convert PyG Data/HeteroData to GraphIR.
    
    Args:
        data: PyG Data or HeteroData object
    
    Returns:
        GraphIR representation
    
    Raises:
        ConversionNotSupportedError: If PyG is not installed
    """
    if not PYG_AVAILABLE:
        raise ConversionNotSupportedError(
            "PyTorch Geometric conversion requires torch and torch-geometric. "
            "Install with: pip install torch torch-geometric"
        )
    
    raise NotImplementedError("PyG converter is not yet fully implemented")
