"""Demonstrate Pareto selection mode for multi-objective optimization.

This example shows:
1. Pareto front computation across multiple metrics
2. Non-dominated solutions
3. Trade-offs between modularity and runtime
4. Weighted selection as alternative
"""

from py3plex.core import multinet
from py3plex.dsl import B, L
import numpy as np

# Create test network with known structure
np.random.seed(42)
net = multinet.multi_layer_network(directed=False)

# Two communities
nodes = [{"source": f"N{i}", "type": "layer1"} for i in range(40)]
net.add_nodes(nodes)

# Dense within communities
for i in range(20):
    for j in range(i + 1, 20):
        if np.random.rand() < 0.4:  # 40% density in block 1
            net.add_edges([{
                "source": f"N{i}",
                "target": f"N{j}",
                "source_type": "layer1",
                "target_type": "layer1",
            }])

for i in range(20, 40):
    for j in range(i + 1, 40):
        if np.random.rand() < 0.4:  # 40% density in block 2
            net.add_edges([{
                "source": f"N{i}",
                "target": f"N{j}",
                "source_type": "layer1",
                "target_type": "layer1",
            }])

# Sparse between communities
for i in range(20):
    for j in range(20, 40):
        if np.random.rand() < 0.05:  # 5% density between blocks
            net.add_edges([{
                "source": f"N{i}",
                "target": f"N{j}",
                "source_type": "layer1",
                "target_type": "layer1",
            }])

print("Running benchmark with Pareto selection...")

res_pareto = (
    B.community()
    .on(net)
    .layers(L["layer1"])
    .algorithms(
        ("louvain", {"grid": {"resolution": [0.5, 0.8, 1.0, 1.2, 1.5]}}),
        ("leiden", {"grid": {"gamma": [0.5, 0.8, 1.0, 1.2, 1.5], "n_iter": [2, 5]}}),
    )
    .metrics("modularity", "coverage", "runtime_ms")
    .repeat(1, seed=42)
    .select("pareto")
    .execute()
)

print("\n=== Pareto Selection Results ===\n")

df_pareto = res_pareto.to_pandas()

# Show all evaluated configs
print(f"Total configs evaluated: {len(df_pareto)}")

# Show Pareto front
if hasattr(res_pareto, "benchmark"):
    print("\n=== Pareto Front (non-dominated solutions) ===")
    pareto = res_pareto.benchmark.pareto_front()
    if pareto is not None and not pareto.empty:
        print(pareto[["algorithm", "params_json", "modularity", "coverage", "runtime_ms"]])
        print(f"\nPareto front size: {len(pareto)} solutions")
    else:
        print("(Pareto front not available)")

print("\n" + "="*60)
print("Now running with weighted selection...")
print("="*60 + "\n")

# Alternative: weighted selection
res_weighted = (
    B.community()
    .on(net)
    .layers(L["layer1"])
    .algorithms(
        ("louvain", {"grid": {"resolution": [0.5, 0.8, 1.0, 1.2, 1.5]}}),
        ("leiden", {"grid": {"gamma": [0.5, 0.8, 1.0, 1.2, 1.5], "n_iter": [2, 5]}}),
    )
    .metrics("modularity", "coverage", "runtime_ms")
    .repeat(1, seed=42)
    .select(("weighted", {
        "modularity": 0.6,
        "coverage": 0.3,
        "runtime_ms": -0.1,  # Negative weight = prefer lower
    }))
    .execute()
)

print("\n=== Weighted Selection Results ===\n")

if hasattr(res_weighted, "benchmark"):
    print("Best overall (weighted score):")
    best = res_weighted.benchmark.best_by_algo()
    if best is not None and not best.empty:
        print(best[["algorithm", "params_json", "modularity", "coverage", "runtime_ms"]])
    else:
        print("(Best by algorithm not available)")

print("\n✅ Pareto selection demo complete!")
print("\nKey insight: Pareto front reveals trade-offs, weighted selection picks one solution.")
