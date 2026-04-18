"""
Out-of-core node degree filter with builder syntax.

FAST: <1s runtime
Dependencies: py3plex (core, out_of_core)

Demonstrates how to retrieve nodes filtered by degree using
query_nodes() — degree is computed out-of-core by scanning the edge
table without building a full adjacency structure in memory.  Key
patterns:
  - degree threshold    : degree__gt=2
  - layer filter        : layer="social"
  - ordering by degree  : order_by="-degree"
  - top-k nodes         : limit=5
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

# ---------------------------------------------------------------------------
# Build a small star-shaped CSV to make degree differences obvious
# ---------------------------------------------------------------------------

ROWS = [
    # social layer: hub A connects to B, C, D, E (degree 4)
    {"source": "A", "target": "B", "source_layer": "social", "target_layer": "social"},
    {"source": "A", "target": "C", "source_layer": "social", "target_layer": "social"},
    {"source": "A", "target": "D", "source_layer": "social", "target_layer": "social"},
    {"source": "A", "target": "E", "source_layer": "social", "target_layer": "social"},
    # work layer: chain A-B-C (degree 1 or 2)
    {"source": "A", "target": "B", "source_layer": "work", "target_layer": "work"},
    {"source": "B", "target": "C", "source_layer": "work", "target_layer": "work"},
]

with tempfile.TemporaryDirectory() as tmpdir:
    csv_path = os.path.join(tmpdir, "edges.csv")
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ROWS[0].keys())
        writer.writeheader()
        writer.writerows(ROWS)

    net = OutOfCoreNetwork.from_edges_csv(csv_path)

    # -----------------------------------------------------------------------
    # Pattern 1 – nodes with degree > 2 in the social layer
    # -----------------------------------------------------------------------
    result = net.query_nodes(layer="social", degree__gt=2)
    print("[Pattern 1] Social-layer nodes with degree > 2:")
    print(result.to_pandas().to_string(index=False))

    # -----------------------------------------------------------------------
    # Pattern 2 – top-5 highest-degree nodes across all layers
    # -----------------------------------------------------------------------
    result = net.query_nodes(order_by="-degree", limit=5)
    print("\n[Pattern 2] Top-5 highest-degree nodes (all layers):")
    print(result.to_pandas().to_string(index=False))

    # -----------------------------------------------------------------------
    # Pattern 3 – degree exactly 1 (leaf nodes)
    # -----------------------------------------------------------------------
    result = net.query_nodes(degree__eq=1)
    print("\n[Pattern 3] Leaf nodes (degree == 1):")
    print(result.to_pandas().to_string(index=False))

    # -----------------------------------------------------------------------
    # Pattern 4 – per-layer node counts
    # -----------------------------------------------------------------------
    result = net.query_nodes(per_layer=True)
    print("\n[Pattern 4] Per-layer node counts:")
    print(result.to_pandas().to_string(index=False))
