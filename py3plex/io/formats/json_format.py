"""
JSON and JSONL format readers and writers.

Supports:
- Canonical JSON format (lossless)
- Streaming JSONL format
- Gzip compression for both formats
"""

import gzip
import json
from pathlib import Path
from typing import Any, Dict, Union

from py3plex.exceptions import Py3plexFormatError

from ..schema import MultiLayerGraph


def _sort_graph_data(data: Dict[str, Any], deterministic: bool) -> Dict[str, Any]:
    """
    Sort graph data for deterministic output.

    Args:
        data: Graph data dictionary
        deterministic: Whether to sort for deterministic output

    Returns:
        Sorted data dictionary
    """
    if not deterministic:
        return data

    # Sort nodes by ID
    if "nodes" in data:
        data["nodes"] = sorted(data["nodes"], key=lambda n: str(n["id"]))

    # Sort layers by ID
    if "layers" in data:
        data["layers"] = sorted(data["layers"], key=lambda l: str(l["id"]))

    # Sort edges by (src, dst, src_layer, dst_layer, key)
    if "edges" in data:
        data["edges"] = sorted(
            data["edges"],
            key=lambda e: (
                str(e["src"]),
                str(e["dst"]),
                str(e["src_layer"]),
                str(e["dst_layer"]),
                e.get("key", 0),
            ),
        )

    return data


def read_json(filepath: Union[str, Path], **kwargs) -> MultiLayerGraph:
    """
    Read a multilayer graph from a JSON file.

    Args:
        filepath: Path to JSON file (supports .json and .json.gz)
        **kwargs: Additional arguments (ignored)

    Returns:
        MultiLayerGraph instance
    """
    filepath = Path(filepath)

    # Handle gzip compression
    if filepath.suffix == ".gz":
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            data = json.load(f)
    else:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

    return MultiLayerGraph.from_dict(data)


def write_json(
    graph: MultiLayerGraph,
    filepath: Union[str, Path],
    deterministic: bool = False,
    indent: int = 2,
    **kwargs,
) -> None:
    """
    Write a multilayer graph to a JSON file.

    Args:
        graph: MultiLayerGraph to write
        filepath: Path to output JSON file (supports .json and .json.gz)
        deterministic: If True, sort nodes/edges for consistent output
        indent: JSON indentation level (None for compact output)
        **kwargs: Additional arguments (ignored)
    """
    filepath = Path(filepath)

    # Convert to dict
    data = graph.to_dict()

    # Sort for deterministic output if requested
    if deterministic:
        data = _sort_graph_data(data, deterministic=True)

    # Create parent directory if needed
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Handle gzip compression
    if filepath.suffix == ".gz":
        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)


def read_jsonl(filepath: Union[str, Path], **kwargs) -> MultiLayerGraph:
    """
    Read a multilayer graph from a JSONL file (streaming format).

    JSONL format has one JSON object per line:
    - Line 1: graph metadata (directed, attributes)
    - Following lines: nodes (type='node'), layers (type='layer'), edges (type='edge')

    Args:
        filepath: Path to JSONL file (supports .jsonl and .jsonl.gz)
        **kwargs: Additional arguments (ignored)

    Returns:
        MultiLayerGraph instance
    """
    filepath = Path(filepath)

    # Storage for parsed data
    nodes = []
    layers = []
    edges = []
    directed = True
    attributes = {}

    # Open file (with or without gzip)
    if filepath.suffix == ".gz":
        f = gzip.open(filepath, "rt", encoding="utf-8")
    else:
        f = open(filepath, encoding="utf-8")

    try:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise Py3plexFormatError(
                    f"Invalid JSON on line {line_num}: {e}. "
                    f"Please ensure the JSONL file contains valid JSON objects, one per line."
                )

            # First line is graph metadata
            if line_num == 1:
                directed = obj.get("directed", True)
                attributes = obj.get("attributes", {})
            else:
                # Parse based on type
                obj_type = obj.get("type")
                if obj_type == "node":
                    nodes.append(obj)
                elif obj_type == "layer":
                    layers.append(obj)
                elif obj_type == "edge":
                    edges.append(obj)
                else:
                    raise Py3plexFormatError(
                        f"Unknown object type '{obj_type}' on line {line_num}. "
                        f"Expected types: 'node', 'layer', or 'edge'."
                    )
    finally:
        f.close()

    # Construct graph data
    data = {
        "nodes": nodes,
        "layers": layers,
        "edges": edges,
        "directed": directed,
        "attributes": attributes,
    }

    return MultiLayerGraph.from_dict(data)


def write_jsonl(
    graph: MultiLayerGraph,
    filepath: Union[str, Path],
    deterministic: bool = False,
    **kwargs,
) -> None:
    """
    Write a multilayer graph to a JSONL file (streaming format).

    JSONL format has one JSON object per line for efficient streaming.

    Args:
        graph: MultiLayerGraph to write
        filepath: Path to output JSONL file (supports .jsonl and .jsonl.gz)
        deterministic: If True, sort nodes/edges for consistent output
        **kwargs: Additional arguments (ignored)
    """
    filepath = Path(filepath)

    # Convert to dict
    data = graph.to_dict()

    # Sort for deterministic output if requested
    if deterministic:
        data = _sort_graph_data(data, deterministic=True)

    # Create parent directory if needed
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Open file (with or without gzip)
    if filepath.suffix == ".gz":
        f = gzip.open(filepath, "wt", encoding="utf-8")
    else:
        f = open(filepath, "w", encoding="utf-8")

    try:
        # Write graph metadata
        metadata = {
            "directed": data["directed"],
            "attributes": data["attributes"],
        }
        f.write(json.dumps(metadata) + "\n")

        # Write nodes
        for node in data["nodes"]:
            node_obj = {**node, "type": "node"}
            f.write(json.dumps(node_obj) + "\n")

        # Write layers
        for layer in data["layers"]:
            layer_obj = {**layer, "type": "layer"}
            f.write(json.dumps(layer_obj) + "\n")

        # Write edges
        for edge in data["edges"]:
            edge_obj = {**edge, "type": "edge"}
            f.write(json.dumps(edge_obj) + "\n")
    finally:
        f.close()
