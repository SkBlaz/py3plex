"""
Parquet directory format for multilayer networks.

This module implements lossless save/load of multilayer networks using a directory layout:
- path/nodes.parquet: Node table with (node, layer) and attributes
- path/edges.parquet: Edge table with (source, target, source_layer, target_layer) and attributes
- path/metadata.json: Network metadata (network_type, directed, coupling, schema version, etc.)

The format ensures zero-loss roundtrip for:
- Node replicas (node_id, layer)
- Edge replicas (source, target, source_layer, target_layer)
- Directedness, network_type, coupling semantics
- Scalar and complex attributes (JSON-encoded)
- Stable network fingerprint
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Union
import shutil

try:
    import pyarrow as pa
    import pyarrow.parquet as pq

    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False

from py3plex.exceptions import Py3plexIOError
from py3plex.io.schema import Edge, Layer, MultiLayerGraph, Node
from py3plex.io.multinet_bridge import (
    multinet_to_multilayergraph,
    multilayergraph_to_multinet,
)


def _normalize_value(value):
    """Convert pyarrow/pandas scalar containers to JSON-serializable Python values."""
    if hasattr(value, "tolist"):
        try:
            return value.tolist()
        except TypeError:
            pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


def save_network_to_parquet(net, path: Union[str, Path]) -> None:
    """
    Save a multi_layer_network to Parquet directory format.

    Creates a directory with:
    - nodes.parquet: Node table
    - edges.parquet: Edge table
    - metadata.json: Network metadata

    Args:
        net: multi_layer_network instance
        path: Directory path (will be created if doesn't exist)

    Raises:
        Py3plexIOError: If save fails or pyarrow not available
    """
    if not PARQUET_AVAILABLE:
        raise Py3plexIOError(
            "PyArrow is required for Parquet support. "
            "Install it with: pip install pyarrow"
        )

    path = Path(path)

    # Convert network to MultiLayerGraph
    try:
        graph = multinet_to_multilayergraph(net)
    except Exception as e:
        raise Py3plexIOError(f"Failed to convert network for Parquet export: {e}")

    staging = None
    backup = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".parquet-", dir=path.parent))
        staged_export = staging / "export"
        staged_export.mkdir()

        # Keep attributes separate from structural fields and preserve sparse
        # columns and heterogeneous attribute values on every record.
        nodes = [
            {"node": node.id, "attributes": json.dumps(node.attributes)}
            for node in graph.nodes.values()
        ]
        edges = [
            {
                "source": edge.src,
                "target": edge.dst,
                "source_layer": json.dumps(edge.src_layer),
                "target_layer": json.dumps(edge.dst_layer),
                "edge_key": json.dumps(edge.key),
                "attributes": json.dumps(edge.attributes),
            }
            for edge in graph.edges
        ]
        for name, records, columns in (
            ("nodes", nodes, ("node", "attributes")),
            (
                "edges",
                edges,
                (
                    "source",
                    "target",
                    "source_layer",
                    "target_layer",
                    "edge_key",
                    "attributes",
                ),
            ),
        ):
            schema = pa.schema([(column, pa.string()) for column in columns])
            pq.write_table(
                pa.Table.from_pylist(records, schema=schema),
                staged_export / f"{name}.parquet",
            )

        metadata = {
            **graph.attributes,
            "directed": graph.directed,
            "layers": [layer.id for layer in graph.layers.values()],
            "parquet_layout_version": 2,
        }
        (staged_export / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

        if path.exists():
            if not path.is_dir() or path.is_symlink():
                raise ValueError(f"Parquet destination must be a directory: {path}")
            backup = staging / "previous"
            os.replace(path, backup)
        try:
            staged_export.rename(path)
        except Exception:
            if backup is not None and backup.exists():
                try:
                    os.replace(backup, path)
                except OSError as restore_error:
                    raise Py3plexIOError(
                        f"Failed to restore the previous Parquet directory. "
                        f"The previous export is available at {backup}: {restore_error}"
                    ) from restore_error
            raise
        backup = None
    except Py3plexIOError:
        raise
    except Exception as e:
        raise Py3plexIOError(f"Failed to write Parquet directory: {e}") from e
    finally:
        if staging is not None and (backup is None or not backup.exists()):
            shutil.rmtree(staging, ignore_errors=True)


def _decode_identity(value):
    """Restore tuples used as edge keys or layer identifiers."""
    if isinstance(value, list):
        return tuple(_decode_identity(part) for part in value)
    return value


def _legacy_attributes(row, reserved):
    attrs = {}
    for key, value in row.items():
        if key not in reserved:
            value = _normalize_value(value)
            if not (isinstance(value, float) and str(value) == "nan"):
                attrs[key] = value
    return attrs


def load_network_from_parquet(path: Union[str, Path]):
    """
    Load a multi_layer_network from Parquet directory format.

    Reads:
    - nodes.parquet: Node table
    - edges.parquet: Edge table
    - metadata.json: Network metadata

    Args:
        path: Directory path

    Returns:
        multi_layer_network instance

    Raises:
        Py3plexIOError: If load fails or required files missing
    """
    if not PARQUET_AVAILABLE:
        raise Py3plexIOError(
            "PyArrow is required for Parquet support. "
            "Install it with: pip install pyarrow"
        )

    path = Path(path)

    if not path.exists() or not path.is_dir():
        raise Py3plexIOError(f"Parquet directory not found: {path}")

    # Check required files
    nodes_file = path / "nodes.parquet"
    edges_file = path / "edges.parquet"
    metadata_file = path / "metadata.json"

    if not nodes_file.exists():
        raise Py3plexIOError(f"Missing nodes.parquet in {path}")
    if not edges_file.exists():
        raise Py3plexIOError(f"Missing edges.parquet in {path}")
    if not metadata_file.exists():
        raise Py3plexIOError(f"Missing metadata.json in {path}")

    try:
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        version = metadata.pop("parquet_layout_version", 1)
        layers = metadata.pop("layers", [])
        graph = MultiLayerGraph(
            directed=metadata.pop("directed", False),
            attributes=metadata,
        )
        for layer in layers:
            graph.add_layer(Layer(id=_decode_identity(layer), attributes={}))

        nodes = pq.read_table(nodes_file)
        edges = pq.read_table(edges_file)
        if version == 2:
            for row in nodes.to_pylist():
                attrs = json.loads(row["attributes"])
                if "__layer__" in attrs:
                    attrs["__layer__"] = _decode_identity(attrs["__layer__"])
                graph.add_node(Node(id=row["node"], attributes=attrs))
            for row in edges.to_pylist():
                graph.add_edge(
                    Edge(
                        src=row["source"],
                        dst=row["target"],
                        src_layer=_decode_identity(json.loads(row["source_layer"])),
                        dst_layer=_decode_identity(json.loads(row["target_layer"])),
                        key=_decode_identity(json.loads(row["edge_key"])),
                        attributes=json.loads(row["attributes"]),
                    )
                )
        elif version == 1:
            for _, row in nodes.to_pandas().iterrows():
                graph.add_node(
                    Node(id=row["node"], attributes=_legacy_attributes(row, {"node"}))
                )
            reserved = {"source", "target", "source_layer", "target_layer"}
            for _, row in edges.to_pandas().iterrows():
                graph.add_edge(
                    Edge(
                        src=row["source"],
                        dst=row["target"],
                        src_layer=row["source_layer"],
                        dst_layer=row["target_layer"],
                        attributes=_legacy_attributes(row, reserved),
                    )
                )
        else:
            raise ValueError(f"Unsupported Parquet directory layout: {version}")

        return multilayergraph_to_multinet(graph)
    except Exception as e:
        raise Py3plexIOError(f"Failed to read Parquet directory: {e}") from e
