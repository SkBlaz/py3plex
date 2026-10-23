"""Sidecar bundles must retain identity columns even when a table has no rows."""

import pandas as pd
import pytest

from py3plex.compat.ir import EdgeTable, GraphIR, GraphMeta, NodeTable
from py3plex.compat.sidecar import export_sidecar, import_sidecar


@pytest.mark.parametrize("table_format", ["csv", "parquet"])
@pytest.mark.parametrize("node_ids", [[], ["isolate"]])
@pytest.mark.parametrize("multilayer", [False, True])
def test_sidecar_empty_tables_keep_identity_columns(
    tmp_path, table_format, node_ids, multilayer
):
    if table_format == "parquet":
        pytest.importorskip("pyarrow")
    ir = GraphIR(
        nodes=NodeTable(
            node_id=node_ids,
            node_order=list(range(len(node_ids))),
            attrs=pd.DataFrame({"score": [7] * len(node_ids)}),
            layer=["L"] * len(node_ids) if multilayer else None,
        ),
        edges=EdgeTable(
            edge_id=[],
            src=[],
            dst=[],
            edge_order=[],
            src_layer=[] if multilayer else None,
            dst_layer=[] if multilayer else None,
            key=[] if multilayer else None,
        ),
        meta=GraphMeta(
            directed=True,
            multi=multilayer,
            name="empty edges",
            layers=["L"] if multilayer else None,
            global_attrs={"experiment": 42},
        ),
    )
    bundle = tmp_path / "bundle"
    export_sidecar(ir, str(bundle), format=f"json+{table_format}")

    # Verify the artifact itself, as well as the public round trip.
    read_table = pd.read_parquet if table_format == "parquet" else pd.read_csv
    nodes = read_table(bundle / f"nodes.{table_format}")
    edges = read_table(bundle / f"edges.{table_format}")
    assert {"node_id", "node_order"} <= set(nodes.columns)
    assert {"edge_id", "src", "dst", "edge_order"} <= set(edges.columns)
    restored = import_sidecar(str(bundle))
    assert restored.nodes.node_id == node_ids
    assert restored.nodes.node_order == list(range(len(node_ids)))
    if node_ids:
        assert restored.nodes.attrs.to_dict("records") == [{"score": 7}]
    assert restored.edges.to_dict() == ir.edges.to_dict()
    assert restored.nodes.layer == ir.nodes.layer
    assert restored.meta.to_dict() == ir.meta.to_dict()
