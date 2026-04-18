"""
Out-of-core edge selection with builder syntax.

FAST: <1s runtime
Dependencies: py3plex (core, out_of_core)

Demonstrates how to query edges from a large on-disk CSV using the
builder-style query_edges() API without loading the full graph into
memory.  Key patterns:
  - layer filter        : layer="social"
  - attribute predicate : weight__gt=0.5
  - multiple layers     : layers=["social", "work"]
  - ordering + limit    : order_by="-weight", limit=10
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
# Build a small CSV file to demonstrate the API
# ---------------------------------------------------------------------------

ROWS = [
    {"source": "A", "target": "B", "source_layer": "social", "target_layer": "social", "weight": "0.8"},
    {"source": "B", "target": "C", "source_layer": "social", "target_layer": "social", "weight": "0.3"},
    {"source": "C", "target": "D", "source_layer": "social", "target_layer": "social", "weight": "0.9"},
    {"source": "A", "target": "B", "source_layer": "work",   "target_layer": "work",   "weight": "1.2"},
    {"source": "B", "target": "D", "source_layer": "work",   "target_layer": "work",   "weight": "0.6"},
    {"source": "A", "target": "C", "source_layer": "family", "target_layer": "family", "weight": "0.1"},
]

with tempfile.TemporaryDirectory() as tmpdir:
    csv_path = os.path.join(tmpdir, "edges.csv")
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ROWS[0].keys())
        writer.writeheader()
        writer.writerows(ROWS)

    # -----------------------------------------------------------------------
    # Create an OutOfCoreNetwork pointing at the CSV (no data loaded yet)
    # -----------------------------------------------------------------------
    net = OutOfCoreNetwork.from_edges_csv(csv_path)
    print("Network descriptor:", net)

    # -----------------------------------------------------------------------
    # Pattern 1 – all edges in a single layer
    # -----------------------------------------------------------------------
    result = net.query_edges(layer="social")
    print("\n[Pattern 1] All edges in 'social' layer:")
    print(result.to_pandas().to_string(index=False))

    # -----------------------------------------------------------------------
    # Pattern 2 – attribute predicate pushdown
    # -----------------------------------------------------------------------
    result = net.query_edges(layer="social", weight__gt=0.5)
    print("\n[Pattern 2] Social edges with weight > 0.5:")
    print(result.to_pandas().to_string(index=False))

    # -----------------------------------------------------------------------
    # Pattern 3 – multiple layers, ordered by weight descending, top-3
    # -----------------------------------------------------------------------
    result = net.query_edges(layers=["social", "work"], order_by="-weight", limit=3)
    print("\n[Pattern 3] Top-3 heaviest social/work edges:")
    print(result.to_pandas().to_string(index=False))

    # -----------------------------------------------------------------------
    # Pattern 4 – all edges ordered ascending
    # -----------------------------------------------------------------------
    result = net.query_edges(order_by="weight", order_asc=True, limit=4)
    print("\n[Pattern 4] 4 lightest edges (ascending weight):")
    print(result.to_pandas().to_string(index=False))
