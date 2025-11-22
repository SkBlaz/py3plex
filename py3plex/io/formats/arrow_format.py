"""
Apache Arrow format readers and writers for multilayer graphs.

Supports:
- High-performance columnar storage with Apache Arrow
- IPC format (Feather v2) for fast serialization
- Parquet format for compressed storage
- Schema preservation and type safety
- Interoperability with data science tools (pandas, polars, etc.)
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from py3plex.exceptions import Py3plexFormatError

from ..schema import Edge, Layer, MultiLayerGraph, Node

# Optional pyarrow dependency
try:
    import pyarrow as pa
    import pyarrow.ipc as ipc
    import pyarrow.parquet as pq

    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False


def _check_pyarrow() -> None:
    """Check if pyarrow is available."""
    if not PYARROW_AVAILABLE:
        raise Py3plexFormatError(
            "pyarrow is required for Apache Arrow format. "
            "Install with: pip install 'py3plex[arrow]' or pip install pyarrow"
        )


def _graph_to_arrow_tables(
    graph: MultiLayerGraph,
) -> Dict[str, "pa.Table"]:
    """
    Convert a multilayer graph to Apache Arrow tables.

    Args:
        graph: MultiLayerGraph instance

    Returns:
        Dictionary with 'metadata', 'nodes', 'layers', and 'edges' tables
    """
    _check_pyarrow()

    # Prepare metadata
    metadata = {
        "directed": graph.directed,
        "attributes": json.dumps(graph.attributes),
    }
    metadata_table = pa.table(
        {
            "directed": [metadata["directed"]],
            "attributes": [metadata["attributes"]],
        }
    )

    # Prepare nodes
    if graph.nodes:
        nodes_data = {
            "id": [],
            "attributes": [],
        }
        for node in graph.nodes.values():
            nodes_data["id"].append(str(node.id))
            nodes_data["attributes"].append(json.dumps(node.attributes))
        nodes_table = pa.table(nodes_data)
    else:
        # Empty table with schema
        nodes_table = pa.table(
            {"id": pa.array([], type=pa.string()), "attributes": pa.array([], type=pa.string())}
        )

    # Prepare layers
    if graph.layers:
        layers_data = {
            "id": [],
            "attributes": [],
        }
        for layer in graph.layers.values():
            layers_data["id"].append(str(layer.id))
            layers_data["attributes"].append(json.dumps(layer.attributes))
        layers_table = pa.table(layers_data)
    else:
        # Empty table with schema
        layers_table = pa.table(
            {"id": pa.array([], type=pa.string()), "attributes": pa.array([], type=pa.string())}
        )

    # Prepare edges
    if graph.edges:
        edges_data = {
            "src": [],
            "dst": [],
            "src_layer": [],
            "dst_layer": [],
            "key": [],
            "attributes": [],
        }
        for edge in graph.edges:
            edges_data["src"].append(str(edge.src))
            edges_data["dst"].append(str(edge.dst))
            edges_data["src_layer"].append(str(edge.src_layer))
            edges_data["dst_layer"].append(str(edge.dst_layer))
            edges_data["key"].append(edge.key)
            edges_data["attributes"].append(json.dumps(edge.attributes))
        edges_table = pa.table(edges_data)
    else:
        # Empty table with schema
        edges_table = pa.table(
            {
                "src": pa.array([], type=pa.string()),
                "dst": pa.array([], type=pa.string()),
                "src_layer": pa.array([], type=pa.string()),
                "dst_layer": pa.array([], type=pa.string()),
                "key": pa.array([], type=pa.int64()),
                "attributes": pa.array([], type=pa.string()),
            }
        )

    return {
        "metadata": metadata_table,
        "nodes": nodes_table,
        "layers": layers_table,
        "edges": edges_table,
    }


def _arrow_tables_to_graph(tables: Dict[str, "pa.Table"]) -> MultiLayerGraph:
    """
    Convert Apache Arrow tables to a multilayer graph.

    Args:
        tables: Dictionary with 'metadata', 'nodes', 'layers', and 'edges' tables

    Returns:
        MultiLayerGraph instance
    """
    _check_pyarrow()

    # Parse metadata
    metadata_dict = tables["metadata"].to_pydict()
    directed = metadata_dict["directed"][0]
    attributes = json.loads(metadata_dict["attributes"][0])

    graph = MultiLayerGraph(directed=directed, attributes=attributes)

    # Parse layers
    if tables["layers"].num_rows > 0:
        layers_dict = tables["layers"].to_pydict()
        for i in range(len(layers_dict["id"])):
            layer_id = layers_dict["id"][i]
            layer_attrs = json.loads(layers_dict["attributes"][i])
            graph.add_layer(Layer(id=layer_id, attributes=layer_attrs))

    # Parse nodes
    if tables["nodes"].num_rows > 0:
        nodes_dict = tables["nodes"].to_pydict()
        for i in range(len(nodes_dict["id"])):
            node_id = nodes_dict["id"][i]
            node_attrs = json.loads(nodes_dict["attributes"][i])
            graph.add_node(Node(id=node_id, attributes=node_attrs))

    # Parse edges
    if tables["edges"].num_rows > 0:
        edges_dict = tables["edges"].to_pydict()
        for i in range(len(edges_dict["src"])):
            src = edges_dict["src"][i]
            dst = edges_dict["dst"][i]
            src_layer = edges_dict["src_layer"][i]
            dst_layer = edges_dict["dst_layer"][i]
            key = edges_dict["key"][i]
            edge_attrs = json.loads(edges_dict["attributes"][i])
            graph.add_edge(
                Edge(
                    src=src,
                    dst=dst,
                    src_layer=src_layer,
                    dst_layer=dst_layer,
                    key=key,
                    attributes=edge_attrs,
                )
            )

    return graph


def write_arrow(
    graph: MultiLayerGraph,
    filepath: Union[str, Path],
    format: str = "feather",
    **kwargs,
) -> None:
    """
    Write a multilayer graph to Apache Arrow format.

    Args:
        graph: MultiLayerGraph instance
        filepath: Path to output file
        format: Arrow format to use ('feather' or 'parquet'). Default: 'feather'
        **kwargs: Additional arguments passed to Arrow writer

    Raises:
        Py3plexFormatError: If pyarrow is not installed or format is unsupported

    Example:
        >>> graph = MultiLayerGraph()
        >>> write_arrow(graph, 'network.arrow')  # Feather format
        >>> write_arrow(graph, 'network.parquet', format='parquet')  # Parquet format
    """
    _check_pyarrow()
    filepath = Path(filepath)

    # Convert graph to Arrow tables
    tables = _graph_to_arrow_tables(graph)

    if format == "feather":
        # Write as Feather file (IPC format)
        # Store multiple tables by concatenating with special markers
        with pa.OSFile(str(filepath), "wb") as sink:
            with ipc.new_file(sink, tables["metadata"].schema) as writer:
                writer.write_table(tables["metadata"])

        # Write companion files for nodes, layers, edges
        nodes_path = filepath.with_suffix(filepath.suffix + ".nodes")
        with pa.OSFile(str(nodes_path), "wb") as sink:
            with ipc.new_file(sink, tables["nodes"].schema) as writer:
                writer.write_table(tables["nodes"])

        layers_path = filepath.with_suffix(filepath.suffix + ".layers")
        with pa.OSFile(str(layers_path), "wb") as sink:
            with ipc.new_file(sink, tables["layers"].schema) as writer:
                writer.write_table(tables["layers"])

        edges_path = filepath.with_suffix(filepath.suffix + ".edges")
        with pa.OSFile(str(edges_path), "wb") as sink:
            with ipc.new_file(sink, tables["edges"].schema) as writer:
                writer.write_table(tables["edges"])

    elif format == "parquet":
        # Write as Parquet file with multiple tables
        # Ensure .parquet extension
        if not filepath.suffix == ".parquet":
            filepath = filepath.with_suffix(".parquet")
        
        pq.write_table(tables["metadata"], str(filepath))
        pq.write_table(
            tables["nodes"], str(filepath.with_suffix(filepath.suffix + ".nodes"))
        )
        pq.write_table(
            tables["layers"], str(filepath.with_suffix(filepath.suffix + ".layers"))
        )
        pq.write_table(
            tables["edges"], str(filepath.with_suffix(filepath.suffix + ".edges"))
        )
    else:
        raise Py3plexFormatError(
            f"Unsupported Arrow format: {format}. Use 'feather' or 'parquet'."
        )


def read_arrow(filepath: Union[str, Path], format: str = "feather", **kwargs) -> MultiLayerGraph:
    """
    Read a multilayer graph from Apache Arrow format.

    Args:
        filepath: Path to input file
        format: Arrow format to use ('feather' or 'parquet'). Default: 'feather'
        **kwargs: Additional arguments (ignored)

    Returns:
        MultiLayerGraph instance

    Raises:
        Py3plexFormatError: If pyarrow is not installed or format is unsupported

    Example:
        >>> graph = read_arrow('network.arrow')  # Feather format
        >>> graph = read_arrow('network.parquet', format='parquet')  # Parquet format
    """
    _check_pyarrow()
    filepath = Path(filepath)

    tables = {}

    if format == "feather":
        # Read Feather files
        with pa.memory_map(str(filepath), "r") as source:
            tables["metadata"] = ipc.open_file(source).read_all()

        nodes_path = filepath.with_suffix(filepath.suffix + ".nodes")
        with pa.memory_map(str(nodes_path), "r") as source:
            tables["nodes"] = ipc.open_file(source).read_all()

        layers_path = filepath.with_suffix(filepath.suffix + ".layers")
        with pa.memory_map(str(layers_path), "r") as source:
            tables["layers"] = ipc.open_file(source).read_all()

        edges_path = filepath.with_suffix(filepath.suffix + ".edges")
        with pa.memory_map(str(edges_path), "r") as source:
            tables["edges"] = ipc.open_file(source).read_all()

    elif format == "parquet":
        # Read Parquet files
        # Ensure .parquet extension
        if not filepath.suffix == ".parquet":
            filepath = filepath.with_suffix(".parquet")
        
        tables["metadata"] = pq.read_table(str(filepath))
        tables["nodes"] = pq.read_table(
            str(filepath.with_suffix(filepath.suffix + ".nodes"))
        )
        tables["layers"] = pq.read_table(
            str(filepath.with_suffix(filepath.suffix + ".layers"))
        )
        tables["edges"] = pq.read_table(
            str(filepath.with_suffix(filepath.suffix + ".edges"))
        )
    else:
        raise Py3plexFormatError(
            f"Unsupported Arrow format: {format}. Use 'feather' or 'parquet'."
        )

    # Convert Arrow tables back to graph
    return _arrow_tables_to_graph(tables)
