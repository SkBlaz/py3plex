"""
CSV format readers and writers for multilayer graphs.

Supports:
- Edge list CSV with required columns (src, dst, src_layer, dst_layer)
- Optional columns (weight, is_directed, key) and dynamic edge attributes
- Sidecar files for nodes (nodes.csv) and layers (layers.csv)
"""

import csv
import gzip
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from ..exceptions import SchemaValidationError
from ..schema import Edge, Layer, MultiLayerGraph, Node


def _sort_graph_data_csv(
    graph: MultiLayerGraph, deterministic: bool
) -> tuple[List[Node], List[Layer], List[Edge]]:
    """
    Sort graph components for deterministic CSV output.

    Args:
        graph: MultiLayerGraph to sort
        deterministic: Whether to sort

    Returns:
        Tuple of (sorted_nodes, sorted_layers, sorted_edges)
    """
    if deterministic:
        nodes = sorted(graph.nodes.values(), key=lambda n: str(n.id))
        layers = sorted(graph.layers.values(), key=lambda l: str(l.id))
        edges = sorted(
            graph.edges,
            key=lambda e: (
                str(e.src),
                str(e.dst),
                str(e.src_layer),
                str(e.dst_layer),
                e.key,
            ),
        )
    else:
        nodes = list(graph.nodes.values())
        layers = list(graph.layers.values())
        edges = graph.edges

    return nodes, layers, edges


def read_csv(
    filepath: Union[str, Path],
    nodes_file: Optional[Union[str, Path]] = None,
    layers_file: Optional[Union[str, Path]] = None,
    delimiter: str = ",",
    **kwargs,
) -> MultiLayerGraph:
    """
    Read a multilayer graph from a CSV edge list file.

    Required columns in edge file: src, dst, src_layer, dst_layer
    Optional columns: weight, is_directed, key, or any custom attribute

    Args:
        filepath: Path to CSV edge list file
        nodes_file: Optional path to nodes.csv sidecar file
        layers_file: Optional path to layers.csv sidecar file
        delimiter: CSV delimiter (default: ',')
        **kwargs: Additional arguments (ignored)

    Returns:
        MultiLayerGraph instance

    Raises:
        SchemaValidationError: If required columns are missing
    """
    filepath = Path(filepath)

    # Storage
    nodes_dict: Dict[Any, Dict[str, Any]] = {}
    layers_dict: Dict[Any, Dict[str, Any]] = {}
    edges_list: List[Dict[str, Any]] = []

    # Load sidecar nodes file if provided
    if nodes_file is not None:
        nodes_file = Path(nodes_file)
        with open(nodes_file, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                if "id" not in row:
                    raise SchemaValidationError(
                        f"Nodes CSV file must have 'id' column: {nodes_file}"
                    )
                node_id = row["id"]
                # All other columns become attributes
                attributes = {k: v for k, v in row.items() if k != "id"}
                nodes_dict[node_id] = attributes

    # Load sidecar layers file if provided
    if layers_file is not None:
        layers_file = Path(layers_file)
        with open(layers_file, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                if "id" not in row:
                    raise SchemaValidationError(
                        f"Layers CSV file must have 'id' column: {layers_file}"
                    )
                layer_id = row["id"]
                # All other columns become attributes
                attributes = {k: v for k, v in row.items() if k != "id"}
                layers_dict[layer_id] = attributes

    # Read edges
    if filepath.suffix == ".gz":
        edge_fh = gzip.open(filepath, "rt", encoding="utf-8")
    else:
        edge_fh = open(filepath, encoding="utf-8")

    with edge_fh as f:
        reader = csv.DictReader(f, delimiter=delimiter)

        # Check required columns
        if reader.fieldnames is None:
            raise SchemaValidationError("CSV file is empty or has no header")

        required_cols = {"src", "dst", "src_layer", "dst_layer"}
        missing_cols = required_cols - set(reader.fieldnames)
        if missing_cols:
            raise SchemaValidationError(
                f"CSV file missing required columns: {missing_cols}"
            )

        for row in reader:
            src = row["src"]
            dst = row["dst"]
            src_layer = row["src_layer"]
            dst_layer = row["dst_layer"]

            # Add nodes if not already present
            if src not in nodes_dict:
                nodes_dict[src] = {}
            if dst not in nodes_dict:
                nodes_dict[dst] = {}

            # Add layers if not already present
            if src_layer not in layers_dict:
                layers_dict[src_layer] = {}
            if dst_layer not in layers_dict:
                layers_dict[dst_layer] = {}

            # Parse optional columns
            key = int(row.get("key", 0))

            # All other columns become edge attributes
            edge_attrs = {}
            for col in reader.fieldnames:
                if col not in {"src", "dst", "src_layer", "dst_layer", "key"}:
                    value = row[col]
                    # Try to convert to number if possible
                    try:
                        if "." in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except (ValueError, AttributeError):
                        pass  # Keep as string
                    edge_attrs[col] = value

            edges_list.append(
                {
                    "src": src,
                    "dst": dst,
                    "src_layer": src_layer,
                    "dst_layer": dst_layer,
                    "key": key,
                    "attributes": edge_attrs,
                }
            )

    # Build graph data
    graph_data = {
        "nodes": [
            {"id": nid, "attributes": attrs} for nid, attrs in nodes_dict.items()
        ],
        "layers": [
            {"id": lid, "attributes": attrs} for lid, attrs in layers_dict.items()
        ],
        "edges": edges_list,
        "directed": True,  # Default to directed for CSV
        "attributes": {},
    }

    return MultiLayerGraph.from_dict(graph_data)


def write_csv(
    graph: MultiLayerGraph,
    filepath: Union[str, Path],
    delimiter: str = ",",
    deterministic: bool = False,
    write_sidecars: bool = False,
    **kwargs,
) -> None:
    """
    Write a multilayer graph to a CSV edge list file.

    Columns written: src, dst, src_layer, dst_layer, key, <edge attributes>

    Args:
        graph: MultiLayerGraph to write
        filepath: Path to output CSV edge list file
        delimiter: CSV delimiter (default: ',')
        deterministic: If True, sort nodes/edges for consistent output
        write_sidecars: If True, write nodes.csv and layers.csv sidecar files
        **kwargs: Additional arguments (ignored)
    """
    filepath = Path(filepath)

    # Create parent directory if needed
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Sort if deterministic
    nodes, layers, edges = _sort_graph_data_csv(graph, deterministic)

    # Collect all edge attribute keys for consistent column ordering
    edge_attr_keys_set: Set[str] = set()
    for edge in edges:
        edge_attr_keys_set.update(edge.attributes.keys())

    # Sort attribute keys for deterministic output
    edge_attr_keys: List[str]
    if deterministic:
        edge_attr_keys = sorted(edge_attr_keys_set)
    else:
        edge_attr_keys = list(edge_attr_keys_set)

    # Write edges
    if filepath.suffix == ".gz":
        edge_fh = gzip.open(filepath, "wt", encoding="utf-8", newline="")
    else:
        edge_fh = open(filepath, "w", encoding="utf-8", newline="")

    with edge_fh as f:
        # Define columns
        columns = ["src", "dst", "src_layer", "dst_layer", "key"] + list(edge_attr_keys)
        writer = csv.DictWriter(f, fieldnames=columns, delimiter=delimiter)
        writer.writeheader()

        for edge in edges:
            row = {
                "src": edge.src,
                "dst": edge.dst,
                "src_layer": edge.src_layer,
                "dst_layer": edge.dst_layer,
                "key": edge.key,
            }
            # Add edge attributes
            for attr_key in edge_attr_keys:
                row[attr_key] = edge.attributes.get(attr_key, "")
            writer.writerow(row)

    # Write sidecar files if requested
    if write_sidecars:
        # Write nodes.csv
        nodes_file = filepath.parent / "nodes.csv"
        if nodes:
            # Collect all node attribute keys
            node_attr_keys_set: Set[str] = set()
            for node in nodes:
                node_attr_keys_set.update(node.attributes.keys())

            node_attr_keys: List[str]
            if deterministic:
                node_attr_keys = sorted(node_attr_keys_set)
            else:
                node_attr_keys = list(node_attr_keys_set)

            with open(nodes_file, "w", encoding="utf-8", newline="") as f:
                columns = ["id"] + list(node_attr_keys)
                writer = csv.DictWriter(f, fieldnames=columns, delimiter=delimiter)
                writer.writeheader()

                for node in nodes:
                    row = {"id": node.id}
                    for attr_key in node_attr_keys:
                        row[attr_key] = node.attributes.get(attr_key, "")
                    writer.writerow(row)

        # Write layers.csv
        layers_file = filepath.parent / "layers.csv"
        if layers:
            # Collect all layer attribute keys
            layer_attr_keys_set: Set[str] = set()
            for layer in layers:
                layer_attr_keys_set.update(layer.attributes.keys())

            layer_attr_keys: List[str]
            if deterministic:
                layer_attr_keys = sorted(layer_attr_keys_set)
            else:
                layer_attr_keys = list(layer_attr_keys_set)

            with open(layers_file, "w", encoding="utf-8", newline="") as f:
                columns = ["id"] + list(layer_attr_keys)
                writer = csv.DictWriter(f, fieldnames=columns, delimiter=delimiter)
                writer.writeheader()

                for layer in layers:
                    row = {"id": layer.id}
                    for attr_key in layer_attr_keys:
                        row[attr_key] = layer.attributes.get(attr_key, "")
                    writer.writerow(row)
