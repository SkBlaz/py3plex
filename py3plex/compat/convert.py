"""
High-level conversion API for lossless graph conversions.

This module provides the main entry point for converting between py3plex
graphs and external formats.
"""

import warnings
from typing import Any, Dict, Literal, Optional

from .exceptions import CompatibilityError, ConversionNotSupportedError
from .ir import GraphIR, from_ir, to_ir


def convert(
    graph: Any,
    target: str,
    *,
    strict: bool = True,
    sidecar: Optional[str] = "auto",
    **kwargs,
) -> Any:
    """
    Convert a graph to a target format with lossless preservation.
    
    This is the main entry point for graph conversion. It routes to
    specific converters based on the target format.
    
    Args:
        graph: Source graph (py3plex graph, NetworkX, scipy sparse, etc.)
        target: Target format name:
            - "networkx": NetworkX graph
            - "scipy_sparse": SciPy sparse matrix
            - "igraph": igraph graph (requires python-igraph)
            - "pyg": PyTorch Geometric Data (requires torch-geometric)
            - "dgl": DGL graph (requires dgl)
        strict: If True, raise exception if target cannot represent all data.
               If False, use sidecar bundle to preserve data.
        sidecar: Path for sidecar bundle (used in non-strict mode).
               "auto" generates a path based on target.
               None disables sidecar.
        **kwargs: Additional arguments passed to specific converters
    
    Returns:
        Converted graph in target format
    
    Raises:
        ConversionNotSupportedError: If target is not recognized or available
        CompatibilityError: In strict mode, if target cannot represent the graph
    
    Examples:
        >>> # Convert py3plex to NetworkX
        >>> nx_graph = convert(py3_graph, "networkx")
        
        >>> # Convert to scipy sparse with sidecar for attributes
        >>> matrix = convert(py3_graph, "scipy_sparse", strict=False, sidecar="my_graph")
        
        >>> # Convert from NetworkX to py3plex (via "py3plex" target)
        >>> py3_graph = convert(nx_graph, "py3plex")
    """
    # Import specific converters based on target
    if target == "networkx":
        from .converters.networkx_converter import to_networkx_from_ir
        
        ir = to_ir(graph)
        return to_networkx_from_ir(ir, strict=strict, **kwargs)
    
    elif target == "scipy_sparse" or target == "scipy":
        from .converters.scipy_converter import to_scipy_sparse_from_ir
        
        ir = to_ir(graph)
        return to_scipy_sparse_from_ir(ir, strict=strict, sidecar=sidecar, **kwargs)
    
    elif target == "igraph":
        try:
            from .converters.igraph_converter import to_igraph_from_ir
        except ImportError:
            raise ConversionNotSupportedError(
                "igraph conversion requires python-igraph to be installed. "
                "Install with: pip install python-igraph"
            )
        
        ir = to_ir(graph)
        return to_igraph_from_ir(ir, strict=strict, **kwargs)
    
    elif target == "pyg" or target == "torch_geometric":
        try:
            from .converters.pyg_converter import to_pyg_from_ir
        except ImportError:
            raise ConversionNotSupportedError(
                "PyTorch Geometric conversion requires torch and torch-geometric. "
                "Install with: pip install torch torch-geometric"
            )
        
        ir = to_ir(graph)
        return to_pyg_from_ir(ir, strict=strict, **kwargs)
    
    elif target == "dgl":
        try:
            from .converters.dgl_converter import to_dgl_from_ir
        except ImportError:
            raise ConversionNotSupportedError(
                "DGL conversion requires dgl to be installed. "
                "Install with: pip install dgl"
            )
        
        ir = to_ir(graph)
        return to_dgl_from_ir(ir, strict=strict, **kwargs)
    
    elif target == "py3plex" or target == "multilayer_graph":
        # Convert from external format to py3plex
        ir = _infer_and_convert_to_ir(graph)
        return from_ir(ir, target_type="multilayer_graph")
    
    elif target == "multi_layer_network":
        # Convert to core multi_layer_network
        ir = _infer_and_convert_to_ir(graph)
        return from_ir(ir, target_type="multi_layer_network")
    
    else:
        raise ConversionNotSupportedError(
            f"Unknown target format: {target}. "
            "Supported: networkx, scipy_sparse, igraph, pyg, dgl, py3plex"
        )


def _infer_and_convert_to_ir(graph: Any) -> GraphIR:
    """
    Infer source format and convert to IR.
    
    Args:
        graph: Graph in some external format
    
    Returns:
        GraphIR representation
    
    Raises:
        TypeError: If graph format cannot be inferred
    """
    # Try py3plex formats first
    try:
        return to_ir(graph)
    except (TypeError, AttributeError):
        pass
    
    # Try NetworkX
    try:
        import networkx as nx
        
        if isinstance(graph, nx.Graph):
            from .converters.networkx_converter import from_networkx_to_ir
            
            return from_networkx_to_ir(graph)
    except ImportError:
        pass
    
    # Try scipy sparse
    try:
        import scipy.sparse as sp
        
        if sp.issparse(graph):
            from .converters.scipy_converter import from_scipy_sparse_to_ir
            
            return from_scipy_sparse_to_ir(graph)
    except ImportError:
        pass
    
    # Try igraph
    try:
        import igraph as ig
        
        if isinstance(graph, ig.Graph):
            from .converters.igraph_converter import from_igraph_to_ir
            
            return from_igraph_to_ir(graph)
    except ImportError:
        pass
    
    # Try PyG
    try:
        from torch_geometric.data import Data, HeteroData
        
        if isinstance(graph, (Data, HeteroData)):
            from .converters.pyg_converter import from_pyg_to_ir
            
            return from_pyg_to_ir(graph)
    except ImportError:
        pass
    
    # Try DGL
    try:
        import dgl
        
        if isinstance(graph, dgl.DGLGraph):
            from .converters.dgl_converter import from_dgl_to_ir
            
            return from_dgl_to_ir(graph)
    except ImportError:
        pass
    
    raise TypeError(
        f"Cannot infer format of graph with type {type(graph)}. "
        "Supported formats: py3plex, NetworkX, scipy.sparse, igraph, PyG, DGL"
    )
