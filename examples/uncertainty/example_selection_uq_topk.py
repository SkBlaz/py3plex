"""Example: SelectionUQ for top-k node ranking with uncertainty.

This example demonstrates how to use SelectionUQ to quantify uncertainty
in top-k node rankings under network perturbations.
"""

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.uncertainty import EdgeDrop

# Create a sample network
net = multinet.multi_layer_network(directed=False, verbose=False)

# Add edges to create a network with hub structure
edges = [
    # Layer 0: Hub 'a' is central
    ["a", "L0", "b", "L0", 1.0],
    ["a", "L0", "c", "L0", 1.0],
    ["a", "L0", "d", "L0", 1.0],
    ["a", "L0", "e", "L0", 1.0],
    ["a", "L0", "f", "L0", 1.0],
    ["b", "L0", "c", "L0", 1.0],
    ["c", "L0", "d", "L0", 1.0],
    # Layer 1: Different structure
    ["a", "L1", "b", "L1", 1.0],
    ["b", "L1", "c", "L1", 1.0],
    ["c", "L1", "d", "L1", 1.0],
    ["d", "L1", "e", "L1", 1.0],
    ["e", "L1", "f", "L1", 1.0],
    ["f", "L1", "g", "L1", 1.0],
    # Inter-layer connections
    ["a", "L0", "a", "L1", 1.0],
    ["b", "L0", "b", "L1", 1.0],
    ["c", "L0", "c", "L1", 1.0],
]
net.add_edges(edges, input_type="list")

print("=" * 60)
print("SelectionUQ Example: Top-5 Nodes by Degree")
print("=" * 60)

# Query: Find top-5 nodes by degree with uncertainty quantification
result = (
    Q.nodes()
    .compute("degree")
    .order_by("degree", desc=True)
    .limit(5)
    .uq(
        method="perturbation",           # Use perturbation-based UQ
        noise_model=EdgeDrop(p=0.1),     # Drop 10% of edges in each sample
        n_samples=100,                    # Run 100 samples
        seed=42                           # Reproducible results
    )
    .execute(net)
)

# Display results
print("\n Top-5 Nodes (with uncertainty):")
print("-" * 60)

df = result.to_pandas()
# Sort by degree for display
df_sorted = df.sort_values("degree", ascending=False).head(10)

print(f"{'Node':<8} {'Degree':<8} {'P(present)':<12} {'Rank Mean':<12} {'P(top-5)':<10}")
print("-" * 60)

for _, row in df_sorted.iterrows():
    node_id = row.get("id", "?")
    degree = row.get("degree", 0)
    present_prob = row.get("present_prob", 0)
    rank_mean = row.get("rank_mean", float('inf'))
    p_in_topk = row.get("p_in_topk", 0)

    print(f"{node_id:<8} {degree:<8.0f} {present_prob:<12.3f} {rank_mean:<12.1f} {p_in_topk:<10.3f}")

# Display UQ metadata
print("\n Uncertainty Statistics:")
print("-" * 60)

uq_meta = result.meta["uq"]
print(f"Number of samples: {uq_meta['n_samples']}")
print(f"UQ method: {uq_meta['method']}")
print(f"Noise model: {uq_meta['noise_model']}")

print(f"\n Selection Set Size:")
size_stats = uq_meta["set_size"]
print(f" Mean: {size_stats['mean']:.2f}")
print(f" Std: {size_stats['std']:.2f}")

print(f"\n Stability (Jaccard similarity):")
stability = uq_meta["stability"]
print(f" Mean: {stability['jaccard_mean']:.3f}")
print(f" Std: {stability['jaccard_std']:.3f}")

print(f"\n Consensus Selection (P ≥ 0.5):")
consensus = uq_meta["consensus"]
print(f" Size: {consensus['size']}")
print(f" Items: {', '.join(str(x) for x in consensus['items_preview'][:10])}")

print(f"\n️ Borderline Items (uncertain inclusion):")
borderline = uq_meta["borderline_items"]
if borderline:
    print(f"  {', '.join(str(x) for x in borderline[:5])}")
else:
    print("  (none)")

if uq_meta.get("topk"):
    print(f"\n Top-5 Overlap Statistics:")
    topk_stats = uq_meta["topk"]["overlap"]
    print(f"  Mean overlap: {topk_stats.get('overlap_mean', 'N/A'):.2f}")
    print(f"  Std overlap:  {topk_stats.get('overlap_std', 'N/A'):.2f}")

print("\n" + "=" * 60)
print("Interpretation:")
print("=" * 60)
print("• present_prob: Probability that a node appears in the top-5")
print("• rank_mean: Average rank across all samples")
print("• p_in_topk: Probability of being in top-5 (P(rank ≤ 5))")
print("• Jaccard stability: How similar selections are across samples")
print("• Consensus items: Nodes that appear in ≥50% of samples")
print("• Borderline items: Nodes with ~50% inclusion probability")
print("=" * 60)

print("\n SelectionUQ provides probabilistic top-k rankings!")
print(" This helps identify which rankings are stable vs. uncertain.")
