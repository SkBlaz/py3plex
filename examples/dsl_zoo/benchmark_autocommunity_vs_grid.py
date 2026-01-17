"""Benchmark AutoCommunity vs grid baselines with fair budget.

This example demonstrates:
1. Fair time budgets per repeat
2. Grid search for baselines (Louvain, Leiden)
3. AutoCommunity meta-algorithm
4. Budgeted evaluation with early stopping
5. Tidy results with leaderboard view
"""

from py3plex.core import multinet
from py3plex.dsl import B, L

# Create simple test network
net = multinet.multi_layer_network(directed=False)

# Add nodes
nodes = [{"source": f"N{i}", "type": "social"} for i in range(30)]
net.add_nodes(nodes)

# Add edges to create community structure
# Block 1: nodes 0-14
for i in range(15):
    for j in range(i + 1, 15):
        if (i + j) % 3 == 0:  # Sparse connections
            net.add_edges([{
                "source": f"N{i}",
                "target": f"N{j}",
                "source_type": "social",
                "target_type": "social",
            }])

# Block 2: nodes 15-29
for i in range(15, 30):
    for j in range(i + 1, 30):
        if (i + j) % 3 == 0:
            net.add_edges([{
                "source": f"N{i}",
                "target": f"N{j}",
                "source_type": "social",
                "target_type": "social",
            }])

# Between blocks (sparse)
for i in range(0, 15, 5):
    for j in range(15, 30, 5):
        net.add_edges([{
            "source": f"N{i}",
            "target": f"N{j}",
            "source_type": "social",
            "target_type": "social",
        }])

# Run benchmark with fair budget
print("Running benchmark with fair time budget...")

res = (
    B.community()
    .on(net)
    .layers(L["social"])
    .budget(runtime_ms=20_000, per="repeat")
    .repeat(3, seed=42)
    .uq(method="seed", n_samples=10, seed=42)
    .algorithms(
        ("autocommunity", {"mode": "pareto", "candidate_set": "core", "fast": False}),
        ("louvain", {"grid": {"resolution": [0.8, 1.0, 1.2]}}),
        ("leiden", {"grid": {"gamma": [0.8, 1.0, 1.2], "n_iter": [2, 5]}}),
    )
    .metrics("modularity", "runtime_ms", "stability")
    .select("wins")
    .execute()
)

print("\n=== Benchmark Results ===\n")

# Get results DataFrame
df = res.to_pandas()
print(f"Total runs: {len(df)}")
print(f"\nColumns: {list(df.columns)}")

# Show leaderboard
if hasattr(res, "benchmark"):
    print("\n=== Leaderboard ===")
    leaderboard = res.benchmark.leaderboard()
    if not leaderboard.empty:
        print(leaderboard)
    else:
        print("(Leaderboard not available)")

    # Show best by algorithm
    print("\n=== Best Config Per Algorithm ===")
    best = res.benchmark.best_by_algo()
    if not best.empty:
        print(best)
    else:
        print("(Best by algorithm not available)")

    # Show AutoCommunity trace if available
    print("\n=== AutoCommunity Trace (first 10 candidates) ===")
    trace = res.benchmark.trace("autocommunity")
    if trace is not None and not trace.empty:
        print(trace.head(10))
    else:
        print("(Trace not available)")
else:
    print("\n=== Run-level Results (sample) ===")
    print(df.head(10))

print("\nBenchmark complete.")
print(f"Total runtime: {res.meta.get('benchmark', {}).get('total_runtime_ms', 0):.1f} ms")
