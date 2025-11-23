"""
NetworkX compatibility layer for py3plex.
This module provides compatibility functions for different NetworkX versions.
"""

import pickle
from typing import Any, Optional

import networkx as nx
import scipy.sparse as sp

# Optional formal verification support
try:
    from icontract import ensure, require

    ICONTRACT_AVAILABLE = True
except ImportError:
    # Create no-op decorators when icontract is not available
    def require(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def ensure(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    ICONTRACT_AVAILABLE = False

# NetworkX version check
NX_VERSION = tuple(map(int, nx.__version__.split(".")[:2]))


@require(lambda G: G is not None, "G must not be None")
@require(lambda G: isinstance(G, nx.Graph), "G must be a NetworkX graph")
@ensure(lambda result: isinstance(result, str), "result must be a string")
@ensure(lambda result: len(result) > 0, "result must not be empty")
def nx_info(G: nx.Graph) -> str:
    """
    Get network information (compatible with NetworkX < 3.0 and >= 3.0).

    Args:
        G: NetworkX graph

    Returns:
        str: Network information

    Contracts:
        - Precondition: G must not be None and must be a NetworkX graph
        - Postcondition: returns a non-empty string
    """
    if hasattr(nx, "info"):
        # NetworkX < 3.0
        return str(nx.info(G))
    else:
        # NetworkX >= 3.0 - manually construct info string
        info_lines = []
        info_lines.append(f"Name: {G.name if hasattr(G, 'name') and G.name else ''}")
        info_lines.append(f"Type: {type(G).__name__}")
        info_lines.append(f"Number of nodes: {G.number_of_nodes()}")
        info_lines.append(f"Number of edges: {G.number_of_edges()}")

        if hasattr(G, "is_directed") and G.is_directed():
            info_lines.append("Directed: True")
        else:
            info_lines.append("Directed: False")

        if hasattr(G, "is_multigraph") and G.is_multigraph():
            info_lines.append("Multigraph: True")
        else:
            info_lines.append("Multigraph: False")

        return "\n".join(info_lines)


@require(lambda path: isinstance(path, str), "path must be a string")
@require(lambda path: len(path) > 0, "path must not be empty")
@ensure(lambda result: result is not None, "result must not be None")
@ensure(lambda result: isinstance(result, nx.Graph), "result must be a NetworkX graph")
def nx_read_gpickle(path: str) -> nx.Graph:
    """
    Read a graph from a pickle file (compatible with NetworkX < 3.0 and >= 3.0).

    Args:
        path: File path

    Returns:
        NetworkX graph

    Contracts:
        - Precondition: path must be a non-empty string
        - Postcondition: returns a NetworkX graph
    """
    if hasattr(nx, "read_gpickle"):
        # NetworkX < 3.0
        return nx.read_gpickle(path)
    else:
        # NetworkX >= 3.0 - use direct pickle
        with open(path, "rb") as f:
            return pickle.load(f)


@require(lambda G: G is not None, "G must not be None")
@require(lambda G: isinstance(G, nx.Graph), "G must be a NetworkX graph")
@require(lambda path: isinstance(path, str), "path must be a string")
@require(lambda path: len(path) > 0, "path must not be empty")
def nx_write_gpickle(G: nx.Graph, path: str) -> None:
    """
    Write a graph to a pickle file (compatible with NetworkX < 3.0 and >= 3.0).

    Args:
        G: NetworkX graph
        path: File path

    Contracts:
        - Precondition: G must not be None and must be a NetworkX graph
        - Precondition: path must be a non-empty string
    """
    if hasattr(nx, "write_gpickle"):
        # NetworkX < 3.0
        nx.write_gpickle(G, path)
    else:
        # NetworkX >= 3.0 - use direct pickle
        with open(path, "wb") as f:
            pickle.dump(G, f)


@require(lambda G: G is not None, "G must not be None")
@require(lambda G: isinstance(G, nx.Graph), "G must be a NetworkX graph")
@require(lambda weight: isinstance(weight, str), "weight must be a string")
@require(lambda weight: len(weight) > 0, "weight must not be empty")
@require(lambda format: isinstance(format, str), "format must be a string")
@require(lambda format: len(format) > 0, "format must not be empty")
@ensure(lambda result: result is not None, "result must not be None")
def nx_to_scipy_sparse_matrix(
    G: nx.Graph,
    nodelist: Optional[list] = None,
    dtype: Optional[Any] = None,
    weight: str = "weight",
    format: str = "csr",
) -> Any:  # Returns scipy sparse matrix
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

    Contracts:
        - Precondition: G must not be None and must be a NetworkX graph
        - Precondition: weight must be a non-empty string
        - Precondition: format must be a non-empty string
        - Postcondition: returns a non-None sparse matrix
    """
    if hasattr(nx, "to_scipy_sparse_matrix"):
        # NetworkX < 3.0
        return nx.to_scipy_sparse_matrix(
            G, nodelist=nodelist, dtype=dtype, weight=weight, format=format
        )
    else:
        # NetworkX >= 3.0 - use adjacency_matrix
        # Note: nx.adjacency_matrix returns sparse array in 3.0+, convert to matrix
        matrix = nx.adjacency_matrix(G, nodelist=nodelist, dtype=dtype, weight=weight)
        # Convert to requested format and ensure it's a sparse matrix
        if format != "csr":
            return sp.csr_matrix(matrix.asformat(format))
        return sp.csr_matrix(matrix)


def is_string_like(obj: Any) -> bool:
    """
    Check if obj is string-like (compatible with NetworkX < 3.0).

    Args:
        obj: Object to check

    Returns:
        bool: True if string-like
    """
    return isinstance(obj, str)


@require(lambda A: A is not None, "A must not be None")
@require(
    lambda edge_attribute: isinstance(edge_attribute, str),
    "edge_attribute must be a string",
)
@require(
    lambda edge_attribute: len(edge_attribute) > 0, "edge_attribute must not be empty"
)
@ensure(lambda result: result is not None, "result must not be None")
@ensure(lambda result: isinstance(result, nx.Graph), "result must be a NetworkX graph")
def nx_from_scipy_sparse_matrix(
    A: Any,  # scipy sparse matrix
    parallel_edges: bool = False,
    create_using: Optional[nx.Graph] = None,
    edge_attribute: str = "weight",
) -> nx.Graph:
    """
    Create a graph from scipy sparse matrix (compatible with NetworkX < 3.0 and >= 3.0).

    Args:
        A: scipy sparse matrix
        parallel_edges: Whether to create parallel edges (ignored in NetworkX 3.0+)
        create_using: Graph type to create
        edge_attribute: Edge attribute name for weights

    Returns:
        NetworkX graph

    Contracts:
        - Precondition: A must not be None
        - Precondition: edge_attribute must be a non-empty string
        - Postcondition: returns a NetworkX graph
    """
    if hasattr(nx, "from_scipy_sparse_matrix"):
        # NetworkX < 3.0
        return nx.from_scipy_sparse_matrix(
            A,
            parallel_edges=parallel_edges,
            create_using=create_using,
            edge_attribute=edge_attribute,
        )
    else:
        # NetworkX >= 3.0 - use from_scipy_sparse_array
        return nx.from_scipy_sparse_array(
            A, create_using=create_using, edge_attribute=edge_attribute
        )
