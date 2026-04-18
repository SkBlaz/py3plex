"""
Out-of-core queries using the standard DSL v2 builder syntax (Q / L).

FAST: <1s runtime
Dependencies: py3plex (core, dsl, out_of_core)

Demonstrates that the same ``Q.edges()`` / ``Q.nodes()`` builder API used
for in-memory networks is automatically routed to the :class:`OutOfCoreBackend`
when the network object is an :class:`~py3plex.out_of_core.OutOfCoreNetwork`.

Patterns covered:
  - ``Q.edges().from_layers(L["social"]).execute(net)``
  - ``Q.edges().where(weight__gt=0.5).limit(10).execute(net)``
  - ``Q.edges().from_layers(...).where(...).order_by(...).execute(net)``
  - ``Q.nodes().from_layers(L["social"]).where(degree__gt=1).execute(net)``
  - ``UnsupportedOutOfCoreOperation`` for centrality measures
"""

import csv
import os
import tempfile
import sys
from pathlib import Path

# Add parent directory to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from py3plex.dsl import L, Q
from py3plex.out_of_core import OutOfCoreNetwork, UnsupportedOutOfCoreOperation

# ---------------------------------------------------------------------------
# Build a small CSV edge file to run the demo against
# ---------------------------------------------------------------------------

ROWS = [
    {"source": "Alice",   "target": "Bob",     "source_layer": "social",  "target_layer": "social",  "weight": "0.8"},
    {"source": "Bob",     "target": "Carol",   "source_layer": "social",  "target_layer": "social",  "weight": "0.3"},
    {"source": "Carol",   "target": "Dave",    "source_layer": "social",  "target_layer": "social",  "weight": "0.9"},
    {"source": "Alice",   "target": "Bob",     "source_layer": "work",    "target_layer": "work",    "weight": "1.2"},
    {"source": "Bob",     "target": "Dave",    "source_layer": "work",    "target_layer": "work",    "weight": "0.6"},
    {"source": "Alice",   "target": "Carol",   "source_layer": "family",  "target_layer": "family",  "weight": "0.1"},
    {"source": "Alice",   "target": "Bob",     "source_layer": "social",  "target_layer": "work",    "weight": "0.4"},
]

with tempfile.TemporaryDirectory() as _tmpdir:
    _csv_path = os.path.join(_tmpdir, "edges.csv")
    with open(_csv_path, "w", newline="") as _fh:
        _w = csv.DictWriter(_fh, fieldnames=ROWS[0].keys())
        _w.writeheader()
        _w.writerows(ROWS)

    # -----------------------------------------------------------------------
    # Create OutOfCoreNetwork — no data is loaded into RAM at this point
    # -----------------------------------------------------------------------
    net = OutOfCoreNetwork.from_edges_csv(_csv_path)
    print("Network:", net)
    print()

    # -----------------------------------------------------------------------
    # 1. Q.edges().from_layers(L["social"])
    #    → selects only edges where source_layer == "social"
    # -----------------------------------------------------------------------
    result = Q.edges().from_layers(L["social"]).execute(net)
    print("[1] Q.edges().from_layers(L['social']) —", result.count, "edges")
    print(result.to_pandas().to_string(index=False))
    print()

    # -----------------------------------------------------------------------
    # 2. Q.edges().where(weight__gt=0.5)
    #    → attribute predicate pushdown, no full load
    # -----------------------------------------------------------------------
    result = Q.edges().where(weight__gt=0.5).execute(net)
    print("[2] Q.edges().where(weight__gt=0.5) —", result.count, "edges")
    print(result.to_pandas().to_string(index=False))
    print()

    # -----------------------------------------------------------------------
    # 3. Q.edges().from_layers(L["social"] + L["work"]).where(weight__gt=0.5)
    #              .order_by("weight").limit(3)
    # -----------------------------------------------------------------------
    result = (
        Q.edges()
        .from_layers(L["social"] + L["work"])
        .where(weight__gt=0.5)
        .order_by("weight")
        .limit(3)
        .execute(net)
    )
    print("[3] Top-3 lightest social/work edges (weight > 0.5):")
    print(result.to_pandas().to_string(index=False))
    print()

    # -----------------------------------------------------------------------
    # 4. Q.nodes().from_layers(L["social"]).where(degree__gt=1)
    #    → degree computed out-of-core by scanning the edge file once
    # -----------------------------------------------------------------------
    result = Q.nodes().from_layers(L["social"]).where(degree__gt=1).execute(net)
    print("[4] Q.nodes().where(degree__gt=1) in 'social' layer —", result.count, "nodes")
    print(result.to_pandas().to_string(index=False))
    print()

    # -----------------------------------------------------------------------
    # 5. Unsupported measure → UnsupportedOutOfCoreOperation
    #    The error message includes a suggestion for the fallback.
    # -----------------------------------------------------------------------
    try:
        Q.nodes().where(betweenness_centrality__gt=0).execute(net)
    except UnsupportedOutOfCoreOperation as exc:
        print("[5] Correctly raised UnsupportedOutOfCoreOperation:")
        print("   ", str(exc).splitlines()[0])
        print()

    # -----------------------------------------------------------------------
    # 6. Accessing .to_pandas() — same API as in-memory QueryResult
    # -----------------------------------------------------------------------
    df = Q.edges().from_layers(L["work"]).execute(net).to_pandas()
    print("[6] Work-layer edges as a pandas DataFrame:")
    print(df.to_string(index=False))
