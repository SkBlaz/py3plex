"""
Out-of-core cross-layer coverage filter with builder syntax.

FAST: <1s runtime
Dependencies: py3plex (core, out_of_core)

Demonstrates ``coverage_k`` — filtering edges whose undirected node
pair (u, v) appears in at least *k* distinct layer pairs.  This runs
entirely out-of-core via an external groupby on the canonical edge key
without loading the full edge list into memory.  Key patterns:
  - coverage_k=2  : keep pairs present in >= 2 layer pairs
  - combining coverage with layer / attribute filters
"""

import csv
import tempfile
import os

from py3plex.out_of_core import OutOfCoreNetwork

# Edge pairs A-B and B-C appear in both social and work layers.
# Pair C-D appears only in social.
ROWS = [
    {"source": "A", "target": "B", "source_layer": "social", "target_layer": "social", "weight": "0.9"},
    {"source": "B", "target": "C", "source_layer": "social", "target_layer": "social", "weight": "0.7"},
    {"source": "C", "target": "D", "source_layer": "social", "target_layer": "social", "weight": "0.4"},
    {"source": "A", "target": "B", "source_layer": "work",   "target_layer": "work",   "weight": "1.1"},
    {"source": "B", "target": "C", "source_layer": "work",   "target_layer": "work",   "weight": "0.8"},
]

with tempfile.TemporaryDirectory() as tmpdir:
    csv_path = os.path.join(tmpdir, "edges.csv")
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ROWS[0].keys())
        writer.writeheader()
        writer.writerows(ROWS)

    net = OutOfCoreNetwork.from_edges_csv(csv_path)

    # -----------------------------------------------------------------------
    # Pattern 1 – keep edges whose (u, v) pair spans >= 2 layer pairs
    # -----------------------------------------------------------------------
    result = net.query_edges(coverage_k=2)
    print("[Pattern 1] Edges with (u,v) pair in >= 2 layer pairs:")
    print(result.to_pandas().to_string(index=False))
    print(f"  → {result.count} edge rows returned")

    # -----------------------------------------------------------------------
    # Pattern 2 – cross-layer edges with a weight filter too
    # -----------------------------------------------------------------------
    result = net.query_edges(coverage_k=2, weight__gt=0.8)
    print("\n[Pattern 2] Cross-layer edges with weight > 0.8:")
    print(result.to_pandas().to_string(index=False))

    # -----------------------------------------------------------------------
    # Pattern 3 – coverage=1 returns all edges (no filtering)
    # -----------------------------------------------------------------------
    result = net.query_edges(coverage_k=1)
    print(f"\n[Pattern 3] coverage_k=1 → all {result.count} edges returned")
