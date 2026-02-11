"""Example 50: Meta-analysis across multiple networks

Demonstrates M.meta() for meta-analytic pooling of network statistics
across multiple networks with DerSimonian-Laird random-effects model.

Runtime: FAST (~0.2s)
"""

from py3plex.core import multinet
from py3plex.dsl import Q, M

# Create multiple networks (simulating different studies/datasets)
def create_network(n_nodes, seed):
    """Create a sample network with specified size."""
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([
        {'source': f'N{i}', 'type': 'layer1'} for i in range(n_nodes)
    ])
    # Add edges with seed-based variation
    import random
    random.seed(seed)
    net.add_edges([
        {'source': f'N{i}', 'target': f'N{j}',
         'source_type': 'layer1', 'target_type': 'layer1'}
        for i in range(n_nodes)
        for j in range(i+1, n_nodes)
        if random.random() < 0.3  # 30% edge probability
    ])
    return net

# Create 3 networks with different sizes
networks = {
    'study1': create_network(10, seed=1),
    'study2': create_network(12, seed=2),
    'study3': create_network(15, seed=3),
}

print("=" * 60)
print("Example 1: Network-level meta-analysis")
print("=" * 60)

# Meta-analyze average degree across networks
result = (
    M.meta("avg_degree_meta")
     .on_networks(networks)
     .run(
         Q.nodes().compute("degree").summarize(avg_degree="mean(degree)"),
         effect="avg_degree"
     )
     .model("random")
     .seed(42)
     .execute()
)

print("Meta-analysis results:")
df = result.to_pandas()
print(df)

print(f"\nPooled effect: {df['pooled_effect'].iloc[0]:.3f}")
print(f"Pooled SE: {df['pooled_se'].iloc[0]:.3f}")
print(f"I²: {df['I2'].iloc[0]:.1f}%")

print("\n" + "=" * 60)
print("Example 2: Per-network statistics")
print("=" * 60)

network_df = result.network_table()
print("\nPer-network effects:")
print(network_df)

print("\n" + "=" * 60)
print("Example 3: Fixed-effect model")
print("=" * 60)

result_fixed = (
    M.meta("avg_degree_fixed")
     .on_networks(networks)
     .run(
         Q.nodes().compute("degree").summarize(avg_degree="mean(degree)"),
         effect="avg_degree"
     )
     .model("fixed")
     .seed(42)
     .execute()
)

df_fixed = result_fixed.to_pandas()
print("Fixed-effect meta-analysis:")
print(df_fixed)

print("\n" + "=" * 60)
print("Example 4: Heterogeneity assessment")
print("=" * 60)

print(f"\nRandom-effects I²: {df['I2'].iloc[0]:.1f}%")
print(f"Fixed-effect I²: {df_fixed['I2'].iloc[0]:.1f}%")

if df['I2'].iloc[0] > 50:
    print("\n[NOTE] High heterogeneity detected (I² > 50%)")
    print("[NOTE] Random-effects model recommended")
else:
    print("\n[NOTE] Low heterogeneity (I² < 50%)")
    print("[NOTE] Both models appropriate")

print("\n[TIP] Use M.meta() for meta-analytic pooling across networks")
print("[TIP] model='random' accounts for between-study heterogeneity")
print("[TIP] model='fixed' assumes all networks share true effect")
print("[TIP] Check I² to assess heterogeneity (>50% = high)")
