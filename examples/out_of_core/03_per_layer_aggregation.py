"""
Out-of-core per-layer aggregations with builder syntax.

FAST: <1s runtime
Dependencies: py3plex (core, out_of_core)

Demonstrates per-layer and per-layer-pair aggregations using
query_edges() and query_nodes() with the ``per_layer_pair=True`` and
``per_layer=True`` flags.  Aggregations run out-of-core via streaming
external groupby — no full materialization needed.  Key patterns:
  - edge counts per (source_layer, target_layer) pair
  - node counts per layer
  - chaining with limit / order_by
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

ROWS = [
    # social–social
    {"source": "A", "target": "B", "source_layer": "social", "target_layer": "social"},
    {"source": "B", "target": "C", "source_layer": "social", "target_layer": "social"},
    {"source": "C", "target": "D", "source_layer": "social", "target_layer": "social"},
    # work–work
    {"source": "A", "target": "B", "source_layer": "work",   "target_layer": "work"},
    {"source": "B", "target": "C", "source_layer": "work",   "target_layer": "work"},
    # social–work cross-layer
    {"source": "A", "target": "A", "source_layer": "social", "target_layer": "work"},
    {"source": "B", "target": "B", "source_layer": "social", "target_layer": "work"},
]

with tempfile.TemporaryDirectory() as tmpdir:
    csv_path = os.path.join(tmpdir, "edges.csv")
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ROWS[0].keys())
        writer.writeheader()
        writer.writerows(ROWS)

    net = OutOfCoreNetwork.from_edges_csv(csv_path)

    # -----------------------------------------------------------------------
    # Pattern 1 – edge counts per layer pair
    # -----------------------------------------------------------------------
    result = net.query_edges(per_layer_pair=True)
    print("[Pattern 1] Edge counts per layer pair:")
    print(result.to_pandas().to_string(index=False))

    # -----------------------------------------------------------------------
    # Pattern 2 – node counts per layer
    # -----------------------------------------------------------------------
    result = net.query_nodes(per_layer=True)
    print("\n[Pattern 2] Node counts per layer:")
    print(result.to_pandas().to_string(index=False))

    # -----------------------------------------------------------------------
    # Pattern 3 – edge counts for a single layer pair (filter first, group)
    # -----------------------------------------------------------------------
    result = net.query_edges(layer="social", per_layer_pair=True)
    print("\n[Pattern 3] Edge counts in layer pairs touching 'social':")
    print(result.to_pandas().to_string(index=False))
