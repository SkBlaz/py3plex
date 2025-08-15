"""
NetworkX compatibility layer for py3plex.
This module provides compatibility functions for different NetworkX versions.
"""

import networkx as nx
import pickle

# NetworkX version check
NX_VERSION = tuple(map(int, nx.__version__.split('.')[:2]))

def nx_info(G):
    """
    Get network information (compatible with NetworkX < 3.0 and >= 3.0).
    
    Args:
        G: NetworkX graph
        
    Returns:
        str: Network information
    """
    if hasattr(nx, 'info'):
        # NetworkX < 3.0
        return nx.info(G)
    else:
        # NetworkX >= 3.0 - manually construct info string
        info_lines = []
        info_lines.append(f"Name: {G.name if hasattr(G, 'name') and G.name else ''}")
        info_lines.append(f"Type: {type(G).__name__}")
        info_lines.append(f"Number of nodes: {G.number_of_nodes()}")
        info_lines.append(f"Number of edges: {G.number_of_edges()}")
        
        if hasattr(G, 'is_directed') and G.is_directed():
            info_lines.append("Directed: True")
        else:
            info_lines.append("Directed: False")
            
        if hasattr(G, 'is_multigraph') and G.is_multigraph():
            info_lines.append("Multigraph: True")
        else:
            info_lines.append("Multigraph: False")
            
        return '\n'.join(info_lines)

def nx_read_gpickle(path):
    """
    Read a graph from a pickle file (compatible with NetworkX < 3.0 and >= 3.0).
    
    Args:
        path: File path
        
    Returns:
        NetworkX graph
    """
    if hasattr(nx, 'read_gpickle'):
        # NetworkX < 3.0
        return nx.read_gpickle(path)
    else:
        # NetworkX >= 3.0 - use direct pickle
        with open(path, 'rb') as f:
            return pickle.load(f)

def nx_write_gpickle(G, path):
    """
    Write a graph to a pickle file (compatible with NetworkX < 3.0 and >= 3.0).
    
    Args:
        G: NetworkX graph
        path: File path
    """
    if hasattr(nx, 'write_gpickle'):
        # NetworkX < 3.0
        nx.write_gpickle(G, path)
    else:
        # NetworkX >= 3.0 - use direct pickle
        with open(path, 'wb') as f:
            pickle.dump(G, f)

def nx_to_scipy_sparse_matrix(G, nodelist=None, dtype=None, weight='weight', format='csr'):
    """
    Convert graph to scipy sparse matrix (compatible with NetworkX < 3.0 and >= 3.0).
    
    Args:
        G: NetworkX graph
        nodelist: List of nodes
        dtype: Data type
        weight: Edge weight attribute
        format: Sparse matrix format
        
    Returns:
        scipy sparse matrix
    """
    if hasattr(nx, 'to_scipy_sparse_matrix'):
        # NetworkX < 3.0
        return nx.to_scipy_sparse_matrix(G, nodelist=nodelist, dtype=dtype, weight=weight, format=format)
    else:
        # NetworkX >= 3.0 - use adjacency_matrix
        # Note: nx.to_scipy_sparse_array exists but returns array, we want matrix for compatibility
        matrix = nx.adjacency_matrix(G, nodelist=nodelist, dtype=dtype, weight=weight)
        if format != 'csr':
            matrix = matrix.asformat(format)
        return matrix

def is_string_like(obj):
    """
    Check if obj is string-like (compatible with NetworkX < 3.0).
    
    Args:
        obj: Object to check
        
    Returns:
        bool: True if string-like
    """
    return isinstance(obj, str)