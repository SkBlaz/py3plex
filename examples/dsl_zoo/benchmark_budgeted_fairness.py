"""Demonstrate budgeted fairness across algorithms.

This example shows:
1. Equal time budget per repeat across all algorithms
2. Partial grid evaluation when budget is exhausted
3. Budget accounting in results (limit, used, timed_out)
4. Deterministic config ordering
"""

from py3plex.core import multinet
from py3plex.dsl import B, L

# Create test network
net = multinet.multi_layer_network(directed=False)

# Simple ring network
nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(20)]
net.add_nodes(nodes)

for i in range(20):
    net.add_edges([{
        "source": f"N{i}",
        "target": f"N{(i+1)%20}",
        "source_type": "layer1",
        "target_type": "layer1",
    }])

# Add some cross-connections
for i in range(0, 20, 5):
    net.add_edges([{
        "source": f"N{i}",
        "target": f"N{(i+10)%20}",
        "source_type": "layer1",
        "target_type": "layer1",
    }])

print("Running budget-constrained benchmark...")

# Small budget to force partial evaluation
res = (
    B.community()
    .on(net)
    .layers(L["layer1"])
    .budget(runtime_ms=5_000, per="repeat")  # Small budget
    .repeat(2, seed=42)
    .algorithms(
        ("louvain", {
            "grid": {
                "resolution": [0.5, 0.8, 1.0, 1.2, 1.5, 2.0],  # 6 configs
            }
        }),
        ("leiden", {
            "grid": {
                "gamma": [0.8, 1.0, 1.2],
                "n_iter": [2, 5, 10],  # 3x3 = 9 configs
            }
        }),
    )
    .metrics("modularity", "n_communities", "runtime_ms")
    .select("pareto")
    .execute()
)

print("\n=== Budget Accounting ===\n")

df = res.to_pandas()

# Show budget usage per algorithm
for algo in df["algorithm"].unique():
    algo_df = df[df["algorithm"] == algo]
    print(f"\n{algo}:")
    print(f"  Configs evaluated: {len(algo_df[algo_df['timed_out'] == False])}")
    print(f"  Configs skipped: {len(algo_df[algo_df['timed_out'] == True])}")
    print(f"  Budget used: {algo_df['budget_used_ms'].iloc[0]:.1f} ms")
    print(f"  Budget limit: {algo_df['budget_limit_ms'].iloc[0]:.1f} ms")

# Show which configs were evaluated
print("\n=== Evaluated Configurations ===\n")
evaluated = df[df["timed_out"] == False]
print(evaluated[["algorithm", "config_id", "params_json", "runtime_ms"]].to_string(index=False))

# Show Pareto front
if hasattr(res, "benchmark"):
    print("\n=== Pareto Front ===")
    pareto = res.benchmark.pareto_front()
    if pareto is not None and not pareto.empty:
        print(pareto)
    else:
        print("(Pareto front not available)")

print("\nBudget fairness demo complete.")
