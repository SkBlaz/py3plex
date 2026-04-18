"""
Out-of-core: unsupported operations and in-memory fallback.

FAST: <1s runtime
Dependencies: py3plex (core, out_of_core)

Shows how unsupported operations (exact betweenness/closeness
centrality) are signalled with an actionable
``UnsupportedOutOfCoreOperation`` exception and how to fall back to
the in-memory DSL when the graph fits in RAM.

The recommended pattern is:
  1. Use query_edges() / query_nodes() for large graphs.
  2. If exact centrality is needed, convert to in-memory with
     OutOfCoreNetwork.to_in_memory() (or filter first to reduce size).
"""

import csv
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from py3plex.out_of_core import OutOfCoreNetwork
from py3plex.out_of_core.errors import UnsupportedOutOfCoreOperation

ROWS = [
    {"source": "A", "target": "B", "source_layer": "social", "target_layer": "social"},
    {"source": "B", "target": "C", "source_layer": "social", "target_layer": "social"},
    {"source": "C", "target": "A", "source_layer": "social", "target_layer": "social"},
]

with tempfile.TemporaryDirectory() as tmpdir:
    csv_path = os.path.join(tmpdir, "edges.csv")
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ROWS[0].keys())
        writer.writeheader()
        writer.writerows(ROWS)

    net = OutOfCoreNetwork.from_edges_csv(csv_path)

    # -----------------------------------------------------------------------
    # Supported: simple edge selection works fine
    # -----------------------------------------------------------------------
    result = net.query_edges(layer="social")
    print("Supported – edge selection:")
    print(result.to_pandas().to_string(index=False))

    # -----------------------------------------------------------------------
    # Unsupported: exact betweenness centrality raises a clear error
    # -----------------------------------------------------------------------
    # query_nodes() with an unsupported centrality condition triggers the guard.
    try:
        net.query_nodes(betweenness_centrality__gt=0)
    except UnsupportedOutOfCoreOperation as exc:
        print("\nCaught expected error for unsupported operation:")
        print(f"  {type(exc).__name__}: {str(exc).splitlines()[0]}")

    # -----------------------------------------------------------------------
    # Fallback: for exact centrality, convert the filtered result to a
    # standard in-memory multi_layer_network and use the regular DSL.
    # -----------------------------------------------------------------------
    print("\nFallback – in-memory DSL for exact centrality:")
    from py3plex.core import multinet
    from py3plex.dsl import Q

    # Build in-memory network from the filtered edge rows
    edges_df = net.query_edges(layer="social").to_pandas()
    mem_net = multinet.multi_layer_network(directed=False)
    mem_net.add_edges([
        {
            "source": row["source"],
            "target": row["target"],
            "source_type": row["source_layer"],
            "target_type": row["target_layer"],
        }
        for _, row in edges_df.iterrows()
    ])

    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .execute(mem_net)
    )
    print(result.to_pandas().to_string(index=False))
