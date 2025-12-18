# This is the main data structure container

import itertools
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union
import matplotlib.pyplot as plt

import networkx as nx
import numpy as np

# Optional formal verification support
try:
    from icontract import ensure, invariant, require

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

    def invariant(*args, **kwargs):
        def decorator(cls):
            return cls

        return decorator

    ICONTRACT_AVAILABLE = False

from py3plex.logging_config import get_logger

from . import converters, parsers
from .HINMINE.decomposition import hinmine_decompose  # decompose the graph
from .HINMINE.decomposition import hinmine_get_cycles
from .HINMINE.IO import load_hinmine_object  # parse the graph
from .nx_compat import nx_from_scipy_sparse_matrix, nx_info, nx_to_scipy_sparse_matrix

# Optional Ricci curvature support
try:
    from py3plex.algorithms.curvature.ollivier_ricci_multilayer import (
        compute_ollivier_ricci_single_graph,
        compute_ollivier_ricci_flow_single_graph,
        RicciBackendNotAvailable,
    )
    RICCI_AVAILABLE = True
except ImportError:
    RICCI_AVAILABLE = False
    RicciBackendNotAvailable = None

# Mapping of sparse matrix format names to conversion method names (for get_tensor)
SPARSE_FORMAT_METHODS = {
    'csr': 'tocsr',
    'csc': 'tocsc',
    'coo': 'tocoo',
    'lil': 'tolil',
    'dok': 'todok',
    'bsr': 'tobsr'
}

logger = get_logger(__name__)
try:
    import tqdm
except ImportError:
    # Create a simple mock for tqdm when it's not available
    class MockTqdm:
        @staticmethod
        def tqdm(iterable, *args, **kwargs):
            return iterable

    tqdm = MockTqdm()

try:
    from py3plex.algorithms.statistics import topology
except ImportError:
    pass

# visualization modules
try:
    from py3plex.visualization.multilayer import (
        draw_multiedges,
        draw_multilayer_default,
        hairball_plot,
        supra_adjacency_matrix_plot,
    )

    server_mode = False
except ImportError:
    server_mode = True


# ─────────────────────────────────────────────────────────────────────────────
# Temporal Attribute Conventions
# ─────────────────────────────────────────────────────────────────────────────
"""
Temporal Attributes for Edges
===============================

Py3plex supports optional temporal information on edges. This allows for 
time-aware network analysis without requiring invasive changes to existing code.

Supported Temporal Attributes:
    - **t**: A scalar timestamp (float, int, or ISO string) representing a 
      point-in-time when the edge is active. For example, t=100.0 means the 
      edge occurs at time 100.

    - **t_start** and **t_end**: Interval timestamps representing a time range 
      during which the edge is active. For example, t_start=100.0 and t_end=200.0 
      means the edge is active from time 100 to time 200 (inclusive).

Precedence Rules:
    - If both **t** and **t_start**/**t_end** are present, the interval form 
      (t_start/t_end) takes precedence.
    
    - If only **t_start** is present, the interval extends to infinity.
    
    - If only **t_end** is present, the interval starts from negative infinity.

Atemporal Edges:
    - Edges without any temporal attributes (no **t**, **t_start**, or **t_end**) 
      are considered "atemporal" and are always included in temporal queries.
    
    - This ensures backward compatibility with existing networks.

Usage with TemporalMultinetView:
    >>> from py3plex.temporal_view import TemporalMultinetView
    >>> 
    >>> # Add temporal edges
    >>> network.add_edges([
    ...     {'source': 'A', 'target': 'B', 't': 100.0,
    ...      'source_type': 'layer1', 'target_type': 'layer1'},
    ...     {'source': 'B', 'target': 'C', 't_start': 150.0, 't_end': 250.0,
    ...      'source_type': 'layer1', 'target_type': 'layer1'}
    ... ])
    >>> 
    >>> # Create temporal view
    >>> view = TemporalMultinetView(network)
    >>> snapshot = view.snapshot_at(150.0)  # Only edges active at t=150
    >>> range_view = view.with_slice(100.0, 200.0)  # Edges active in [100, 200]

For more details, see:
    - py3plex.temporal_utils: Utilities for parsing and extracting temporal data
    - py3plex.temporal_view: TemporalMultinetView wrapper for temporal filtering
    - DSL temporal queries: AT and DURING clauses for time-based queries
"""


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions for visualization (extracted from visualize_network method)
# ─────────────────────────────────────────────────────────────────────────────


def _draw_diagonal_layers(
    graphs, network_labels, parameters_layers, axis, verbose
):
    """Helper function to draw diagonal layer visualization.

    Args:
        graphs: List of layer graphs
        network_labels: Labels for network layers
        parameters_layers: Custom parameters for layer drawing
        axis: Optional matplotlib axis
        verbose: Enable verbose output

    Returns:
        Matplotlib axis object
    """
    if parameters_layers is None:
        draw_params = {
            "display": False,
            "background_shape": "circle",
            "labels": network_labels,
            "node_size": 3,
            "verbose": verbose,
        }
        return draw_multilayer_default(graphs, **draw_params)
    else:
        return draw_multilayer_default(graphs, **parameters_layers)


def _draw_multiedges_for_type(
    graphs,
    edges,
    edge_type,
    alphachannel,
    linepoints,
    orientation,
    linewidth,
    resolution,
    parameters_multiedges=None,
):
    """Helper function to draw multi-edges for a specific edge type.

    Args:
        graphs: List of layer graphs
        edges: Edges to draw
        edge_type: Type of edges ('coupling' or other)
        alphachannel: Alpha channel for edge transparency
        linepoints: Line style for edges
        orientation: Edge orientation ('upper', 'bottom', etc.)
        linewidth: Width of edge lines
        resolution: Resolution for edge curves
        parameters_multiedges: Custom parameters for edge drawing

    Returns:
        Matplotlib axis object
    """
    if parameters_multiedges is not None:
        return draw_multiedges(graphs, edges, **parameters_multiedges)

    if edge_type == "coupling":
        return draw_multiedges(
            graphs,
            edges,
            alphachannel=alphachannel,
            linepoints=linepoints,
            linecolor="red",
            curve_height=2,
            linmod="bottom",
            linewidth=linewidth,
            resolution=resolution,
        )
    else:
        return draw_multiedges(
            graphs,
            edges,
            alphachannel=alphachannel,
            linepoints="--",
            linecolor="black",
            curve_height=2,
            linmod=orientation,
            linewidth=linewidth,
            resolution=resolution,
        )


def _visualize_diagonal_style(
    network_obj,
    parameters_layers,
    parameters_multiedges,
    axis,
    verbose,
    no_labels,
    alphachannel,
    linepoints,
    orientation,
    linewidth,
    resolution,
    show,
):
    """Helper function for diagonal style visualization.

    Args:
        network_obj: Multi-layer network object
        parameters_layers: Custom parameters for layer drawing
        parameters_multiedges: Custom parameters for edge drawing
        axis: Optional matplotlib axis
        verbose: Enable verbose output
        no_labels: Hide network labels
        alphachannel: Alpha channel for edge transparency
        linepoints: Line style for edges
        orientation: Edge orientation
        linewidth: Width of edge lines
        resolution: Resolution for edge curves
        show: Show plot immediately

    Returns:
        Matplotlib axis object
    """
    network_labels, graphs, multilinks = network_obj.get_layers("diagonal")
    if no_labels:
        network_labels = None

    # Draw layers
    ax = _draw_diagonal_layers(graphs, network_labels, parameters_layers, axis, verbose)

    # Draw multi-edges
    for edge_type, edges in tqdm.tqdm(multilinks.items()):
        ax = _draw_multiedges_for_type(
            graphs,
            edges,
            edge_type,
            alphachannel,
            linepoints,
            orientation,
            linewidth,
            resolution,
            parameters_multiedges,
        )

    if show:
        plt.show()

    return ax


def _visualize_hairball_style(network_obj, axis, legend, show):
    """Helper function for hairball style visualization.

    Args:
        network_obj: Multi-layer network object
        axis: Optional matplotlib axis
        legend: Show legend
        show: Show plot immediately

    Returns:
        Matplotlib axis object
    """
    network_colors, graph = network_obj.get_layers(style="hairball")
    ax = hairball_plot(graph, network_colors, layout_algorithm="force", legend=legend)

    if show:
        plt.show()

    return ax


def _encode_multilayer_network(core_network, directed):
    """Helper function to encode multilayer network to numeric format.

    Args:
        core_network: NetworkX graph with multilayer structure
        directed: Whether the network is directed

    Returns:
        Tuple of (numeric_network, node_order)
    """
    nmap = {}
    n_count = 0

    # Create simple graph based on directedness
    simple_graph = nx.DiGraph() if directed else nx.Graph()

    # First, add all nodes (including isolated nodes)
    for node in core_network.nodes():
        if node not in nmap:
            nmap[node] = n_count
            simple_graph.add_node(n_count)
            n_count += 1

    # Then add all edges with weights
    for edge in core_network.edges(data=True):
        node_first, node_second = edge[0], edge[1]
        try:
            weight = float(edge[2]["weight"])
        except (KeyError, IndexError, ValueError, TypeError):
            weight = 1

        simple_graph.add_edge(nmap[node_first], nmap[node_second], weight=weight)

    vectors = nx_to_scipy_sparse_matrix(simple_graph)
    return vectors, simple_graph.nodes()


def _encode_multiplex_network(core_network):
    """Helper function to encode multiplex network to numeric format using sparse matrices.

    This implementation uses scipy.sparse block matrices for efficient memory usage
    and faster operations on large multiplex networks. The supra-adjacency matrix
    is constructed with intralayer adjacency matrices on the diagonal blocks and
    identity matrices for interlayer coupling.

    Complexity: O(E + N*L) where E is edges, N nodes per layer, L layers
    Memory: O(E + N*L) sparse vs O(N²*L²) dense

    Args:
        core_network: NetworkX graph with multiplex structure

    Returns:
        Tuple of (numeric_network, node_order)
            - numeric_network: scipy.sparse.csr_matrix supra-adjacency matrix
            - node_order: list of (node_id, layer) tuples in matrix order
    """
    import scipy.sparse as sp

    unique_layers = sorted({n[1] for n in core_network.nodes()})
    num_layers = len(unique_layers)
    individual_adj_sparse = []
    all_nodes = []
    layer_sizes = []

    # Build sparse adjacency matrix for each layer
    # Using sparse matrices from the start avoids dense intermediate arrays
    for layer in unique_layers:
        layer_nodes = [n for n in core_network.nodes() if n[1] == layer]
        H = core_network.subgraph(layer_nodes)

        # Use nx_to_scipy_sparse_matrix for direct sparse conversion
        adj_sparse = nx_to_scipy_sparse_matrix(H)

        all_nodes += list(H.nodes())
        individual_adj_sparse.append(adj_sparse)
        layer_sizes.append(adj_sparse.shape[0])

    # Construct supra-adjacency matrix using sparse block matrices
    # This avoids creating large dense arrays and is memory-efficient
    # Block structure: diagonal blocks = intralayer adjacency, off-diagonal = identity (coupling)
    block_rows = []
    for i, adj_i in enumerate(individual_adj_sparse):
        n_i = layer_sizes[i]
        row_blocks = []
        for j in range(num_layers):
            n_j = layer_sizes[j]
            if i == j:
                # Diagonal block: intralayer adjacency matrix
                row_blocks.append(adj_i)
            else:
                # Off-diagonal block: identity matrix for interlayer coupling
                # Only create identity if dimensions match (multiplex assumption)
                if n_i == n_j:
                    row_blocks.append(sp.identity(n_i, format='csr'))
                else:
                    # For non-multiplex or layers with different sizes, use zeros
                    row_blocks.append(sp.csr_matrix((n_i, n_j)))

        # Horizontally stack blocks for this layer's row
        block_rows.append(sp.hstack(row_blocks, format='csr'))

    # Vertically stack all block rows to form supra-adjacency matrix
    vectors = sp.vstack(block_rows, format='csr')
    return vectors, all_nodes


class multi_layer_network:
    """Main class for multilayer network analysis and manipulation.

    This class provides a comprehensive toolkit for creating, analyzing, and
    visualizing multilayer networks where nodes can exist in multiple layers
    and edges can connect nodes within or across layers.

    Supported Network Types (network_type parameter):
        - **multilayer** (default): General multilayer networks with arbitrary
          layer structure. Each layer can have a different set of nodes.
          Suitable for heterogeneous networks (e.g., authors-papers-venues)
          or networks where nodes naturally appear in only some layers.

        - **multiplex**: Special case where all layers share the same node set
          but with different edge types. After loading a network, automatic
          coupling edges are created between each node and its counterparts
          in other layers. Suitable for social networks with multiple
          relationship types (e.g., friend, colleague, family layers).

    Choosing the Right Network Type:
        ===============  ==================  ==================
        Criterion        multilayer          multiplex
        ===============  ==================  ==================
        Node sets        Different per layer Same across layers
        Coupling edges   Manual (explicit)   Automatic
        Use case         Heterogeneous nets  Same entities, many
                         (author-paper)      relationship types
        ===============  ==================  ==================

    Key Features:
        - Dict-based API for adding nodes and edges (see add_nodes() and add_edges())
        - NetworkX interoperability via to_networkx() and from_networkx()
        - Multiple I/O formats (edgelist, GML, GraphML, gpickle, etc.)
        - Visualization methods for multilayer layouts
        - Community detection and centrality analysis
        - Random walk and embedding generation

    Hypergraph Support:
        This class does NOT natively support true hypergraphs (edges connecting
        more than two nodes). For hypergraph-like structures, consider:
        - Using bipartite projections (nodes and hyperedges as separate node types)
        - The incidence gadget encoding via to_homogeneous_hypergraph()
        - External hypergraph libraries with conversion utilities

    Notes:
        - Nodes in multilayer networks are represented as (node_id, layer) tuples
        - Use add_nodes() and add_edges() with dict format for easiest interaction
        - See examples/ directory for usage patterns and best practices

    Examples:
        >>> # Create a general multilayer network (different node sets per layer)
        >>> net = multi_layer_network(network_type='multilayer', directed=False)
        >>>
        >>> # Add nodes to different layers
        >>> _ = net.add_nodes([
        ...     {'source': 'A', 'type': 'social'},
        ...     {'source': 'B', 'type': 'social'},
        ...     {'source': 'A', 'type': 'email'}  # Same node, different layer
        ... ])
        >>>
        >>> # Add edges (intra-layer and inter-layer)
        >>> _ = net.add_edges([
        ...     {'source': 'A', 'target': 'B',
        ...      'source_type': 'social', 'target_type': 'social'},
        ...     {'source': 'A', 'target': 'A',
        ...      'source_type': 'social', 'target_type': 'email'}
        ... ])
        >>>
        >>> print(net)  # Shows network statistics
        <multi_layer_network: type=multilayer, directed=False, nodes=3, edges=2, layers=2>

        >>> # Create a multiplex network (same nodes across relationship layers)
        >>> # Note: coupling edges are auto-added after load_network()
        >>> multiplex_net = multi_layer_network(network_type='multiplex')
    """

    def __init__(
        self,
        verbose: bool = True,
        network_type: str = "multilayer",
        directed: bool = True,
        dummy_layer: str = "null",
        label_delimiter: str = "---",
        coupling_weight: Union[int, float] = 1,
    ) -> None:
        """Initialize a multilayer network.

        Args:
            verbose: Enable verbose logging output
            network_type: Type of network. Must be one of:

                - ``'multilayer'`` (default): General multilayer network where each layer
                  can have a different set of nodes. Edges can connect any nodes within
                  or across layers. Use this when layers represent different node types
                  (heterogeneous networks) or when nodes don't need to be present in all
                  layers.

                - ``'multiplex'``: Special case where all layers share the same node set.
                  After loading, automatic coupling edges are created between each node
                  and its counterparts in other layers. Use this when the same entities
                  (e.g., people, cities) are connected via multiple relationship types
                  (e.g., friendship, professional ties).

            directed: Whether the network is directed
            dummy_layer: Name for dummy/placeholder layer
            label_delimiter: Delimiter used to separate layer names in node labels
            coupling_weight: Default weight for inter-layer coupling edges in multiplex
                networks. Only applies when network_type='multiplex'.

        Raises:
            ValueError: If network_type is not 'multilayer' or 'multiplex' (raised
                during get_edges() or other operations that depend on network_type).

        Examples:
            >>> # General multilayer network (different node sets per layer)
            >>> net = multi_layer_network(network_type='multilayer')
            >>> net.add_edges([
            ...     {'source': 'author1', 'target': 'paper1',
            ...      'source_type': 'authors', 'target_type': 'papers'}
            ... ])
            <multi_layer_network: type=multilayer, directed=True, nodes=2, edges=1, layers=2>

            >>> # Multiplex network (same nodes, different relationship types)
            >>> net = multi_layer_network(network_type='multiplex')
            >>> # After loading, coupling edges are auto-generated between layers

        See Also:
            - :doc:`/concepts/multilayer_networks_101` for conceptual background
            - :meth:`load_network` for loading from files with network_type behavior
            - :meth:`get_edges` for how network_type affects edge iteration

        """
        # initialize the class
        self.coupling_weight: Union[int, float] = coupling_weight
        self.layer_name_map: Dict[str, int] = {}
        self.layer_inverse_name_map: Dict[int, str] = {}
        self.core_network: Optional[Union[nx.MultiGraph, nx.MultiDiGraph]] = None
        self.directed: bool = directed
        self.node_order_in_matrix: Optional[List[Any]] = None
        self.dummy_layer: str = dummy_layer
        self.numeric_core_network: Optional[Any] = None
        self.labels: Optional[Any] = None
        self.embedding: Optional[Any] = None
        self.verbose: bool = verbose
        self.network_type: str = network_type  # assing network type
        self.sparse_enabled: bool = False
        self.hinmine_network: Optional[Any] = None
        self.label_delimiter: str = label_delimiter

    # ═════════════════════════════════════════════════════════════════════════
    # Core Data Access Methods
    # ═════════════════════════════════════════════════════════════════════════

    def __getitem__(self, i, j=None):
        """Access network nodes using dictionary-like syntax.

        Args:
            i: Node identifier
            j: Optional second node identifier for edge access

        Returns:
            Node neighbors if j is None, else edge data
        """
        if j is None:
            return self.core_network[i]
        else:
            return self.core_network[i][j]

    def __repr__(self) -> str:
        """Return a string representation of the network with statistics.

        Returns:
            str: Network statistics including type, nodes, edges, and layers
        """
        if self.core_network is None:
            return f"<multi_layer_network (empty): type={self.network_type}, directed={self.directed}>"

        try:
            num_nodes = self.core_network.number_of_nodes()
            num_edges = self.core_network.number_of_edges()

            # Count unique layers
            try:
                unique_layers = len({n[1] for n in self.core_network.nodes() if isinstance(n, tuple) and len(n) >= 2})
            except (TypeError, IndexError):
                unique_layers = 1  # Fallback for non-multilayer networks

            return (f"<multi_layer_network: "
                   f"type={self.network_type}, "
                   f"directed={self.directed}, "
                   f"nodes={num_nodes}, "
                   f"edges={num_edges}, "
                   f"layers={unique_layers}>")
        except Exception:
            # Fallback for unusual cases
            return f"<multi_layer_network: type={self.network_type}, directed={self.directed}>"

    def __len__(self) -> int:
        """Return the number of nodes in the network.

        This enables using len() on network objects for quick size checks.

        Returns:
            int: Number of nodes in the network, or 0 if empty

        Examples:
            >>> net = multi_layer_network()
            >>> len(net)
            0
            >>> _ = net.add_nodes([{'source': 'A', 'type': 'layer1'}])
            >>> len(net)
            1
        """
        if self.core_network is None:
            return 0
        return self.core_network.number_of_nodes()

    def __bool__(self) -> bool:
        """Return True if the network has nodes.

        This enables using network objects in boolean contexts.

        Returns:
            bool: True if network has at least one node, False otherwise

        Examples:
            >>> net = multi_layer_network()
            >>> bool(net)
            False
            >>> _ = net.add_nodes([{'source': 'A', 'type': 'layer1'}])
            >>> bool(net)
            True
            >>> if net:
            ...     print("Network has nodes")
            Network has nodes
        """
        return len(self) > 0

    def __contains__(self, item: Any) -> bool:
        """Check if a node or edge exists in the network.

        Supports checking for:
        - Node tuples: (node_id, layer)
        - Edge tuples: ((source_node, source_layer), (target_node, target_layer))

        Args:
            item: Node tuple or edge tuple to check

        Returns:
            bool: True if item exists in network

        Examples:
            >>> net = multi_layer_network()
            >>> _ = net.add_nodes([{'source': 'A', 'type': 'layer1'}])
            >>> ('A', 'layer1') in net
            True
            >>> ('B', 'layer1') in net
            False
        """
        if self.core_network is None:
            return False

        # Check if it's an edge (tuple of two tuples)
        if (isinstance(item, tuple) and len(item) == 2 and
            isinstance(item[0], tuple) and isinstance(item[1], tuple)):
            return self.core_network.has_edge(item[0], item[1])

        # Otherwise treat as a node
        return self.core_network.has_node(item)

    def __iter__(self):
        """Iterate over nodes in the network.

        Yields:
            Node tuples (node_id, layer)

        Examples:
            >>> net = multi_layer_network()
            >>> _ = net.add_nodes([{'source': 'A', 'type': 'layer1'}])
            >>> for node in net:
            ...     print(node)
            ('A', 'layer1')
        """
        if self.core_network is None:
            return iter([])
        return iter(self.core_network.nodes())

    # ─────────────────────────────────────────────────────────────────────────
    # Property Accessors for Common Attributes
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def node_count(self) -> int:
        """Number of nodes in the network.

        Returns:
            int: Total count of nodes (node-layer pairs)

        Examples:
            >>> net = multi_layer_network()
            >>> _ = net.add_nodes([{'source': 'A', 'type': 'layer1'}])
            >>> net.node_count
            1
        """
        return len(self)

    @property
    def edge_count(self) -> int:
        """Number of edges in the network.

        Returns:
            int: Total count of edges

        Examples:
            >>> net = multi_layer_network()
            >>> _ = net.add_edges([{'source': 'A', 'target': 'B',
            ...                 'source_type': 'layer1', 'target_type': 'layer1'}])
            >>> net.edge_count
            1
        """
        if self.core_network is None:
            return 0
        return self.core_network.number_of_edges()

    @property
    def layer_count(self) -> int:
        """Number of unique layers in the network.

        Returns:
            int: Count of distinct layers

        Examples:
            >>> net = multi_layer_network()
            >>> _ = net.add_nodes([
            ...     {'source': 'A', 'type': 'layer1'},
            ...     {'source': 'B', 'type': 'layer2'}
            ... ])
            >>> net.layer_count
            2
        """
        if self.core_network is None:
            return 0
        try:
            return len({n[1] for n in self.core_network.nodes()
                       if isinstance(n, tuple) and len(n) >= 2})
        except (TypeError, IndexError):
            return 0

    @property
    def layers(self) -> List[Any]:
        """List of unique layer identifiers in the network.

        Returns:
            list: Sorted list of layer identifiers

        Examples:
            >>> net = multi_layer_network()
            >>> _ = net.add_nodes([
            ...     {'source': 'A', 'type': 'social'},
            ...     {'source': 'B', 'type': 'work'}
            ... ])
            >>> net.layers
            ['social', 'work']
        """
        if self.core_network is None:
            return []
        try:
            unique_layers = {n[1] for n in self.core_network.nodes()
                            if isinstance(n, tuple) and len(n) >= 2}
            return sorted(unique_layers)
        except (TypeError, IndexError):
            return []

    @property
    def is_empty(self) -> bool:
        """Check if the network is empty (has no nodes).

        Returns:
            bool: True if network has no nodes

        Examples:
            >>> net = multi_layer_network()
            >>> net.is_empty
            True
            >>> _ = net.add_nodes([{'source': 'A', 'type': 'layer1'}])
            >>> net.is_empty
            False
        """
        return len(self) == 0

    # ─────────────────────────────────────────────────────────────────────────
    # Convenience Factory Methods
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def from_edges(
        cls,
        edges: List[Union[Dict, List]],
        network_type: str = "multilayer",
        directed: bool = False,
        input_type: str = "dict",
    ) -> "multi_layer_network":
        """Create a multilayer network directly from a list of edges.

        This is a convenience factory method that creates a network and populates
        it with edges in a single call, supporting method chaining patterns.

        Args:
            edges: List of edges in dict or list format
            network_type: Type of network ('multilayer' or 'multiplex')
            directed: Whether the network is directed
            input_type: Format of edge data ('dict' or 'list')

        Returns:
            multi_layer_network: New network instance with edges added

        Examples:
            >>> # Create from dict format
            >>> net = multi_layer_network.from_edges([
            ...     {'source': 'A', 'target': 'B',
            ...      'source_type': 'layer1', 'target_type': 'layer1'},
            ...     {'source': 'B', 'target': 'C',
            ...      'source_type': 'layer1', 'target_type': 'layer1'}
            ... ])
            >>> len(net)
            3

            >>> # Create from list format
            >>> net = multi_layer_network.from_edges([
            ...     ['A', 'layer1', 'B', 'layer1', 1],
            ...     ['B', 'layer1', 'C', 'layer1', 1]
            ... ], input_type='list')
            >>> net.edge_count
            2
        """
        net = cls(network_type=network_type, directed=directed, verbose=False)
        net.add_edges(edges, input_type=input_type)
        return net

    # ═════════════════════════════════════════════════════════════════════════
    # I/O Operations - Loading and Saving Networks
    # ═════════════════════════════════════════════════════════════════════════

    def read_ground_truth_communities(self, cfile):
        """
        Parse ground truth community file and make mappings to the original nodes. This works based on node ID mappings, exact node,layer tuplets are to be added.
        Args:
            param1: ground truth communities.
        Returns:
            self.ground_truth_communities
        """

        community_assignments = {}
        with open(cfile) as cf:
            for line in cf:
                line = line.strip().split()
                community_assignments[line[0]] = line[1]

        self.ground_truth_communities = {}
        # reorder the mampings appropriately
        for node in self.get_nodes():
            com = community_assignments[node[0]]
            self.ground_truth_communities[node] = com

    def load_network(
        self,
        input_file: Optional[str] = None,
        directed: bool = False,
        input_type: str = "gml",
        label_delimiter: str = "---",
    ) -> "multi_layer_network":
        """Load a network from file.

        This method loads and prepares a given network. The behavior depends on
        the ``network_type`` set during initialization:

        - **multilayer**: Network is loaded as-is. No automatic edges are added.
        - **multiplex**: After loading, coupling edges are automatically created
          between each node and its counterparts in other layers. These edges
          have type='coupling' and can be filtered via get_edges().

        Args:
            input_file: Path to the network file to load
            directed: Whether the network is directed
            input_type: Format of the input file. Supported values:
                - 'gml': Graph Modeling Language format
                - 'graphml': GraphML XML format
                - 'edgelist': Simple edge list (source target [weight])
                - 'multiedgelist': Multilayer edge list (node1 layer1 node2 layer2 weight)
                - 'multiplex_edges': Multiplex format (layer node1 node2 weight)
                - 'multiplex_folder': Folder with layer files
                - 'gpickle': Python pickle format
                - 'nx': NetworkX graph object
                - 'sparse': Sparse matrix format
            label_delimiter: Delimiter used to separate layer names in node labels

        Returns:
            Self for method chaining. Populates self.core_network, self.labels,
            and self.activity.

        Note:
            For multiplex networks, use input_type='multiplex_edges' or
            'multiplex_folder' with network_type='multiplex' to get automatic
            coupling edges.

        Examples:
            >>> # Load multilayer network (no automatic coupling)
            >>> net = multi_layer_network(network_type='multilayer')
            >>> net.load_network('data.gml', input_type='gml')  # doctest: +SKIP

            >>> # Load multiplex network (automatic coupling edges)
            >>> net = multi_layer_network(network_type='multiplex')
            >>> net.load_network('data.edges', input_type='multiplex_edges')  # doctest: +SKIP

        """
        # crosshair: analysis_kind=asserts
        # Precondition: input_type must be from supported set
        SUPPORTED = {"edgelist", "multiedgelist", "multiplex_edges", "multiplex_folder", "gml", "gpickle", "gpickle_biomine", "graphml", "nx", "sparse"}
        assert input_type in SUPPORTED, f"input_type must be one of {SUPPORTED}, got {input_type}"

        # Precondition: if not nx type, input_file should be provided
        if input_type != "nx":
            assert input_file is not None, "input_file must be provided for non-nx input types"

        self.input_file = input_file
        self.input_type = input_type
        self.directed = directed
        self.temporal_edges = None
        self.label_delimiter = label_delimiter
        if input_type == "sparse":
            self.sparse_enabled = True

        self.core_network, self.labels, self.activity = parsers.parse_network(
            self.input_file,
            self.input_type,
            directed=self.directed,
            label_delimiter=self.label_delimiter,
            network_type=self.network_type,
        )

        if self.network_type == "multiplex":
            self.monitor("Checking multiplex edges..")
            self._couple_all_edges()

        # Postconditions: core_network should be valid
        assert self.core_network is not None, "core_network must be initialized"

        # Only check node/edge counts for NetworkX graphs (not sparse matrices)
        if hasattr(self.core_network, 'number_of_nodes'):
            assert self.core_network.number_of_nodes() >= 0, "node count must be non-negative"
            assert self.core_network.number_of_edges() >= 0, "edge count must be non-negative"

        # Postcondition: if directed=False, graph should be undirected
        if not directed and self.core_network is not None:
            assert not isinstance(self.core_network, (nx.DiGraph, nx.MultiDiGraph)), \
                "core_network should not be directed when directed=False"

        return self

    def _couple_all_edges(self):
        """Create coupling edges between same nodes across all layers (multiplex only).

        This method is automatically called when loading a multiplex network
        (network_type='multiplex'). It creates bidirectional coupling edges
        connecting each node to its counterparts in all other layers.

        For example, if node 'A' exists in layers 'L1' and 'L2', coupling edges
        are created: ('A', 'L1') <-> ('A', 'L2').

        Coupling edges have:
            - type='coupling' (used to filter them in get_edges())
            - weight=self.coupling_weight (default 1)

        Note:
            This is an internal method called by load_network() when
            network_type='multiplex'. Users typically don't call this directly.

        See Also:
            - :meth:`__init__` for setting coupling_weight
            - :meth:`get_edges` for filtering coupling edges (multiplex_edges param)
        """
        unique_layers = {n[1] for n in self.core_network.nodes()}
        unique_nodes = {n[0] for n in self.core_network.nodes()}

        #        for potential_node in itertools.product(unique_nodes,unique_layers):
        #            self.core_network.add_node(potential_node)

        # draw edges between same nodes accross layers
        for node in unique_nodes:
            for layer_first in unique_layers:
                for layer_second in unique_layers:
                    if layer_first != layer_second:
                        coupled_edge = ((node, layer_first), (node, layer_second))
                        self.core_network.add_edge(
                            coupled_edge[0],
                            coupled_edge[1],
                            type="coupling",
                            weight=self.coupling_weight,
                        )

    def load_layer_name_mapping(self, mapping_name, header=False):
        """Layer-node mapping loader method

        Args:
            param1: The name of the mapping file.

        Returns:
            self.layer_name_map is filled, returns nothing.

        """

        with open(mapping_name, "r+") as lf:
            if header:
                lf.readline()
            for line in lf:
                lid, lname = line.strip().split(" ")
                self.layer_name_map[lname] = lid
                self.layer_inverse_name_map[lid] = lname

    def load_network_activity(self, activity_file):
        """Network activity loader

                Args:
                    param1: The name of the generic activity file -> 65432 61888 1377688175 RE
        , n1 n2 timestamp and layer name. Note that layer node mappings MUST be loaded in order to map nodes to activity properly.

                Returns:
                   self.activity is filled.

        """

        self.activity = parsers.load_edge_activity_raw(
            activity_file, self.layer_name_map
        )
        self.activity = self.activity.sort_values(by=["timestamp"])

    def to_json(self):
        """A method for exporting the graph to a json file

        Args:
        self

        """

        from networkx.readwrite import json_graph

        data = json_graph.node_link_data(self.core_network)
        return data

    def to_sparse_matrix(self, replace_core=False, return_only=False):
        """
        Conver the matrix to scipy-sparse version. This is useful for classification.
        """
        if return_only:
            return nx_to_scipy_sparse_matrix(self.core_network)

        if replace_core:
            self.core_network = nx_to_scipy_sparse_matrix(self.core_network)
            self.core_sparse = None
        else:
            self.core_sparse = nx_to_scipy_sparse_matrix(self.core_network)

    def load_temporal_edge_information(
        self,
        input_file=None,
        input_type="edge_activity",
        directxed=False,
        layer_mapping=None,
    ):
        """A method for loading temporal edge information"""

        self.temporal_edges = parsers.load_temporal_edge_information(
            input_file, input_type=input_type, layer_mapping=layer_mapping
        )

    # ═════════════════════════════════════════════════════════════════════════
    # Utility and Helper Methods
    # ═════════════════════════════════════════════════════════════════════════

    def monitor(self, message):
        """A simple monitor method for logging"""

        logger.info("-" * 20)
        logger.info(message)
        logger.info("-" * 20)

    def get_neighbors(self, node_id: str, layer_id: Optional[str] = None) -> Any:
        """Get neighbors of a node in a specific layer.

        Args:
            node_id: Node identifier
            layer_id: Layer identifier (optional)

        Returns:
            Iterator of neighbor nodes
        """
        return self.core_network.neighbors((node_id, layer_id))

    # ═════════════════════════════════════════════════════════════════════════
    # Network Transformation and Conversion Methods
    # ═════════════════════════════════════════════════════════════════════════

    def invert(self, override_core=False):
        """
        invert the nodes to edges. Get the "edge graph". Each node is here an edge.
        """

        # default structure for a new graph
        G = nx.MultiGraph()
        new_edges = []
        for node in self.core_network.nodes():
            ngs = [(neigh, node) for neigh in self.core_network[node] if neigh != node]
            if len(ngs) > 0:
                pairs = itertools.combinations(ngs, 2)
                new_edges += list(pairs)

        for edge in new_edges:
            G.add_edge(edge[0], edge[1])

        if override_core:
            self.core_network = G
        else:
            self.core_network_inverse = G  # .add_edges_from(new_edges)

    def save_network(self, output_file=None, output_type="edgelist"):
        """Save the network to a file in various formats.

        This method exports the multilayer network to different file formats
        for persistence, sharing, or use with other tools.

        Args:
            output_file: Path where the network should be saved
            output_type: Format for saving ('edgelist', 'multiedgelist',
                        'multiedgelist_encoded', or 'gpickle')

        Supported Formats:
            - 'edgelist': Simple edge list format (standard NetworkX)
            - 'multiedgelist': Multilayer edge list with layer information
            - 'multiedgelist_encoded': Multilayer edge list with integer encoding
            - 'gpickle': Python pickle format (preserves all attributes)

        Examples:
            >>> net = multi_layer_network()
            >>> _ = net.add_nodes([{'source': 'A', 'type': 'layer1'}])
            >>> _ = net.add_edges([{'source': 'A', 'target': 'B',
            ...                 'source_type': 'layer1', 'target_type': 'layer1'}])
            >>> net.save_network('network.txt', output_type='multiedgelist')

            >>> # For faster I/O with all metadata preserved
            >>> net.save_network('network.gpickle', output_type='gpickle')

        Notes:
            - 'gpickle' format preserves all node/edge attributes
            - 'multiedgelist_encoded' creates node_map and layer_map attributes
            - Edge weights and types are preserved in supported formats
        """
        if output_type == "edgelist":
            parsers.save_edgelist(self.core_network, output_file=output_file)

        if output_type == "multiedgelist_encoded":
            self.node_map, self.layer_map = parsers.save_multiedgelist(
                self.core_network, output_file=output_file, encode_with_ints=True
            )

        if output_type == "multiedgelist":
            parsers.save_multiedgelist(self.core_network, output_file=output_file)

        if output_type == "gpickle":
            parsers.save_gpickle(self.core_network, output_file=output_file)

    def add_dummy_layers(self):
        """
        Internal function, for conversion between objects
        """

        self.tmp_core_network = self.core_network
        self.core_network = self._create_graph()

        for edge in self.tmp_core_network.edges():
            self.add_edges(
                {
                    "source": edge[0],
                    "target": edge[1],
                    "source_type": self.dummy_layer,
                    "target_type": self.dummy_layer,
                }
            )
        del self.tmp_core_network
        return self

    def sparse_to_px(self, directed=None):
        """Convert sparse matrix to py3plex format

        Args:
            directed: Whether the network is directed (uses self.directed if None)
        """

        if directed is None:
            directed = self.directed

        self.core_network = nx_from_scipy_sparse_matrix(
            self.core_network, create_using=(nx.DiGraph() if directed else nx.Graph())
        )
        self.add_dummy_layers()
        self.sparse_enabled = False

    # ═════════════════════════════════════════════════════════════════════════
    # Network Statistics and Analysis Methods
    # ═════════════════════════════════════════════════════════════════════════

    def summary(self):
        """Generate a summary of network statistics.

        Computes and returns key metrics about the multilayer network structure.

        Returns:
            dict: Network statistics including:
                - 'Number of layers': Count of unique layers
                - 'Nodes': Total number of nodes
                - 'Edges': Total number of edges
                - 'Mean degree': Average node degree
                - 'CC': Number of connected components

        Examples:
            >>> net = multi_layer_network()
            >>> _ = net.add_nodes([{'source': 'A', 'type': 'layer1'}])
            >>> _ = net.add_edges([{'source': 'A', 'target': 'B',
            ...                 'source_type': 'layer1', 'target_type': 'layer1'}])
            >>> stats = net.summary()
            >>> print(f"Network has {stats['Nodes']} nodes and {stats['Edges']} edges")
            Network has 2 nodes and 1 edges

        Notes:
            - Connected components are computed on the undirected version
            - Mean degree is averaged across all nodes in all layers
        """

        unique_layers = len({n[1] for n in self.core_network.nodes()})
        nodes = len(self.core_network.nodes())
        edges = len(self.core_network.edges())
        components = len(
            list(nx.connected_components(self.core_network.to_undirected()))
        )
        node_degree_vector = dict(nx.degree(self.core_network)).values()
        mean_degree = np.mean(list(node_degree_vector))
        return {
            "Number of layers": unique_layers,
            "Nodes": nodes,
            "Edges": edges,
            "Mean degree": mean_degree,
            "CC": components,
        }

    def get_unique_entity_counts(self):
        """Count unique entities in the network.

        Returns:
            tuple: (total_unique_nodes, unique_node_ids, nodes_per_layer)
                - total_unique_nodes: count of unique (node, layer) tuples
                - unique_node_ids: count of unique node IDs (across all layers)
                - nodes_per_layer: dict mapping layer to count of nodes in that layer
        """

        unique_node_layer_tuples = set()
        unique_node_ids = set()
        nodes_per_layer = {}

        # Iterate through all nodes (which are (node_id, layer) tuples in multilayer networks)
        for node in self.get_nodes():
            # Add the entire (node_id, layer) tuple as unique
            unique_node_layer_tuples.add(node)

            # Extract node_id and layer if node is a tuple
            if isinstance(node, tuple) and len(node) >= 2:
                node_id, layer = node[0], node[1]
                unique_node_ids.add(node_id)

                # Count nodes per layer
                if layer not in nodes_per_layer:
                    nodes_per_layer[layer] = set()
                nodes_per_layer[layer].add(node)
            else:
                # For simple networks without layers, just count the node
                unique_node_ids.add(node)

        # Convert per-layer node sets to counts
        nodes_per_layer_counts = {
            layer: len(nodes) for layer, nodes in nodes_per_layer.items()
        }

        return (
            len(unique_node_layer_tuples),
            len(unique_node_ids),
            nodes_per_layer_counts,
        )

    def basic_stats(self, target_network=None):
        """A method for obtaining a network's statistics.

        Displays:
        - Basic network info (nodes, edges)
        - Total unique nodes (counting each (node, layer) as unique)
        - Unique node IDs (across all layers)
        - Per-layer node counts
        """

        if self.sparse_enabled:
            self.monitor(
                "Only sparse matrix is loaded for efficiency! Converting to .px for this task!"
            )
        else:

            if self.verbose:
                self.monitor("Computing core stats of the network")

            if target_network is None:
                logger.info(nx_info(self.core_network))
                total_nodes, unique_ids, nodes_per_layer = (
                    self.get_unique_entity_counts()
                )
                logger.info(
                    f"Number of unique nodes (as node-layer tuples): {total_nodes}"
                )
                logger.info(
                    f"Number of unique node IDs (across all layers): {unique_ids}"
                )

                if nodes_per_layer:
                    logger.info("Nodes per layer:")
                    for layer, count in sorted(nodes_per_layer.items()):
                        logger.info(f"  Layer '{layer}': {count} nodes")

            else:
                logger.info(nx_info(target_network))
                total_nodes, unique_ids, nodes_per_layer = (
                    self.get_unique_entity_counts()
                )
                logger.info(
                    f"Number of unique nodes (as node-layer tuples): {total_nodes}"
                )
                logger.info(
                    f"Number of unique node IDs (across all layers): {unique_ids}"
                )

                if nodes_per_layer:
                    logger.info("Nodes per layer:")
                    for layer, count in sorted(nodes_per_layer.items()):
                        logger.info(f"  Layer '{layer}': {count} nodes")

    def to_networkx(self) -> nx.Graph:
        """Convert the multilayer network to a NetworkX graph.

        Returns a copy of the core network as a NetworkX graph. The returned graph
        preserves all node and edge attributes, including layer information for
        multilayer networks (where nodes are typically (node_id, layer) tuples).

        Returns:
            nx.Graph: A NetworkX graph (MultiGraph or MultiDiGraph depending on network type)

        Examples:
            >>> net = multi_layer_network(directed=False)
            >>> _ = net.add_nodes([{'source': 'A', 'type': 'layer1'}])
            >>> nx_graph = net.to_networkx()
            >>> print(type(nx_graph))
            <class 'networkx.classes.multigraph.MultiGraph'>

        Notes:
            - For multilayer networks, nodes are tuples: (node_id, layer)
            - All edge attributes (weight, type, etc.) are preserved
            - The returned graph is a copy, not a reference
        """
        if self.core_network is None:
            raise ValueError("Network is empty. Load or create a network first.")

        return self.core_network.copy()

    @classmethod
    def from_networkx(cls, G: nx.Graph, network_type: str = "multilayer",
                     directed: Optional[bool] = None) -> "multi_layer_network":
        """Create a multi_layer_network from a NetworkX graph.

        This class method converts a NetworkX graph into a py3plex multi_layer_network.
        For multilayer networks, nodes should be tuples of (node_id, layer).

        Args:
            G: NetworkX graph to convert
            network_type: Type of network ('multilayer' or 'multiplex')
            directed: Whether to treat the network as directed. If None, inferred from G.

        Returns:
            multi_layer_network: A new multi_layer_network instance

        Examples:
            >>> import networkx as nx
            >>> G = nx.Graph()
            >>> G.add_nodes_from([('A', 'layer1'), ('B', 'layer1')])
            >>> G.add_edge(('A', 'layer1'), ('B', 'layer1'))
            >>> net = multi_layer_network.from_networkx(G)
            >>> print(net)
            <multi_layer_network: type=multilayer, directed=False, nodes=2, edges=1, layers=1>

        Notes:
            - For proper multilayer behavior, ensure nodes are (node_id, layer) tuples
            - Edge attributes are preserved during conversion
            - The input graph is copied, not referenced
        """
        if directed is None:
            directed = G.is_directed()

        # Create new instance
        net = cls(network_type=network_type, directed=directed, verbose=False)

        # Copy the graph
        net.core_network = G.copy()

        return net

    def get_edges(self, data: bool = False, multiplex_edges: bool = False) -> Any:
        """Iterate over edges in the network.

        This method behaves differently based on the network_type:

        - **multilayer**: Returns all edges without filtering.
        - **multiplex**: By default, filters out coupling edges (auto-generated
          inter-layer edges connecting each node to itself in other layers).
          Set multiplex_edges=True to include coupling edges.

        Args:
            data: If True, return edge data along with edge tuples
            multiplex_edges: If True, include coupling edges in multiplex networks.
                Only relevant when network_type='multiplex'. Coupling edges are
                automatically added to connect each node to its counterparts
                in other layers.

        Yields:
            Edge tuples, optionally with data. For multiplex networks with
            multiplex_edges=False, coupling edges are excluded.

        Raises:
            ValueError: If network_type is not 'multilayer' or 'multiplex'.

        Examples:
            >>> net = multi_layer_network(network_type='multilayer')
            >>> net.add_edges([
            ...     {'source': 'A', 'target': 'B',
            ...      'source_type': 'layer1', 'target_type': 'layer1'}
            ... ])
            <multi_layer_network: type=multilayer, directed=True, nodes=2, edges=1, layers=1>
            >>> list(net.get_edges())
            [(('A', 'layer1'), ('B', 'layer1'))]

        See Also:
            - :meth:`__init__` for the difference between multilayer and multiplex
            - :meth:`_couple_all_edges` for how coupling edges are created
        """
        if self.network_type == "multilayer":
            for edge in self.core_network.edges(data=data):
                yield edge

        elif self.network_type == "multiplex":
            if not multiplex_edges:
                for edge in self.core_network.edges(data=data, keys=True):
                    if data:
                        _, _, key, attr = edge
                    else:
                        u, v, key = edge
                        attr = self.core_network.get_edge_data(u, v, key=key)

                    if attr.get("type") == "coupling":
                        continue

                    yield edge
            else:
                for edge in self.core_network.edges(data=data):
                    yield edge
        else:
            raise ValueError(
                f"Invalid network_type: '{self.network_type}'. "
                f"Expected 'multilayer' or 'multiplex'. "
                f"Use 'multilayer' for heterogeneous networks (different node sets per layer) "
                f"or 'multiplex' for same-node-set networks with automatic coupling. "
                f"Set network_type during initialization: "
                f"multi_layer_network(network_type='multilayer')"
            )

    def get_nodes(self, data: bool = False) -> Any:
        """A method for obtaining a network's nodes

        Args:
            data: If True, return node data along with node identifiers

        Yields:
            Node identifiers, optionally with data
        """

        yield from self.core_network.nodes(data=data)

    def merge_with(self, target_px_object):
        """
        Merge two px objects.
        """

        all_edges = []
        for edge in target_px_object.get_edges(data=True):
            n1_name = edge[0][0]
            n1_type = edge[0][1]
            n2_name = edge[1][0]
            n2_type = edge[1][1]
            edge_type = edge[2].get("type")
            edge_weight = edge[2].get("weight")
            edge_obj = {
                "source": n1_name,
                "target": n2_name,
                "type": edge_type,
                "source_type": n1_type,
                "target_type": n2_type,
            }
            if edge_weight is not None:
                edge_obj["weight"] = edge_weight
            all_edges.append(edge_obj)

        self.add_edges(all_edges)
        return self

    def subnetwork(self, input_list=None, subset_by="node_layer_names"):
        """
        Construct a subgraph based on a set of nodes.
        """

        input_list = set(input_list)
        if subset_by == "layers":
            subnetwork = self.core_network.subgraph(
                [n for n in self.core_network.nodes() if n[1] in input_list]
            )

        elif subset_by == "node_names":
            subnetwork = self.core_network.subgraph(
                [n for n in self.core_network.nodes() if n[0] in input_list]
            )

        elif subset_by == "node_layer_names":
            subnetwork = self.core_network.subgraph(
                [n for n in self.core_network.nodes() if n in input_list]
            )

        else:
            self.monitor("Please, select layers of node_names options..")

        tmp_net = multi_layer_network()
        tmp_net.core_network = subnetwork
        return tmp_net

    @require(
        lambda self: self.core_network is not None, "core_network must be initialized"
    )
    @require(
        lambda metric: metric in {"count", "mean", "max", "sum"},
        "metric must be valid aggregation method",
    )
    @ensure(lambda result: result is not None, "result must not be None")
    @ensure(
        lambda result: isinstance(result, (nx.Graph, nx.DiGraph)),
        "result must be a NetworkX graph",
    )
    def aggregate_edges(self, metric="count", normalize_by="degree"):
        """Edge aggregation method

        Count weights across layers and return a weighted network

        Args:
            param1: aggregation operator (count is default)
            param2: normalization of the values

        Returns:
             A simplified network.

        """

        layer_object = defaultdict(list)
        edge_object = {}

        for node in self.get_nodes():
            layer_object[node[1]].append(node)

        for layer, nodes in layer_object.items():
            layer_network = self.subnetwork(nodes)

            if normalize_by != "raw":
                nx_func = getattr(nx, normalize_by)
                connectivity = np.mean([x[1] for x in nx_func(layer_network.core_network)])
            else:
                connectivity = 1

            for edge in layer_network.get_edges():
                edge_new = (edge[0][0], edge[1][0])  # keep just the nids.
                if edge_new not in edge_object:

                    edge_object[edge_new] = 1 / connectivity

                else:
                    edge_object[edge_new] += 1 / connectivity

        if self.directed:
            outgraph = nx.DiGraph()

        else:
            outgraph = nx.Graph()

        for k, v in edge_object.items():
            outgraph.add_edge(k[0], k[1], weight=v)
        return outgraph

    def remove_layer_edges(self):
        """Remove all edges from separate layer graphs while keeping nodes.

        This method creates empty copies of each layer graph with all nodes intact
        but no edges. Useful for reconstructing networks with different edge sets
        or for temporal network analysis.

        Notes:
            - Requires split_to_layers() to be called first
            - Stores empty layer graphs in self.tmp_layers
            - Original graphs in self.separate_layers remain unchanged
            - All nodes and their attributes are preserved

        Raises:
            RuntimeError: If split_to_layers() hasn't been called yet

        See Also:
            split_to_layers: Must be called before this method
            fill_tmp_with_edges: Add edges back to emptied layers
        """

        if self.separate_layers is not None:
            self.tmp_layers = []
            for graph in self.separate_layers:
                empty_graph = graph.copy()
                empty_graph.remove_edges_from(graph.edges())
                assert len(empty_graph.edges()) == 0
                self.tmp_layers.append(empty_graph)
        else:
            self.monitor("Please,first call your_object.split_to_layers() method!")

        self.monitor("Finished edge cleaning..")

    def edges_from_temporal_table(self, edge_df):
        """Convert a temporal edge DataFrame to edge tuple list.

        Extracts edges from a pandas DataFrame with temporal/activity information
        and converts them to a list of edge tuples suitable for network construction.

        Args:
            edge_df: pandas DataFrame with columns:
                - node_first: Source node identifier
                - node_second: Target node identifier
                - layer_name: Layer identifier

        Returns:
            list: List of edge tuples in format:
                (node_first, node_second, layer_first, layer_second, weight)
                where weight is always 1

        Notes:
            - All values are converted to strings
            - All edges are assigned weight=1
            - Both source and target are assumed to be in the same layer

        Examples:
            >>> import pandas as pd
            >>> net = multi_layer_network()
            >>> df = pd.DataFrame({
            ...     'node_first': ['A', 'B'],
            ...     'node_second': ['B', 'C'],
            ...     'layer_name': ['L1', 'L1']
            ... })
            >>> result = net.edges_from_temporal_table(df)
            >>> len(result) >= 2
            True

        See Also:
            fill_tmp_with_edges: Add these edges to layer graphs
        """

        node_first_names = edge_df.node_first.values
        node_second_names = edge_df.node_second.values
        layer_names = edge_df.layer_name.values
        edges = []
        for enx, _en in enumerate(node_first_names):
            edge = (
                str(node_first_names[enx]),
                str(node_second_names[enx]),
                str(layer_names[enx]),
                str(layer_names[enx]),
                1,
            )
            edges.append(edge)
        return edges

    def fill_tmp_with_edges(self, edge_df):
        """Fill temporary layer graphs with edges from a DataFrame.

        Populates the emptied layer graphs (created by remove_layer_edges) with
        edges from a temporal/activity DataFrame. Useful for temporal network
        analysis where edge sets change over time.

        Args:
            edge_df: pandas DataFrame with columns:
                - node_first: Source node identifier
                - node_second: Target node identifier
                - layer_name: Layer identifier

        Notes:
            - Requires remove_layer_edges() to be called first
            - Edges are grouped by layer
            - Modifies self.tmp_layers in place
            - Each edge is stored as ((node_first, layer), (node_second, layer))

        Raises:
            AttributeError: If self.tmp_layers doesn't exist (call remove_layer_edges first)

        Examples:
            These examples require proper network setup and are for illustration only.

            >>> import pandas as pd  # doctest: +SKIP
            >>> net = multi_layer_network()  # doctest: +SKIP
            >>> net.split_to_layers()  # doctest: +SKIP
            >>> net.remove_layer_edges()  # doctest: +SKIP
            >>> df = pd.DataFrame({  # doctest: +SKIP
            ...     'node_first': ['A', 'B'],
            ...     'node_second': ['B', 'C'],
            ...     'layer_name': ['L1', 'L1']
            ... })
            >>> net.fill_tmp_with_edges(df)  # doctest: +SKIP

        See Also:
            remove_layer_edges: Creates empty layer graphs
            edges_from_temporal_table: Convert DataFrame to edge list
        """

        node_first_names = edge_df.node_first.values
        node_second_names = edge_df.node_second.values
        layer_names = edge_df.layer_name.values
        layer_edges = defaultdict(list)
        for enx, _en in enumerate(node_first_names):
            edge = (
                (str(node_first_names[enx]), str(layer_names[enx])),
                (str(node_second_names[enx]), str(layer_names[enx])),
            )
            layer_edges[layer_names[enx]].append(edge)

        # fill layer by layer
        for enx, layer in enumerate(self.layer_names):
            layer_ed = layer_edges[layer]
            self.tmp_layers[enx].add_edges_from(layer_ed)

    def split_to_layers(
        self,
        style="diagonal",
        compute_layouts="force",
        layout_parameters=None,
        verbose=True,
        multiplex=False,
        convert_to_simple=False,
    ):
        """A method for obtaining layerwise distributions"""

        if self.verbose:
            self.monitor("Network splitting in progress")

        # multilayer visualization
        if style == "diagonal":
            self.layer_names, self.separate_layers, self.multiedges = (
                converters.prepare_for_visualization(
                    self.core_network,
                    compute_layouts=compute_layouts,
                    layout_parameters=layout_parameters,
                    verbose=verbose,
                    multiplex=multiplex,
                )
            )

            try:
                self.real_layer_names = [
                    self.layer_inverse_name_map[lid] for lid in self.layer_names
                ]
            except (KeyError, AttributeError):
                logger.warning(
                    "self.layer_inverse_name_map not defined (name layers), please define them explicitly to have proper names present."
                )
                pass

        # hairball visualization
        if style == "hairball":
            self.layer_names, self.separate_layers, self.multiedges = (
                converters.prepare_for_visualization_hairball(
                    self.core_network, compute_layouts=True
                )
            )

        if style == "none":

            self.layer_names, self.separate_layers, self.multiedges = (
                converters.prepare_for_parsing(self.core_network)
            )

            if convert_to_simple:
                graph_class = nx.DiGraph if self.directed else nx.Graph
                self.separate_layers = [graph_class(x) for x in self.separate_layers]

    def get_layers(
        self,
        style="diagonal",
        compute_layouts="force",
        layout_parameters=None,
        verbose=True,
    ):
        """A method for obtaining layerwise distributions"""

        if self.verbose:
            self.monitor("Network splitting in progress")

        # multilayer visualization
        if style == "diagonal":
            return converters.prepare_for_visualization(
                self.core_network,
                compute_layouts=compute_layouts,
                network_type=self.network_type,
                layout_parameters=layout_parameters,
                verbose=verbose,
            )

        # hairball visualization
        if style == "hairball":
            return converters.prepare_for_visualization_hairball(
                self.core_network, compute_layouts=True
            )

    def _initiate_network(self):
        """Initialize the core network if it doesn't exist."""
        if self.core_network is None:
            self.core_network = self._create_graph()

    def _create_graph(self, multi: bool = True) -> Union[nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph]:
        """Create an appropriate graph type based on network settings.

        Args:
            multi: Whether to create a MultiGraph/MultiDiGraph (default: True)

        Returns:
            NetworkX graph object of the appropriate type
        """
        if self.directed:
            return nx.MultiDiGraph() if multi else nx.DiGraph()
        else:
            return nx.MultiGraph() if multi else nx.Graph()

    def monoplex_nx_wrapper(self, method, kwargs=None):
        """
        A generic networkx function wrapper.

        Args:
            method (str): Name of the NetworkX function to call (e.g., 'degree_centrality', 'betweenness_centrality')
            kwargs (dict, optional): Keyword arguments to pass to the NetworkX function.
                                     For example, for betweenness_centrality you can pass:
                                     - weight: Edge attribute to use as weight
                                     - normalized: Whether to normalize betweenness values
                                     - distance: Edge attribute to use as distance (for closeness_centrality)

        Returns:
            The result of the NetworkX function call.

        Raises:
            AttributeError: If the specified method does not exist in NetworkX.

        Example:
            # Unweighted betweenness centrality
            centralities = network.monoplex_nx_wrapper("betweenness_centrality")

            # Weighted betweenness centrality
            centralities = network.monoplex_nx_wrapper("betweenness_centrality", kwargs={"weight": "weight"})

            # With multiple parameters
            centralities = network.monoplex_nx_wrapper("betweenness_centrality",
                                                       kwargs={"weight": "weight", "normalized": True})
        """

        if kwargs is None:
            kwargs = {}

        # Validate that the method exists in NetworkX
        if not hasattr(nx, method):
            raise AttributeError(f"NetworkX has no method '{method}'")

        # Get the NetworkX function and call it safely
        nx_function = getattr(nx, method)
        result = nx_function(self.core_network, **kwargs)
        return result

    def _generic_edge_dict_manipulator(self, edge_dict_list, target_function, raw: bool = False):
        """
        Generic manipulator of edge dicts
        """

        def _apply(edge_dict):
            # Work with a copy to avoid mutating the original dictionary
            edge_dict = edge_dict.copy()

            if "source_type" in edge_dict.keys() and "target_type" in edge_dict.keys():
                u_for_edge = (edge_dict["source"], edge_dict["source_type"])
                v_for_edge = (edge_dict["target"], edge_dict["target_type"])
            else:
                u_for_edge = (edge_dict["source"], self.dummy_layer)
                v_for_edge = (edge_dict["target"], self.dummy_layer)

            # Remove keys only if they exist
            edge_dict.pop("target", None)
            edge_dict.pop("source", None)
            edge_dict.pop("target_type", None)
            edge_dict.pop("source_type", None)

            func = getattr(self.core_network, target_function)
            key = edge_dict.pop("key", None)

            if raw:
                if key is None:
                    func(u_for_edge, v_for_edge)
                else:
                    func(u_for_edge, v_for_edge, key=key)
            else:
                if key is None:
                    func(u_for_edge, v_for_edge, **edge_dict)
                else:
                    func(u_for_edge, v_for_edge, key=key, **edge_dict)

        if isinstance(edge_dict_list, dict):
            _apply(edge_dict_list)
        else:
            for edge_dict_item in edge_dict_list:
                _apply(edge_dict_item)

    def _generic_edge_list_manipulator(self, edge_list, target_function, raw=False):
        """Generic manipulator of edge lists.

        Args:
            edge_list: List of edges or single edge as [node1, layer1, node2, layer2, weight]
            target_function: Name of the method to call (e.g., 'add_edge', 'remove_edge')
            raw: If True, only pass node tuples; if False, also include weight and type
        """
        func = getattr(self.core_network, target_function)

        if isinstance(edge_list[0], list):
            for edge in edge_list:
                n1, l1, n2, l2, w = edge
                if raw:
                    func((n1, l1), (n2, l2))
                else:
                    func((n1, l1), (n2, l2), weight=w, type="default")
        else:
            n1, l1, n2, l2, w = edge_list
            if raw:
                func((n1, l1), (n2, l2))
            else:
                func((n1, l1), (n2, l2), weight=w, type="default")

    def _generic_node_dict_manipulator(self, node_dict_list, target_function):
        """
        Generic manipulator of node dict
        """

        if isinstance(node_dict_list, dict):
            # Work with a copy to avoid mutating the original dictionary
            node_dict = node_dict_list.copy()

            if "type" in node_dict.keys():
                node_dict["node_for_adding"] = (node_dict["source"], node_dict["type"])
            else:
                node_dict["node_for_adding"] = (node_dict["source"], self.dummy_layer)

            # Remove keys only if they exist
            node_dict.pop("source", None)
            node_dict.pop("type", None)
            nname = node_dict["node_for_adding"]
            node_dict.pop("node_for_adding", None)
            getattr(self.core_network, target_function)(nname, **node_dict)

        else:
            # Handle list of node dictionaries
            for node_dict_item in node_dict_list:
                # Work with a copy to avoid mutating the original dictionary
                node_dict = node_dict_item.copy()

                if "type" in node_dict.keys():
                    node_dict["node_for_adding"] = (
                        node_dict["source"],
                        node_dict["type"],
                    )
                else:
                    node_dict["node_for_adding"] = (
                        node_dict["source"],
                        self.dummy_layer,
                    )

                # Remove keys only if they exist
                node_dict.pop("source", None)
                node_dict.pop("type", None)
                nname = node_dict["node_for_adding"]
                node_dict.pop("node_for_adding", None)
                getattr(self.core_network, target_function)(nname, **node_dict)

    def _generic_node_list_manipulator(self, node_list, target_function):
        """Generic manipulator of node lists.

        Args:
            node_list: List of nodes or single node as [node_id, layer_id]
            target_function: Name of the method to call (e.g., 'add_node', 'remove_node')
        """
        func = getattr(self.core_network, target_function)

        if isinstance(node_list, list):
            for node in node_list:
                n1, l1 = node
                func((n1, l1))
        else:
            n1, l1 = node_list
            func((n1, l1))

    def _unfreeze(self):
        """Unfreeze the network graph for modifications by creating a mutable copy."""
        graph_class = nx.MultiDiGraph if self.directed else nx.MultiGraph
        self.core_network = graph_class(self.core_network)

    # ═════════════════════════════════════════════════════════════════════════
    # Node and Edge Manipulation Methods
    # ═════════════════════════════════════════════════════════════════════════

    def add_edges(
        self,
        edge_dict_list: Union[List[Dict], List[List], Tuple],
        input_type: str = "dict",
    ) -> "multi_layer_network":
        """Add edges to the multilayer network.

        This method supports multiple input formats for specifying edges between nodes
        in different layers. The most common format is dict-based.

        Args:
            edge_dict_list: Edge data in one of the supported formats (see below)
            input_type: Format of edge data ('dict', 'list', or 'px_edge')

        Returns:
            self: Returns self for method chaining

        Supported Formats:
            **Dict format (recommended):**
            ```python
            {
                'source': 'node1',          # Source node ID
                'target': 'node2',          # Target node ID
                'source_type': 'layer1',    # Source layer name
                'target_type': 'layer2',    # Target layer name (can be same as source)
                'weight': 1.0,              # Optional: edge weight
                'type': 'interaction'       # Optional: edge type/label
            }
            ```

            **List format:**
            `[node1, layer1, node2, layer2]`

            **px_edge format:**
            `((node1, layer1), (node2, layer2), {'weight': 1.0})`

        Examples:
            >>> # Add single intra-layer edge
            >>> net = multi_layer_network()
            >>> net.add_edges([{
            ...     'source': 'A',
            ...     'target': 'B',
            ...     'source_type': 'protein',
            ...     'target_type': 'protein'
            ... }])
            <multi_layer_network: type=multilayer, directed=True, nodes=2, edges=1, layers=1>

            >>> # Method chaining
            >>> net = multi_layer_network()
            >>> net.add_edges([
            ...     {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}
            ... ]).add_edges([
            ...     {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'}
            ... ])
            <multi_layer_network: type=multilayer, directed=True, nodes=3, edges=2, layers=1>

            >>> # Add inter-layer edge with weight
            >>> net.add_edges([{
            ...     'source': 'gene1',
            ...     'target': 'protein1',
            ...     'source_type': 'genes',
            ...     'target_type': 'proteins',
            ...     'weight': 0.95,
            ...     'type': 'expression'
            ... }])
            <multi_layer_network: type=multilayer, directed=True, nodes=5, edges=3, layers=3>

            >>> # Add multiple edges at once
            >>> edges = [
            ...     {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
            ...     {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'}
            ... ]
            >>> net.add_edges(edges)
            <multi_layer_network: type=multilayer, directed=True, nodes=5, edges=5, layers=3>

        Raises:
            Exception: If input_type is not one of 'dict', 'list', or 'px_edge'

        Notes:
            - For intra-layer edges, use the same layer for source_type and target_type
            - For inter-layer edges, use different layers
            - Edge weights default to 1.0 if not specified
        """

        self._initiate_network()

        if input_type == "dict":
            self._generic_edge_dict_manipulator(edge_dict_list, "add_edge")

        elif input_type == "list":
            if not edge_dict_list:
                return self
            self._generic_edge_list_manipulator(edge_dict_list, "add_edge")

        elif input_type == "px_edge":

            if edge_dict_list[2] is None:
                attr_dict = None
            else:
                attr_dict = edge_dict_list[2]

            self._unfreeze()
            self.core_network.add_edge(
                edge_dict_list[0], edge_dict_list[1], attr_dict=attr_dict
            )
        else:
            raise ValueError(
                f"Invalid input_type: '{input_type}'. "
                f"Expected 'dict', 'list', or 'px_edge'. "
                f"Example dict format: {{'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}}"
            )

        return self

    def remove_edges(
        self, edge_dict_list: Union[List[Dict], List[List]], input_type: str = "list"
    ) -> None:
        """A method for removing edges..

        Args:
            edge_dict_list: Edge data in dict or list format
            input_type: Format of edge data ('dict' or 'list')

        Raises:
            Exception: If input_type is not valid
        """

        if input_type == "dict":
            self._generic_edge_dict_manipulator(edge_dict_list, "remove_edge", raw=True)
        elif input_type == "list":
            self._generic_edge_list_manipulator(edge_dict_list, "remove_edge", raw=True)
        else:
            raise ValueError(
                f"Invalid input_type: '{input_type}'. "
                f"Expected 'dict' or 'list'. "
                f"Example dict format: {{'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'}}"
            )

    def add_nodes(
        self, node_dict_list: Union[List[Dict], Dict], input_type: str = "dict"
    ) -> "multi_layer_network":
        """Add nodes to the multilayer network.

        Nodes in a multilayer network are identified by both their ID and the layer
        they belong to. This method adds nodes using a dict-based format.

        Args:
            node_dict_list: Node data as a dict or list of dicts (see format below)
            input_type: Format of node data (currently only 'dict' is supported)

        Returns:
            self: Returns self for method chaining

        Dict Format:
            ```python
            {
                'source': 'node_id',    # Node identifier (can be string or number)
                'type': 'layer_name',   # Layer this node belongs to
                'weight': 1.0,          # Optional: node weight/importance
                'label': 'display'      # Optional: display label
                # ... any other node attributes
            }
            ```

        Examples:
            >>> # Add single node
            >>> net = multi_layer_network()
            >>> net.add_nodes([{'source': 'A', 'type': 'layer1'}])
            <multi_layer_network: type=multilayer, directed=True, nodes=1, edges=0, layers=1>

            >>> # Method chaining
            >>> net = multi_layer_network()
            >>> net.add_nodes([{'source': 'A', 'type': 'layer1'}]).add_nodes([{'source': 'B', 'type': 'layer1'}])
            <multi_layer_network: type=multilayer, directed=True, nodes=2, edges=0, layers=1>

            >>> # Add multiple nodes to the same layer
            >>> nodes = [
            ...     {'source': 'A', 'type': 'protein'},
            ...     {'source': 'B', 'type': 'protein'},
            ...     {'source': 'C', 'type': 'protein'}
            ... ]
            >>> net.add_nodes(nodes)
            <multi_layer_network: type=multilayer, directed=True, nodes=5, edges=0, layers=2>

            >>> # Add nodes with attributes
            >>> net.add_nodes([{
            ...     'source': 'gene1',
            ...     'type': 'genes',
            ...     'weight': 0.8,
            ...     'label': 'BRCA1',
            ...     'chromosome': '17'
            ... }])
            <multi_layer_network: type=multilayer, directed=True, nodes=6, edges=0, layers=3>

            >>> # Add nodes to multiple layers
            >>> multi_layer_nodes = [
            ...     {'source': 'entity1', 'type': 'layer1'},
            ...     {'source': 'entity1', 'type': 'layer2'},  # Same entity, different layer
            ...     {'source': 'entity2', 'type': 'layer1'}
            ... ]
            >>> net.add_nodes(multi_layer_nodes)
            <multi_layer_network: type=multilayer, directed=True, nodes=9, edges=0, layers=4>

        Notes:
            - The same node ID can exist in multiple layers
            - Each (node_id, layer) combination is treated as a unique node
            - Additional attributes beyond 'source' and 'type' are preserved
            - Nodes must be added before edges referencing them
        """

        self._initiate_network()

        if input_type == "dict":
            self._generic_node_dict_manipulator(node_dict_list, "add_node")

        return self

    def remove_nodes(self, node_dict_list, input_type="dict"):
        """
        Remove nodes from the network
        """

        if input_type == "dict":
            self._generic_node_dict_manipulator(node_dict_list, "remove_node")

        if input_type == "list":
            self._generic_node_list_manipulator(node_dict_list, "remove_node")

    def _get_num_layers(self):
        """
        Count layers
        """

        self.number_of_layers = len({x[1] for x in self.get_nodes()})

    def _get_num_nodes(self):
        """
        Count nodes
        """

        self.number_of_unique_nodes = len({x[0] for x in self.get_nodes()})

    def _node_layer_mappings(self):

        pass

    def get_tensor(self, sparsity_type="bsr"):
        """Get sparse tensor representation of the multilayer network.

        Returns the supra-adjacency matrix in the specified sparse format.
        This method provides a tensor-like view of the multilayer network,
        useful for mathematical analysis and matrix-based algorithms.

        Args:
            sparsity_type: Sparse matrix format to use. Options include:
                - 'bsr' (default): Block Sparse Row format
                - 'csr': Compressed Sparse Row format
                - 'csc': Compressed Sparse Column format
                - 'coo': Coordinate format
                - 'lil': List of Lists format
                - 'dok': Dictionary of Keys format

        Returns:
            scipy.sparse matrix: Supra-adjacency matrix in specified format

        Example:
            >>> net = multi_layer_network()
            >>> _ = net.add_edges([['A', 'L0', 'B', 'L0', 1]], input_type='list')
            >>> tensor = net.get_tensor(sparsity_type='csr')
            >>> tensor.shape
            (2, 2)

        Note:
            The returned matrix is the same as get_supra_adjacency_matrix(mtype='sparse')
            but with control over the specific sparse format used.
        """
        if self.numeric_core_network is None:
            self._encode_to_numeric()

        # Get the sparse matrix
        sparse_matrix = self.numeric_core_network

        # Convert to requested format if needed
        if sparsity_type != 'bsr':
            method_name = SPARSE_FORMAT_METHODS.get(sparsity_type)
            if method_name:
                try:
                    convert_method = getattr(sparse_matrix, method_name, None)
                    if convert_method:
                        return convert_method()
                    else:
                        import warnings
                        warnings.warn(
                            f"Sparse format '{sparsity_type}' conversion method '{method_name}' not available. "
                            f"Returning matrix in {type(sparse_matrix).__name__} format.",
                            UserWarning,
                            stacklevel=2
                        )
                        return sparse_matrix
                except Exception as e:
                    import warnings
                    warnings.warn(
                        f"Failed to convert to '{sparsity_type}' format: {e}. "
                        f"Returning matrix in {type(sparse_matrix).__name__} format.",
                        UserWarning,
                        stacklevel=2
                    )
                    return sparse_matrix
            else:
                import warnings
                warnings.warn(
                    f"Unknown sparse format '{sparsity_type}'. "
                    f"Supported formats: {', '.join(SPARSE_FORMAT_METHODS.keys())}. "
                    f"Returning matrix in {type(sparse_matrix).__name__} format.",
                    UserWarning,
                    stacklevel=2
                )
                return sparse_matrix

        return sparse_matrix

    def _encode_to_numeric(self):
        """Encode network to numeric format for matrix operations.

        Converts the network structure to numeric matrices. For multilayer networks,
        creates a simple numeric graph. For multiplex networks, creates a supra-adjacency
        matrix with identity matrices coupling layers.
        """
        if self.network_type != "multiplex":
            self.numeric_core_network, self.node_order_in_matrix = _encode_multilayer_network(
                self.core_network, self.directed
            )
        else:
            self.numeric_core_network, self.node_order_in_matrix = _encode_multiplex_network(
                self.core_network
            )

    def get_supra_adjacency_matrix(self, mtype="sparse"):
        """
        Get sparse representation of the supra matrix.

        Args:
            mtype: 'sparse' or 'dense' - matrix representation type

        Returns:
            Supra-adjacency matrix in requested format

        Warning:
            For large multilayer networks, dense matrices can consume
            significant memory (N*L)^2 * 8 bytes for float64.
        """

        if self.numeric_core_network is None:
            self._encode_to_numeric()

        # Calculate and warn about memory usage for dense matrices
        if mtype == "dense":
            nodes_list = list(self.get_nodes())
            num_nodes = len(nodes_list)
            num_layers = len({x[1] for x in nodes_list})
            supra_size = num_nodes * num_layers

            # Estimate memory for dense matrix (8 bytes per float64)
            estimated_bytes = supra_size * supra_size * 8
            estimated_gb = estimated_bytes / (1024**3)

            if estimated_gb > 10:
                import warnings

                warnings.warn(
                    f"Dense supra-adjacency matrix will be approximately {estimated_gb:.1f} GB "
                    f"({num_nodes} nodes × {num_layers} layers = {supra_size} × {supra_size} matrix). "
                    "This may cause memory issues. Consider using mtype='sparse' instead, "
                    "or analyzing layers independently.",
                    ResourceWarning,
                    stacklevel=2,
                )
            elif estimated_gb > 1:
                import warnings

                warnings.warn(
                    f"Dense supra-adjacency matrix will be approximately {estimated_gb:.1f} GB. "
                    "Consider using mtype='sparse' for better memory efficiency.",
                    ResourceWarning,
                    stacklevel=2,
                )

        #        print(self.numeric_core_network)
        if mtype == "sparse":
            return self.numeric_core_network
        else:
            try:
                return self.numeric_core_network.todense()
            except AttributeError:
                return self.numeric_core_network

    def visualize_matrix(self, kwargs=None):
        """
        Plot the matrix -- this plots the supra-adjacency matrix
        """

        if kwargs is None:
            kwargs = {}
        if server_mode:
            return 0

        adjmat = self.get_supra_adjacency_matrix(mtype="dense")
        supra_adjacency_matrix_plot(adjmat, **kwargs)

    # ═════════════════════════════════════════════════════════════════════════
    # Visualization Methods
    # ═════════════════════════════════════════════════════════════════════════

    def visualize_network(
        self,
        style="diagonal",
        parameters_layers=None,
        parameters_multiedges=None,
        show=False,
        compute_layouts="force",
        layouts_parameters=None,
        verbose=True,
        orientation="upper",
        resolution=0.01,
        axis=None,
        fig=None,
        no_labels=False,
        linewidth=1.7,
        alphachannel=0.3,
        linepoints="-.",
        legend=False,
    ):
        """Visualize the multilayer network.

        Supports multiple visualization styles:
        - 'diagonal': Layer-centric diagonal layout with inter-layer edges
        - 'hairball': Aggregate hairball plot of all layers
        - 'flow' or 'alluvial': Layered flow visualization with horizontal bands
        - 'sankey': Sankey diagram showing inter-layer flow strength

        Args:
            style: Visualization style ('diagonal', 'hairball', 'flow', 'alluvial', or 'sankey')
            parameters_layers: Custom parameters for layer drawing
            parameters_multiedges: Custom parameters for edge drawing
            show: Show plot immediately
            compute_layouts: Layout algorithm (currently unused)
            layouts_parameters: Layout parameters (currently unused)
            verbose: Enable verbose output
            orientation: Edge orientation for diagonal style
            resolution: Resolution for edge curves
            axis: Optional matplotlib axis to draw on
            fig: Optional matplotlib figure (currently unused)
            no_labels: Hide network labels
            linewidth: Width of edge lines
            alphachannel: Alpha channel for edge transparency
            linepoints: Line style for edges
            legend: Show legend (for hairball style)

        Returns:
            Matplotlib axis object

        Raises:
            Exception: If style is not recognized

        Performance Notes:
            For large networks (>500 nodes), visualization performance may degrade:
            - Layout computation can be slow (O(n²) for force-directed layouts)
            - Rendering many edges is memory and CPU intensive
            - Consider filtering or sampling for exploratory visualization
            - Use simpler layouts or increase layout iteration limits

            Approximate rendering times on typical hardware:
            - 100 nodes: <1 second
            - 500 nodes: 5-10 seconds
            - 1000 nodes: 30-60 seconds
            - 5000+ nodes: Several minutes, may run out of memory
        """
        if server_mode:
            return 0

        # Performance warning for large networks
        if self.core_network is not None:
            num_nodes = self.core_network.number_of_nodes()
            if num_nodes > 500:
                logger.warning(
                    f"Visualizing large network with {num_nodes} nodes. "
                    "This may take significant time and memory. "
                    "Consider using network sampling or filtering for exploratory analysis."
                )

        if style == "diagonal":
            return _visualize_diagonal_style(
                self,
                parameters_layers,
                parameters_multiedges,
                axis,
                verbose,
                no_labels,
                alphachannel,
                linepoints,
                orientation,
                linewidth,
                resolution,
                show,
            )
        elif style == "hairball":
            return _visualize_hairball_style(self, axis, legend, show)
        elif style in ("flow", "alluvial"):
            # Import here to avoid circular dependency
            from py3plex.visualization.multilayer import draw_multilayer_flow

            # Get layers data
            labels_list, graphs, multilinks = self.get_layers("diagonal")

            # Extract relevant kwargs for draw_multilayer_flow
            flow_kwargs = {}
            if 'node_activity' in locals():
                flow_kwargs['node_activity'] = locals()['node_activity']
            if 'layer_gap' in locals():
                flow_kwargs['layer_gap'] = locals()['layer_gap']
            if 'node_size' in locals():
                flow_kwargs['node_size'] = locals()['node_size']
            if 'node_cmap' in locals():
                flow_kwargs['node_cmap'] = locals()['node_cmap']
            if 'flow_alpha' in locals():
                flow_kwargs['flow_alpha'] = locals()['flow_alpha']

            return draw_multilayer_flow(
                graphs,
                multilinks,
                labels=labels_list if not no_labels else None,
                ax=axis,
                display=show,
                **flow_kwargs
            )
        elif style == "sankey":
            # Import here to avoid circular dependency
            from py3plex.visualization.sankey import draw_multilayer_sankey

            # Get layers data (using "diagonal" layout type to extract layer structure)
            labels_list, graphs, multilinks = self.get_layers("diagonal")

            return draw_multilayer_sankey(
                graphs,
                multilinks,
                labels=labels_list if not no_labels else None,
                ax=axis,
                display=show
            )
        else:
            raise ValueError(
                f"Invalid visualization style: '{style}'. "
                f"Expected 'diagonal', 'hairball', 'flow', 'alluvial', or 'sankey'. "
                f"Example: net.visualize_network(style='diagonal')"
            )

    def get_nx_object(self):
        """Return only core network with proper annotations"""
        return self.core_network

    def test_scale_free(self):
        """
        Test the scale-free-nness of the network
        """

        val_vect = sorted(dict(nx.degree(self.core_network)).values(), reverse=True)
        alpha, sigma = topology.basic_pl_stats(val_vect)
        return (alpha, sigma)

    def get_label_matrix(self):
        """Return network labels"""
        return self.labels

    def _assign_types_for_hinmine(self):
        """
        Assing some basic types...
        """
        for node in self.get_nodes(data=True):
            node[1]["type"] = node[0][1]

    def get_decomposition_cycles(self, cycle=None):
        """A supporting method for obtaining decomposition triplets"""
        self._assign_types_for_hinmine()
        if self.hinmine_network is None:
            self.hinmine_network = load_hinmine_object(
                self.core_network, self.label_delimiter
            )
        return hinmine_get_cycles(self.hinmine_network)

    def get_decomposition(
        self, heuristic="all", cycle=None, parallel=False, alpha=1, beta=0
    ):
        """Core method for obtaining a network's decomposition in terms of relations"""

        if heuristic == "all":
            heuristic = [
                "idf",
                "tf",
                "chi",
                "ig",
                "gr",
                "delta",
                "rf",
                "okapi",
            ]  # all available
        if self.hinmine_network is None:
            if self.verbose:
                logger.info("Loading into a hinmine object..")
            self.hinmine_network = load_hinmine_object(
                self.core_network, self.label_delimiter
            )

        induced_net = 1
        if beta > 0:
            subset_nodes = []
            for n in self.core_network.nodes(data=True):
                if "labels" in n[1]:
                    subset_nodes.append(n[0])
            induced_net = self.core_network.subgraph(subset_nodes)
            for e in induced_net.edges(data=True):
                e[2]["weight"] = float(e[2]["weight"])
            induced_net = nx_to_scipy_sparse_matrix(induced_net)

        for x in heuristic:
            try:

                dout = hinmine_decompose(
                    self.hinmine_network, heuristic=x, cycle=cycle, parallel=parallel
                )
                decomposition = dout.decomposed["decomposition"]

                # use alpha and beta levels
                final_decomposition = alpha * decomposition + beta * induced_net

                #                print("Successfully decomposed: {}".format(x))

                yield (final_decomposition, dout.label_matrix, x)

            except Exception as es:
                logger.error("No decomposition found for: %s", x)
                logger.error(str(es))

    def load_embedding(self, embedding_file):
        """Embedding loading method"""

        self.embedding = parsers.parse_embedding(embedding_file)
        return self

    def get_degrees(self):
        """
        A simple wrapper which computes node degrees.
        """

        return dict(nx.degree(self.core_network))

    def serialize_to_edgelist(
        self,
        edgelist_file="./tmp/tmpedgelist.txt",
        tmp_folder="tmp",
        out_folder="out",
        multiplex=False,
    ):
        """Serialize the multilayer network to an edgelist file.

        Converts the network to a numeric edgelist format suitable for external tools
        and algorithms that require integer node/layer identifiers.

        Args:
            edgelist_file: Path to output edgelist file (default: "./tmp/tmpedgelist.txt")
            tmp_folder: Temporary folder for intermediate files (default: "tmp")
            out_folder: Output folder for results (default: "out")
            multiplex: If True, use multiplex format (node layer node layer weight)
                      If False, use simple edgelist format (node1 node2 weight)

        Returns:
            dict: Inverse node mapping (numeric_id -> original_node_tuple)
                 Use this to decode results from external algorithms

        File Formats:
            - Multiplex format: node1_id layer1_id node2_id layer2_id weight
            - Simple format: node1_id node2_id weight

        Notes:
            - Creates tmp_folder and out_folder if they don't exist
            - Nodes are mapped to sequential integers starting from 0
            - Layers are mapped to sequential integers starting from 0 (multiplex mode)
            - All edges have weight 1 unless explicitly specified

        Examples:
            Example requires file output - for illustration only.
            
            >>> net = multi_layer_network()  # doctest: +SKIP
            >>> # ... build network ...
            >>> node_mapping = net.serialize_to_edgelist(  # doctest: +SKIP
            ...     edgelist_file='network.txt',
            ...     multiplex=True
            ... )
            >>> # Use node_mapping to decode results
            >>> original_node = node_mapping[0]  # Get original node for id 0  # doctest: +SKIP

        See Also:
            load_network: Load networks from file
            save_network: Alternative serialization method
        """

        import os

        node_dict = {e: k for k, e in enumerate(list(self.get_nodes()))}
        outstruct = []

        # enumerated n l n l
        if multiplex:
            separate_layers = []

            for node in self.get_nodes():
                separate_layers.append(node[1])

            layer_mappings = {e: k for k, e in enumerate(set(separate_layers))}
            node_mappings = {k[0]: v for k, v in node_dict.items()}

            # add encoded edges
            for edge in self.get_edges():
                node_zero = node_mappings[edge[0][0]]
                node_first = node_mappings[edge[1][0]]
                layer_zero = layer_mappings[edge[0][1]]
                layer_first = layer_mappings[edge[1][1]]
                el = [node_zero, layer_zero, node_first, layer_first, 1]
                outstruct.append(el)
        else:
            # serialize as a simple edgelist
            for edge in self.get_edges(data=True):
                node_zero = node_dict[edge[0]]
                node_first = node_dict[edge[1]]
                if "weight" in edge[2]:
                    weight = edge[2]["weight"]
                else:
                    weight = 1
                el = [node_zero, node_first, weight]
                outstruct.append(el)

        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)

        if not os.path.exists(out_folder):
            os.makedirs(out_folder)

        with open(edgelist_file, "w") as file:
            for el in outstruct:
                file.write(" ".join([str(x) for x in el]) + "\n")

        inverse_nodes = {a: b for b, a in node_dict.items()}
        #        inverse_layers = {a:b for b,a in layer_mappings.items()}

        return inverse_nodes

    def to_homogeneous_hypergraph(self):
        """
        Transform a multiplex network into a homogeneous graph using incidence gadget encoding.

        This method encodes the multiplex structure where each layer is represented by
        a unique prime number signature. Each edge becomes an edge-node connected to
        its endpoints and a cycle of length prime-1 that encodes the layer.

        Returns
        -------
        tuple (H, node_mapping, edge_info)
            H : networkx.Graph
                Homogeneous unlabeled graph encoding the multiplex structure.
            node_mapping : dict
                Maps each original node to its vertex-node in H.
            edge_info : dict
                Mapping from each edge-node in H to its (layer, endpoints) tuple.

        Examples:
            Example requires sympy dependency - for illustration only.
            
        >>> network = multi_layer_network(directed=False)  # doctest: +SKIP
        >>> network.add_nodes([{'source': '1', 'type': 'A'}, {'source': '2', 'type': 'A'}], input_type='dict')  # doctest: +SKIP
        >>> network.add_edges([{'source': '1', 'target': '2', 'source_type': 'A', 'target_type': 'A'}], input_type='dict')  # doctest: +SKIP
        >>> H, node_map, edge_info = network.to_homogeneous_hypergraph()  # doctest: +SKIP
        >>> print(f"Homogeneous graph has {len(H.nodes())} nodes")  # doctest: +SKIP

        Notes
        -----
        This transformation uses prime-based signatures to encode layers:
        - Each layer is assigned a unique prime number (2, 3, 5, 7, ...)
        - Each edge in layer with prime p is connected to a cycle of length p
        - The cycle structure uniquely identifies the layer
        """
        from itertools import count

        from sympy import primerange

        H = nx.Graph()
        node_mapping = {}
        edge_info = {}

        # Handle empty network
        if self.core_network is None:
            return H, node_mapping, edge_info

        # Build multiplex dict from current network structure
        # Nodes in py3plex are stored as tuples: (node_id, layer_id)
        multiplex = {}

        for u, v in self.core_network.edges():
            # u and v are tuples like ('1', 'A')
            u_node, u_layer = u
            v_node, v_layer = v

            # Only include intra-layer edges (same layer)
            if u_layer == v_layer:
                if u_layer not in multiplex:
                    multiplex[u_layer] = []
                multiplex[u_layer].append((u_node, v_node))

        # Step 1: create vertex-nodes
        all_nodes = set()
        for edges in multiplex.values():
            for e in edges:
                for n in e:
                    all_nodes.add(n)

        for node in all_nodes:
            node_mapping[node] = f"v_{node}"
            H.add_node(f"v_{node}")

        # Step 2: assign prime-based signatures to layers
        primes = list(primerange(2, 2000))
        layer_to_prime = {
            layer: primes[i] for i, layer in enumerate(sorted(multiplex.keys()))
        }

        eid = count()

        for layer, edges in multiplex.items():
            p = layer_to_prime[layer]
            for u, v in edges:
                y = f"e_{next(eid)}"
                H.add_node(y)

                # connect to endpoints
                H.add_edges_from([(node_mapping[u], y), (node_mapping[v], y)])

                # attach the signature cycle C_p
                cycle_nodes = [f"{y}_s{i}" for i in range(p - 1)]
                H.add_nodes_from(cycle_nodes)
                sig_edges = [(y, cycle_nodes[0])]
                sig_edges += [
                    (cycle_nodes[i], cycle_nodes[i + 1]) for i in range(p - 2)
                ]
                sig_edges.append((cycle_nodes[-1], y))
                H.add_edges_from(sig_edges)

                edge_info[y] = (layer, (u, v))

        return H, node_mapping, edge_info

    # ═════════════════════════════════════════════════════════════════════════
    # Ricci Curvature and Ricci Flow Methods
    # ═════════════════════════════════════════════════════════════════════════

    def _build_supra_graph(self, weight_attr: str = "weight", interlayer_weight: float = 1.0):
        """Build a supra-graph representation of the multilayer network.

        The supra-graph includes both intra-layer edges (from each layer) and
        inter-layer edges (connecting corresponding nodes across layers).

        Args:
            weight_attr: Name of the edge attribute containing weights.
            interlayer_weight: Weight for inter-layer coupling edges.

        Returns:
            NetworkX graph: Supra-graph with nodes labeled as (node_id, layer_id).
        """
        if self.core_network is None:
            raise ValueError("Core network is not initialized. Cannot build supra-graph.")

        # Create a new graph of the same type (directed/undirected)
        if self.directed:
            G_supra = nx.DiGraph()
        else:
            G_supra = nx.Graph()

        # Add all nodes and intra-layer edges from core_network
        G_supra.add_nodes_from(self.core_network.nodes())

        # Add intra-layer edges with their weights
        for u, v, key, data in self.core_network.edges(keys=True, data=True):
            # For intra-layer edges, u and v should have the same layer
            if isinstance(u, tuple) and isinstance(v, tuple) and len(u) >= 2 and len(v) >= 2:
                if u[1] == v[1]:  # Same layer
                    weight = data.get(weight_attr, 1.0)
                    if G_supra.has_edge(u, v):
                        # If edge exists, keep the minimum weight (or sum, depending on semantics)
                        G_supra[u][v][weight_attr] = min(G_supra[u][v].get(weight_attr, weight), weight)
                    else:
                        G_supra.add_edge(u, v, **{weight_attr: weight})

        # Add inter-layer coupling edges
        # Group nodes by node_id
        node_layers = defaultdict(list)
        for node in G_supra.nodes():
            if isinstance(node, tuple) and len(node) >= 2:
                node_id, layer = node[0], node[1]
                node_layers[node_id].append(layer)

        # Add inter-layer edges between same nodes in different layers
        for node_id, layers in node_layers.items():
            if len(layers) > 1:
                # Add edges between all pairs of layers for this node
                for i, layer1 in enumerate(layers):
                    for layer2 in layers[i+1:]:
                        node1 = (node_id, layer1)
                        node2 = (node_id, layer2)
                        G_supra.add_edge(node1, node2, **{weight_attr: interlayer_weight})

        return G_supra

    def compute_ollivier_ricci(
        self,
        mode: str = "core",
        layers: Optional[List[Any]] = None,
        alpha: float = 0.5,
        weight_attr: str = "weight",
        curvature_attr: str = "ricciCurvature",
        verbose: str = "ERROR",
        backend_kwargs: Optional[Dict[str, Any]] = None,
        inplace: bool = True,
        interlayer_weight: float = 1.0,
    ) -> Dict[str, Any]:
        """Compute Ollivier-Ricci curvature on the multilayer network.

        This method provides flexible computation of Ollivier-Ricci curvature
        at different levels of the multilayer network:

        - **core mode**: Compute curvature on the aggregated (flattened) network
        - **layers mode**: Compute curvature separately for each layer
        - **supra mode**: Compute curvature on the full supra-graph including
          both intra-layer and inter-layer edges

        Args:
            mode: Scope of computation. Options: "core", "layers", "supra".
            layers: List of layer identifiers to process (only for mode="layers").
                If None, all layers are processed.
            alpha: Ollivier-Ricci parameter in [0, 1] controlling the mass
                distribution. Default: 0.5.
            weight_attr: Name of edge attribute containing weights. Default: "weight".
            curvature_attr: Name of edge attribute to store curvature values.
                Default: "ricciCurvature".
            verbose: Verbosity level. Options: "INFO", "DEBUG", "ERROR". Default: "ERROR".
            backend_kwargs: Additional keyword arguments for OllivierRicci constructor.
            inplace: If True, update internal graphs. If False, return new graphs
                without modifying the network. Default: True.
            interlayer_weight: Weight for inter-layer coupling edges (only for
                mode="supra"). Default: 1.0.

        Returns:
            Dictionary mapping scope identifiers to NetworkX graphs with computed
            curvatures:
            - mode="core": {"core": graph_with_curvature}
            - mode="layers": {layer_id: graph_with_curvature, ...}
            - mode="supra": {"supra": supra_graph_with_curvature}

        Raises:
            RicciBackendNotAvailable: If GraphRicciCurvature is not installed.
            ValueError: If mode is invalid or layers contains invalid identifiers.

        Examples:
            >>> from py3plex.core import multinet
            >>> net = multinet.multi_layer_network()
            >>> _ = net.add_edges([
            ...     ['A', 'layer1', 'B', 'layer1', 1],
            ...     ['B', 'layer1', 'C', 'layer1', 1],
            ... ], input_type="list")
            >>>
            >>> # Compute on aggregated network
            >>> result = net.compute_ollivier_ricci(mode="core")  # doctest: +SKIP
            >>>
            >>> # Compute per layer
            >>> result = net.compute_ollivier_ricci(mode="layers")  # doctest: +SKIP
            >>>
            >>> # Compute on supra-graph
            >>> result = net.compute_ollivier_ricci(mode="supra", inplace=False)  # doctest: +SKIP
        """
        if not RICCI_AVAILABLE:
            raise RicciBackendNotAvailable()

        if mode not in ["core", "layers", "supra"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'core', 'layers', or 'supra'.")

        if self.core_network is None:
            raise ValueError("Core network is not initialized.")

        result = {}

        if mode == "core":
            # Compute on aggregated core network
            G_curved = compute_ollivier_ricci_single_graph(
                self.core_network,
                alpha=alpha,
                weight_attr=weight_attr,
                curvature_attr=curvature_attr,
                verbose=verbose,
                backend_kwargs=backend_kwargs,
            )
            if inplace:
                self.core_network = G_curved
            result["core"] = G_curved

        elif mode == "layers":
            # Get all unique layers
            all_layers = set([n[1] for n in self.core_network.nodes()
                            if isinstance(n, tuple) and len(n) >= 2])

            # Determine which layers to process
            if layers is None:
                layers_to_process = all_layers
            else:
                layers_to_process = set(layers)
                # Validate layer identifiers
                invalid_layers = layers_to_process - all_layers
                if invalid_layers:
                    raise ValueError(f"Invalid layer identifiers: {invalid_layers}")

            # Process each layer
            for layer in layers_to_process:
                # Get subnetwork for this layer
                subnet = self.subnetwork([layer], subset_by='layers')

                # Compute curvature
                G_curved = compute_ollivier_ricci_single_graph(
                    subnet.core_network,
                    alpha=alpha,
                    weight_attr=weight_attr,
                    curvature_attr=curvature_attr,
                    verbose=verbose,
                    backend_kwargs=backend_kwargs,
                )

                if inplace:
                    # Update edges in the main core_network
                    for u, v, data in G_curved.edges(data=True):
                        if curvature_attr in data:
                            # Update curvature in the core network
                            if self.core_network.has_edge(u, v):
                                for key in self.core_network[u][v]:
                                    self.core_network[u][v][key][curvature_attr] = data[curvature_attr]

                result[layer] = G_curved

        elif mode == "supra":
            # Build supra-graph
            G_supra = self._build_supra_graph(
                weight_attr=weight_attr,
                interlayer_weight=interlayer_weight
            )

            # Compute curvature on supra-graph
            G_supra_curved = compute_ollivier_ricci_single_graph(
                G_supra,
                alpha=alpha,
                weight_attr=weight_attr,
                curvature_attr=curvature_attr,
                verbose=verbose,
                backend_kwargs=backend_kwargs,
            )

            # Note: For supra mode, we don't update core_network even if inplace=True,
            # as the supra-graph is a different representation
            result["supra"] = G_supra_curved

        return result

    def compute_ollivier_ricci_flow(
        self,
        mode: str = "core",
        layers: Optional[List[Any]] = None,
        alpha: float = 0.5,
        iterations: int = 10,
        method: str = "OTD",
        weight_attr: str = "weight",
        curvature_attr: str = "ricciCurvature",
        verbose: str = "ERROR",
        backend_kwargs: Optional[Dict[str, Any]] = None,
        inplace: bool = True,
        interlayer_weight: float = 1.0,
    ) -> Dict[str, Any]:
        """Compute Ollivier-Ricci flow on the multilayer network.

        Ricci flow iteratively adjusts edge weights based on their Ricci curvature,
        effectively revealing and enhancing community structure. After Ricci flow,
        edges with negative curvature (community boundaries) have reduced weights,
        while edges with positive curvature have increased weights.

        Args:
            mode: Scope of computation. Options: "core", "layers", "supra".
            layers: List of layer identifiers to process (only for mode="layers").
                If None, all layers are processed.
            alpha: Ollivier-Ricci parameter in [0, 1]. Default: 0.5.
            iterations: Number of Ricci flow iterations. Default: 10.
            method: Ricci flow method. Options: "OTD" (Optimal Transport Distance,
                recommended), "ATD" (Average Transport Distance). Default: "OTD".
            weight_attr: Name of edge attribute containing weights. After Ricci flow,
                these weights are updated to reflect the flow metric.
            curvature_attr: Name of edge attribute for curvature values.
                Default: "ricciCurvature".
            verbose: Verbosity level. Options: "INFO", "DEBUG", "ERROR". Default: "ERROR".
            backend_kwargs: Additional keyword arguments for OllivierRicci constructor.
            inplace: If True, update internal graphs. If False, return new graphs.
                Default: True.
            interlayer_weight: Weight for inter-layer coupling edges (only for
                mode="supra"). Default: 1.0.

        Returns:
            Dictionary mapping scope identifiers to NetworkX graphs with Ricci flow
            applied:
            - mode="core": {"core": graph_with_flow}
            - mode="layers": {layer_id: graph_with_flow, ...}
            - mode="supra": {"supra": supra_graph_with_flow}

        Raises:
            RicciBackendNotAvailable: If GraphRicciCurvature is not installed.
            ValueError: If mode is invalid or layers contains invalid identifiers.

        Examples:
            >>> from py3plex.core import multinet
            >>> net = multinet.multi_layer_network()
            >>> _ = net.add_edges([
            ...     ['A', 'layer1', 'B', 'layer1', 1],
            ...     ['B', 'layer1', 'C', 'layer1', 1],
            ... ], input_type="list")
            >>>
            >>> # Apply Ricci flow to aggregated network
            >>> result = net.compute_ollivier_ricci_flow(mode="core", iterations=20)  # doctest: +SKIP
            >>>
            >>> # Apply to each layer
            >>> result = net.compute_ollivier_ricci_flow(mode="layers", iterations=10)  # doctest: +SKIP
        """
        if not RICCI_AVAILABLE:
            raise RicciBackendNotAvailable()

        if mode not in ["core", "layers", "supra"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'core', 'layers', or 'supra'.")

        if self.core_network is None:
            raise ValueError("Core network is not initialized.")

        result = {}

        if mode == "core":
            # Compute Ricci flow on aggregated core network
            G_flow = compute_ollivier_ricci_flow_single_graph(
                self.core_network,
                alpha=alpha,
                iterations=iterations,
                method=method,
                weight_attr=weight_attr,
                curvature_attr=curvature_attr,
                verbose=verbose,
                backend_kwargs=backend_kwargs,
            )
            if inplace:
                self.core_network = G_flow
            result["core"] = G_flow

        elif mode == "layers":
            # Get all unique layers
            all_layers = set([n[1] for n in self.core_network.nodes()
                            if isinstance(n, tuple) and len(n) >= 2])

            # Determine which layers to process
            if layers is None:
                layers_to_process = all_layers
            else:
                layers_to_process = set(layers)
                # Validate layer identifiers
                invalid_layers = layers_to_process - all_layers
                if invalid_layers:
                    raise ValueError(f"Invalid layer identifiers: {invalid_layers}")

            # Process each layer
            for layer in layers_to_process:
                # Get subnetwork for this layer
                subnet = self.subnetwork([layer], subset_by='layers')

                # Compute Ricci flow
                G_flow = compute_ollivier_ricci_flow_single_graph(
                    subnet.core_network,
                    alpha=alpha,
                    iterations=iterations,
                    method=method,
                    weight_attr=weight_attr,
                    curvature_attr=curvature_attr,
                    verbose=verbose,
                    backend_kwargs=backend_kwargs,
                )

                if inplace:
                    # Update edges in the main core_network
                    for u, v, data in G_flow.edges(data=True):
                        # Update both weight and curvature in the core network
                        if self.core_network.has_edge(u, v):
                            for key in self.core_network[u][v]:
                                if weight_attr in data:
                                    self.core_network[u][v][key][weight_attr] = data[weight_attr]
                                if curvature_attr in data:
                                    self.core_network[u][v][key][curvature_attr] = data[curvature_attr]

                result[layer] = G_flow

        elif mode == "supra":
            # Build supra-graph
            G_supra = self._build_supra_graph(
                weight_attr=weight_attr,
                interlayer_weight=interlayer_weight
            )

            # Compute Ricci flow on supra-graph
            G_supra_flow = compute_ollivier_ricci_flow_single_graph(
                G_supra,
                alpha=alpha,
                iterations=iterations,
                method=method,
                weight_attr=weight_attr,
                curvature_attr=curvature_attr,
                verbose=verbose,
                backend_kwargs=backend_kwargs,
            )

            result["supra"] = G_supra_flow

        return result

    def visualize_ricci_core(
        self,
        alpha: float = 0.5,
        iterations: int = 10,
        layout_type: str = "mds",
        dim: int = 2,
        **kwargs
    ):
        """
        Visualize the aggregated core network using Ricci-flow-based layout.

        This method is a high-level wrapper for Ricci-flow-based visualization
        of the core (aggregated) network. It automatically computes Ricci flow
        if not already done and creates an informative layout that emphasizes
        geometric structure and communities.

        Args:
            alpha: Ollivier-Ricci parameter for flow computation. Default: 0.5.
            iterations: Number of Ricci flow iterations. Default: 10.
            layout_type: Layout algorithm ("mds", "spring", "spectral"). Default: "mds".
            dim: Dimensionality of layout (2 or 3). Default: 2.
            **kwargs: Additional arguments passed to visualize_multilayer_ricci_core.

        Returns:
            Tuple of (figure, axes, positions_dict).

        Raises:
            RicciBackendNotAvailable: If GraphRicciCurvature is not installed.

        Examples:
            Example requires GraphRicciCurvature library - for illustration only.
            
            >>> from py3plex.core import multinet  # doctest: +SKIP
            >>> net = multinet.multi_layer_network()  # doctest: +SKIP
            >>> net.add_edges([  # doctest: +SKIP
            ...     ['A', 'layer1', 'B', 'layer1', 1],
            ...     ['B', 'layer1', 'C', 'layer1', 1],
            ... ], input_type="list")
            >>> fig, ax, pos = net.visualize_ricci_core()  # doctest: +SKIP
            >>> import matplotlib.pyplot as plt  # doctest: +SKIP
            >>> plt.show()  # doctest: +SKIP

        See Also:
            visualize_ricci_layers: Per-layer visualization with Ricci flow
            visualize_ricci_supra: Supra-graph visualization with Ricci flow
        """
        from py3plex.visualization.ricci_multilayer_vis import (
            visualize_multilayer_ricci_core,
        )

        return visualize_multilayer_ricci_core(
            self,
            alpha=alpha,
            iterations=iterations,
            layout_type=layout_type,
            dim=dim,
            **kwargs
        )

    def visualize_ricci_layers(
        self,
        layers: Optional[List[Any]] = None,
        alpha: float = 0.5,
        iterations: int = 10,
        layout_type: str = "mds",
        share_layout: bool = True,
        **kwargs
    ):
        """
        Visualize individual layers using Ricci-flow-based layouts.

        This method creates visualizations of individual layers with layouts
        derived from Ricci flow. Layers can share a common coordinate system
        (for easier comparison) or have independent layouts.

        Args:
            layers: List of layer identifiers to visualize. If None, uses all layers.
            alpha: Ollivier-Ricci parameter. Default: 0.5.
            iterations: Number of Ricci flow iterations. Default: 10.
            layout_type: Layout algorithm. Default: "mds".
            share_layout: If True, use shared coordinates across layers. Default: True.
            **kwargs: Additional arguments passed to visualize_multilayer_ricci_layers.

        Returns:
            Tuple of (figure, layer_positions_dict).

        Raises:
            RicciBackendNotAvailable: If GraphRicciCurvature is not installed.

        Examples:
            >>> fig, pos_dict = net.visualize_ricci_layers(  # doctest: +SKIP
            ...     arrangement="grid", share_layout=True
            ... )
            >>> import matplotlib.pyplot as plt
            >>> plt.show()

        See Also:
            visualize_ricci_core: Core network visualization with Ricci flow
            visualize_ricci_supra: Supra-graph visualization with Ricci flow
        """
        from py3plex.visualization.ricci_multilayer_vis import (
            visualize_multilayer_ricci_layers,
        )

        return visualize_multilayer_ricci_layers(
            self,
            layers=layers,
            alpha=alpha,
            iterations=iterations,
            layout_type=layout_type,
            share_layout=share_layout,
            **kwargs
        )

    def visualize_ricci_supra(
        self,
        alpha: float = 0.5,
        iterations: int = 10,
        layout_type: str = "mds",
        dim: int = 2,
        **kwargs
    ):
        """
        Visualize the full supra-graph using Ricci-flow-based layout.

        This method visualizes the complete multilayer structure including both
        intra-layer edges (within layers) and inter-layer edges (coupling between
        layers) using a layout derived from Ricci flow.

        Args:
            alpha: Ollivier-Ricci parameter. Default: 0.5.
            iterations: Number of Ricci flow iterations. Default: 10.
            layout_type: Layout algorithm. Default: "mds".
            dim: Dimensionality (2 or 3). Default: 2.
            **kwargs: Additional arguments passed to visualize_multilayer_ricci_supra.

        Returns:
            Tuple of (figure, axes, positions_dict).

        Raises:
            RicciBackendNotAvailable: If GraphRicciCurvature is not installed.

        Examples:
            >>> fig, ax, pos = net.visualize_ricci_supra(dim=3)  # doctest: +SKIP
            >>> import matplotlib.pyplot as plt
            >>> plt.show()

        See Also:
            visualize_ricci_core: Core network visualization with Ricci flow
            visualize_ricci_layers: Per-layer visualization with Ricci flow
        """
        from py3plex.visualization.ricci_multilayer_vis import (
            visualize_multilayer_ricci_supra,
        )

        return visualize_multilayer_ricci_supra(
            self,
            alpha=alpha,
            iterations=iterations,
            layout_type=layout_type,
            dim=dim,
            **kwargs
        )

    # ═════════════════════════════════════════════════════════════════════════
    # DSL Query Methods
    # ═════════════════════════════════════════════════════════════════════════

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a DSL query on this multilayer network.

        This is a convenience method that provides first-class access to the
        py3plex DSL (Domain-Specific Language) for querying multilayer networks.
        
        Supports both SELECT and MATCH queries:
        
        SELECT queries:
            net.execute_query('SELECT nodes WHERE layer="transport"')
            net.execute_query('SELECT * FROM nodes IN LAYER "ppi" WHERE degree > 10')
        
        MATCH queries (Cypher-like):
            net.execute_query('MATCH (g:Gene)-[r]->(t:Gene) RETURN g, t')
            net.execute_query('MATCH (a)-[e]->(b) IN LAYER "ppi" WHERE a.degree > 5 RETURN a, b')

        Args:
            query: DSL query string

        Returns:
            Dictionary containing query results:
                - For SELECT queries: 'nodes' or 'edges' list, 'count', optional 'computed'
                - For MATCH queries: 'bindings' list, 'count', 'type'

        Raises:
            DSLSyntaxError: If query syntax is invalid
            DSLExecutionError: If query cannot be executed

        Examples:
            >>> net = multi_layer_network(directed=False)
            >>> _ = net.add_nodes([{'source': 'A', 'type': 'layer1'}])
            >>> _ = net.add_edges([{'source': 'A', 'target': 'B',
            ...                 'source_type': 'layer1', 'target_type': 'layer1'}])
            >>> result = net.execute_query('SELECT nodes WHERE layer="layer1"')
            >>> result['count'] >= 0
            True
            
            >>> # Using MATCH syntax
            >>> result = net.execute_query('MATCH (a:layer1)-[r]->(b:layer1) RETURN a, b')
            >>> 'bindings' in result
            True

        See Also:
            - :func:`py3plex.dsl.execute_query` for standalone function
            - :func:`py3plex.dsl.format_result` for formatting results
        """
        from py3plex.dsl import execute_query as dsl_execute_query
        return dsl_execute_query(self, query)

    def from_homogeneous_hypergraph(self, H):
        """
        Decode a homogeneous graph created by to_homogeneous_hypergraph.

        This method reconstructs a multiplex network from its incidence gadget encoding.
        It identifies edge-nodes by their degree and cycle structure, then reconstructs
        the original layers based on cycle lengths (prime numbers).

        Parameters
        ----------
        H : networkx.Graph
            Homogeneous graph created by to_homogeneous_hypergraph().

        Returns
        -------
        dict
            Dictionary mapping layer names to lists of edges: {layer: [(u, v), ...]}

        Examples:
            Example requires proper network setup - for illustration only.
            
            >>> network = multi_layer_network()  # doctest: +SKIP
            >>> network.add_layer("A")  # doctest: +SKIP
            >>> network.add_nodes([("1", "A"), ("2", "A")])  # doctest: +SKIP
            >>> network.add_edges([(("1", "A"), ("2", "A"))])  # doctest: +SKIP
            >>> H, node_map, edge_info = network.to_homogeneous_hypergraph()  # doctest: +SKIP
            >>> recovered = network.from_homogeneous_hypergraph(H)  # doctest: +SKIP
            >>> print(recovered)  # doctest: +SKIP
            {'layer_with_prime_2': [('1', '2')]}

        Notes
        -----
        The decoded layer names indicate the prime number used for encoding:
        - "layer_with_prime_2" corresponds to the first layer
        - "layer_with_prime_3" corresponds to the second layer, etc.
        """
        multiplex = {}

        for n in H.nodes():
            # Heuristic: edge-nodes are adjacent to two vertex-nodes (starting with 'v_')
            v_neighbors = [v for v in H[n] if str(v).startswith("v_")]
            if len(v_neighbors) == 2:
                # Find cycle length by checking signature nodes
                # The edge-node is connected to signature nodes forming a cycle
                all_neighbors = list(H[n])
                signature_neighbors = [
                    v for v in all_neighbors if not str(v).startswith("v_")
                ]

                # The cycle includes the edge-node itself plus all signature nodes
                # For a cycle of length p, we have: edge-node + (p-1) signature nodes
                cycle_len = len(signature_neighbors) + 1

                layer = f"layer_with_prime_{cycle_len}"
                u = str(v_neighbors[0]).replace("v_", "")
                v = str(v_neighbors[1]).replace("v_", "")
                multiplex.setdefault(layer, []).append((u, v))

        return multiplex

    # ═════════════════════════════════════════════════════════════════════════
    # Community/Partition Management Methods
    # ═════════════════════════════════════════════════════════════════════════

    def assign_partition(
        self, partition: Dict[Tuple[Any, Any], int]
    ) -> None:
        """
        Assign community partition to network nodes.

        This method stores the community assignments as node attributes and
        computes community-level statistics.

        Parameters
        ----------
        partition : dict
            Dictionary mapping (node, layer) tuples to community IDs.

        Examples
        --------
        >>> from py3plex.core import multinet
        >>> net = multinet.multi_layer_network(directed=False)
        >>> _ = net.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type='list')
        >>> partition = {('A', 'L1'): 0, ('B', 'L1'): 0}
        >>> net.assign_partition(partition)
        >>> print(net.community_sizes)
        {0: 2}
        """
        # Store partition as node attribute
        for (node, layer), community_id in partition.items():
            if (node, layer) in self.core_network.nodes:
                self.core_network.nodes[(node, layer)]["community"] = community_id

        # Compute community sizes
        community_counts: Dict[int, int] = {}
        for community_id in partition.values():
            community_counts[community_id] = community_counts.get(community_id, 0) + 1

        self.community_sizes = community_counts

    def get_partition(self, node: Any, layer: Any = None) -> Optional[int]:
        """
        Get the community/partition ID for a given node.

        Parameters
        ----------
        node : Any
            Node identifier.
        layer : Any, optional
            Layer identifier. If None and node is a tuple, assumes node is (node_id, layer).

        Returns
        -------
        int or None
            Community ID, or None if node doesn't have a partition assigned.

        Examples
        --------
        >>> from py3plex.core import multinet
        >>> net = multinet.multi_layer_network(directed=False)
        >>> _ = net.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type='list')
        >>> partition = {('A', 'L1'): 0, ('B', 'L1'): 1}
        >>> net.assign_partition(partition)
        >>> print(net.get_partition('A', 'L1'))
        0
        """
        # Handle different input formats
        if layer is None and isinstance(node, tuple) and len(node) == 2:
            node, layer = node

        node_tuple = (node, layer)
        if node_tuple in self.core_network.nodes:
            return self.core_network.nodes[node_tuple].get("community")
        return None

    def get_node_attribute(
        self, node: Any, attribute: str, layer: Any = None
    ) -> Any:
        """
        Get an attribute value for a given node.

        Parameters
        ----------
        node : Any
            Node identifier.
        attribute : str
            Name of the attribute to retrieve.
        layer : Any, optional
            Layer identifier. If None and node is a tuple, assumes node is (node_id, layer).

        Returns
        -------
        Any
            The attribute value, or None if not found.

        Examples
        --------
        >>> from py3plex.core import multinet
        >>> net = multinet.multi_layer_network(directed=False)
        >>> _ = net.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type='list')
        >>> net.set_node_attribute('A', 'score', 42.0, 'L1')
        >>> print(net.get_node_attribute('A', 'score', 'L1'))
        42.0
        """
        # Handle different input formats
        if layer is None and isinstance(node, tuple) and len(node) == 2:
            node, layer = node

        node_tuple = (node, layer)
        if node_tuple in self.core_network.nodes:
            return self.core_network.nodes[node_tuple].get(attribute)
        return None

    def set_node_attribute(
        self, node: Any, attribute: str, value: Any, layer: Any = None
    ) -> None:
        """
        Set an attribute value for a given node.

        Parameters
        ----------
        node : Any
            Node identifier.
        attribute : str
            Name of the attribute to set.
        value : Any
            Value to assign to the attribute.
        layer : Any, optional
            Layer identifier. If None and node is a tuple, assumes node is (node_id, layer).

        Examples
        --------
        >>> from py3plex.core import multinet
        >>> net = multinet.multi_layer_network(directed=False)
        >>> _ = net.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type='list')
        >>> net.set_node_attribute('A', 'score', 42.0, 'L1')
        >>> print(net.get_node_attribute('A', 'score', 'L1'))
        42.0
        """
        # Handle different input formats
        if layer is None and isinstance(node, tuple) and len(node) == 2:
            node, layer = node

        node_tuple = (node, layer)
        if node_tuple in self.core_network.nodes:
            self.core_network.nodes[node_tuple][attribute] = value


if __name__ == "__main__":

    multinet = multi_layer_network("../../datasets/imdb_gml.gml")
    multinet.basic_stats()
