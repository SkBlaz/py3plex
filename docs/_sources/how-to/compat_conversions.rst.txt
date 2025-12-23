Cross-Ecosystem Compatibility
==============================

The py3plex compatibility layer provides **lossless conversion** between py3plex multilayer networks and common graph libraries.

Quick Start
-----------

Basic conversion between py3plex and NetworkX:

.. code-block:: python

    from py3plex.compat import convert
    from py3plex.io.schema import MultiLayerGraph, Node, Layer, Edge

    # Create a py3plex graph
    graph = MultiLayerGraph(directed=False)
    graph.add_layer(Layer(id="social"))
    graph.add_node(Node(id="Alice", attributes={"age": 30}))
    graph.add_node(Node(id="Bob", attributes={"age": 25}))
    graph.add_edge(Edge(src="Alice", dst="Bob",
                       src_layer="social", dst_layer="social",
                       attributes={"weight": 0.8}))

    # Convert to NetworkX
    nx_graph = convert(graph, "networkx")

    # Convert back to py3plex
    restored = convert(nx_graph, "py3plex")

Supported Formats
-----------------

The ``convert()`` function supports the following targets:

* **networkx** — NetworkX graphs (MultiGraph, DiGraph, etc.)
* **scipy_sparse** — SciPy sparse matrices (CSR, CSC, COO, etc.)
* **igraph** — igraph Graph objects (requires ``python-igraph``)
* **pyg** — PyTorch Geometric Data (stub, coming soon)
* **dgl** — DGL graphs (stub, coming soon)

Conversion Modes
----------------

**Strict Mode** (default)
    Raises ``CompatibilityError`` if target cannot represent all data:

    .. code-block:: python

        from py3plex.compat.exceptions import CompatibilityError

        try:
            # SciPy sparse can't store attributes
            matrix = convert(graph, "scipy_sparse", strict=True)
        except CompatibilityError as e:
            print(f"Cannot convert: {e.reason}")
            for suggestion in e.suggestions:
                print(f"  - {suggestion}")

**Compatibility Mode**
    Uses sidecar bundles to preserve data that target format can't represent:

    .. code-block:: python

        # Convert with sidecar for attributes
        matrix = convert(graph, "scipy_sparse",
                        strict=False,
                        sidecar="graph_data")

        # Later: restore with all attributes
        restored = convert(matrix, "py3plex",
                          sidecar="graph_data")

NetworkX Conversions
--------------------

NetworkX is the most feature-complete target, supporting:

* Directed and undirected graphs
* Multigraphs (parallel edges)
* All node and edge attributes
* Self-loops

Example with NetworkX algorithms:

.. code-block:: python

    import networkx as nx
    from py3plex.compat import convert

    # Convert to NetworkX
    nx_graph = convert(py3plex_graph, "networkx")

    # Use NetworkX algorithms
    centrality = nx.betweenness_centrality(nx_graph)
    communities = nx.community.greedy_modularity_communities(nx_graph)

    # Convert back
    restored = convert(nx_graph, "py3plex")

SciPy Sparse Conversions
-------------------------

Sparse matrices are useful for large graphs and linear algebra operations:

.. code-block:: python

    import scipy.sparse.linalg

    # Convert to sparse matrix (compat mode for attributes)
    matrix = convert(graph, "scipy_sparse",
                    strict=False,
                    sidecar="bundle",
                    format="csr")

    # Compute eigenvalues
    eigenvalues, eigenvectors = scipy.sparse.linalg.eigs(matrix, k=10)

    # Restore graph with attributes
    restored = convert(matrix, "py3plex", sidecar="bundle")

**Important:** Sparse matrices cannot represent:

* Node/edge attributes (use sidecar in compat mode)
* Multigraphs/parallel edges (use sidecar or aggregate)
* Non-numeric edge weights

igraph Conversions
------------------

igraph provides high-performance graph algorithms:

.. code-block:: python

    # Requires: pip install python-igraph
    try:
        ig_graph = convert(py3plex_graph, "igraph")

        # Use igraph algorithms
        communities = ig_graph.community_multilevel()
        betweenness = ig_graph.betweenness()

        # Convert back
        restored = convert(ig_graph, "py3plex")
    except ConversionNotSupportedError:
        print("Install igraph: pip install python-igraph")

Schema Validation
-----------------

Validate graph compatibility before conversion:

.. code-block:: python

    from py3plex.compat import to_ir
    from py3plex.compat.schema import infer_schema

    # Convert to intermediate representation
    ir = to_ir(graph)

    # Infer and check schema
    schema = infer_schema(ir)
    print(f"Node ID type: {schema.node_id_type}")
    print(f"Directed: {schema.directed}")
    print(f"Multi: {schema.multi}")
    print(f"Attributes: {schema.node_attr_types}")

    # Check for incompatibilities
    if schema.multi:
        print("Warning: Multigraph - SciPy sparse won't work in strict mode")

Sidecar Bundles
---------------

Sidecar bundles preserve complete graph data when target format is lossy:

.. code-block:: python

    from py3plex.compat.sidecar import export_sidecar, import_sidecar
    from py3plex.compat import to_ir

    # Export complete graph data
    ir = to_ir(graph)
    export_sidecar(ir, "my_graph", format="json+parquet")

    # Bundle structure:
    # my_graph/
    #   ├── meta.json          # Graph metadata
    #   ├── nodes.parquet      # Node table
    #   └── edges.parquet      # Edge table

    # Import later
    restored_ir = import_sidecar("my_graph")

Intermediate Representation
----------------------------

All conversions use a canonical intermediate representation (IR):

.. code-block:: python

    from py3plex.compat import to_ir, from_ir

    # Convert to IR
    ir = to_ir(graph)

    # IR structure:
    # - ir.nodes: NodeTable (node_id, node_order, attrs, layer)
    # - ir.edges: EdgeTable (edge_id, src, dst, edge_order, attrs)
    # - ir.meta: GraphMeta (directed, multi, layers, global_attrs)

    # Convert IR to any format
    nx_graph = convert(ir, "networkx")
    scipy_matrix = convert(ir, "scipy_sparse", strict=False)

    # Convert back from IR
    restored = from_ir(ir, target_type="multilayer_graph")

Error Handling
--------------

Three specialized exceptions with actionable messages:

**CompatibilityError**
    Target cannot represent data (strict mode):

    .. code-block:: python

        from py3plex.compat.exceptions import CompatibilityError

        try:
            convert(multigraph, "scipy_sparse", strict=True)
        except CompatibilityError as e:
            print(f"Reason: {e.reason}")
            print("Suggestions:")
            for s in e.suggestions:
                print(f"  - {s}")

**SchemaError**
    Schema validation failure:

    .. code-block:: python

        from py3plex.compat.exceptions import SchemaError

        try:
            validate_against_schema(ir, expected_schema)
        except SchemaError as e:
            print(f"Field '{e.field}': {e}")

**ConversionNotSupportedError**
    Missing optional dependencies:

    .. code-block:: python

        from py3plex.compat.exceptions import ConversionNotSupportedError

        try:
            convert(graph, "igraph")
        except ConversionNotSupportedError as e:
            print(e)  # Clear install instructions

Common Patterns
---------------

**NetworkX to py3plex**

.. code-block:: python

    import networkx as nx
    from py3plex.compat import convert

    G = nx.karate_club_graph()
    py3_graph = convert(G, "py3plex")

**py3plex to SciPy sparse with attributes**

.. code-block:: python

    matrix = convert(graph, "scipy_sparse",
                    strict=False, sidecar="/tmp/bundle")
    # Use matrix for computation
    restored = convert(matrix, "py3plex", sidecar="/tmp/bundle")

**Format-to-format via py3plex**

.. code-block:: python

    # NetworkX → py3plex → igraph
    py3_graph = convert(nx_graph, "py3plex")
    ig_graph = convert(py3_graph, "igraph")

Installation
------------

Basic compatibility layer (NetworkX + SciPy):

.. code-block:: bash

    pip install py3plex[compat]

With optional dependencies:

.. code-block:: bash

    # igraph support
    pip install py3plex[igraph]

    # PyTorch Geometric (coming soon)
    pip install py3plex[pyg]

    # DGL (coming soon)
    pip install py3plex[dgl_compat]

Examples
--------

Complete examples are available in ``examples/io_and_data/example_compat_conversion.py``.

See Also
--------

* :doc:`../reference/compat` — API reference
* :doc:`export_serialize` — I/O and serialization guide
* :doc:`../networkx_interop` — NetworkX compatibility
